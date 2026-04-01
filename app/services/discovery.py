"""Discovery service — crawls the Rubricator to discover clinical recommendation documents.

Uses Playwright to handle JS-driven pages and intercept XHR/Fetch payloads.
Supports full sync and incremental sync modes.
"""

import json
import logging
import re
import time
from datetime import datetime, timezone

import httpx
from playwright.sync_api import sync_playwright

from app.core.config import settings
from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry
from app.models.pipeline import PipelineRun

logger = logging.getLogger(__name__)

API_ENDPOINT_PATTERN = "/api/"


class DiscoveryService:
    @staticmethod
    def _build_url(path: str) -> str:
        clean_base = settings.rubricator_base_url.rstrip("/")
        clean_path = path.strip("/")
        return f"{clean_base}/{clean_path}"

    def _list_urls(self) -> list[str]:
        urls: list[str] = []
        for path in (
            settings.rubricator_list_path,
            settings.rubricator_list_fallback_path,
        ):
            if not path:
                continue
            url = self._build_url(path)
            if url not in urls:
                urls.append(url)
        return urls

    def execute(self, run_id: int, mode: str = "full") -> None:
        session = get_sync_session()
        try:
            run = session.get(PipelineRun, run_id)
            if not run:
                logger.error("Pipeline run %d not found", run_id)
                return
            run.status = "running"
            run.started_at = datetime.now(timezone.utc)
            session.commit()

            try:
                records, discovery_stats = self._discover_documents()
                discovered, new_count = self._upsert_records(session, records, mode)
                run.discovered_count = discovered
                run.fetched_count = new_count
                run.status = "completed"
                run.finished_at = datetime.now(timezone.utc)
                run.stats_json = {
                    "total_discovered": discovered,
                    "new_or_updated": new_count,
                    "failed_count": max(0, discovered - new_count),
                    **discovery_stats,
                }
                session.commit()

                # Queue probe tasks for new/updated documents
                from app.workers.tasks.probe import probe_document

                for reg_id in self._get_probe_candidates(session, mode):
                    probe_document.delay(reg_id)

            except Exception as e:
                logger.exception("Discovery failed: %s", e)
                run.status = "failed"
                run.error_message = str(e)[:2000]
                run.finished_at = datetime.now(timezone.utc)
                session.commit()
        finally:
            session.close()

    def _discover_documents(self) -> tuple[list[dict], dict]:
        """Use Playwright to open the rubricator and capture document data from network requests."""
        records: list[dict] = []
        stats: dict = {
            "strategy": "unknown",
            "api_payloads": 0,
            "api_records": 0,
            "dom_records": 0,
            "runtime_records": 0,
        }

        # API-first strategy for stability when frontend DOM changes.
        api_records = self._discover_from_backend_api()
        if api_records:
            records.extend(api_records)
            stats["strategy"] = "backend_api"
            stats["api_records"] = len(api_records)
            records = self._deduplicate_records(records)
            logger.info("Discovered %d document records", len(records))
            return records, stats

        captured_payloads: list[dict] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()

            # Intercept XHR/Fetch responses to capture API payloads
            def handle_response(response):
                if API_ENDPOINT_PATTERN in response.url and response.status == 200:
                    try:
                        body = response.json()
                        captured_payloads.append({"url": response.url, "data": body})
                    except Exception:
                        try:
                            text_body = response.text()
                            parsed = json.loads(text_body)
                            captured_payloads.append({"url": response.url, "data": parsed})
                        except Exception:
                            pass

            page.on("response", handle_response)

            try:
                navigated = False
                for list_url in self._list_urls():
                    try:
                        page.goto(list_url, wait_until="networkidle", timeout=60000)
                        time.sleep(settings.discovery_request_delay)
                        navigated = True
                        break
                    except Exception as nav_err:
                        logger.warning("Failed to open %s: %s", list_url, nav_err)

                if not navigated:
                    raise RuntimeError("Unable to open rubricator list page")

                self._trigger_spa_activity(page)

                # Try to paginate through all results
                self._paginate_and_collect(page)

            except Exception as e:
                logger.warning("Playwright navigation error: %s", e)
            finally:
                browser.close()

        # Extract records from captured payloads
        for payload in captured_payloads:
            extracted = self._extract_records_from_payload(payload)
            records.extend(extracted)
        stats["api_payloads"] = len(captured_payloads)
        stats["api_records"] = len(records)

        # Try to extract from JS runtime as additional fallback for SPA state stores.
        if not records:
            runtime_records = self._discover_from_runtime_state()
            records.extend(runtime_records)
            stats["runtime_records"] = len(runtime_records)

        # Fallback: if no API payloads captured, try DOM parsing
        if not records:
            dom_records = self._discover_from_dom()
            records = dom_records
            stats["dom_records"] = len(dom_records)

        records = self._deduplicate_records(records)
        if records and stats["strategy"] == "unknown":
            stats["strategy"] = "playwright_fallback"
        logger.info("Discovered %d document records", len(records))
        return records, stats

    def _discover_from_backend_api(self) -> list[dict]:
        """Query rubricator backend API directly when available."""
        all_records: list[dict] = []
        page = 1
        max_pages = 200
        page_size = max(1, settings.rubricator_api_page_size)
        page_delay = max(0.0, settings.rubricator_api_request_delay)
        total_records = None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": settings.rubricator_api_user_agent,
        }

        with httpx.Client(timeout=30, follow_redirects=True, trust_env=False) as client:
            while page <= max_pages:
                params = {
                    "op": settings.rubricator_api_list_op,
                }
                payload = {
                    "filters": [
                        {
                            "fieldName": "status",
                            "filterType": 1,
                            "filterValueType": 2,
                            "value1": 0,
                            "value2": "",
                            "values": [],
                        }
                    ],
                    "sortOption": {"fieldName": "publishdate", "sortType": 2},
                    "pageSize": page_size,
                    "currentPage": page,
                    "useANDoperator": True,
                    "columns": [],
                }
                try:
                    response = client.post(
                        settings.rubricator_api_base_url,
                        params=params,
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                except Exception:
                    break

                try:
                    payload = response.json()
                except Exception:
                    break

                if isinstance(payload, dict):
                    total_records = payload.get("TotalRecords", total_records)

                page_records = self._extract_records_from_payload({"url": str(response.url), "data": payload})
                if not page_records:
                    break

                all_records.extend(page_records)

                # Stop when last page appears incomplete.
                if len(page_records) < page_size:
                    break

                # Stop when we reached total records according to API response.
                if isinstance(total_records, int) and len(all_records) >= total_records:
                    break
                page += 1
                if page_delay > 0:
                    time.sleep(page_delay)

        return self._deduplicate_records(all_records)

    def _trigger_spa_activity(self, page) -> None:
        """Trigger typical SPA interactions to force list/XHR loading."""
        actions = [
            'button:has-text("Показать"), button:has-text("Применить"), button:has-text("Найти")',
            '[role="button"]:has-text("Показать"), [role="button"]:has-text("Применить")',
            'input[type="search"], input[placeholder*="Поиск"], input[placeholder*="поиск"]',
        ]

        for selector in actions:
            try:
                el = page.query_selector(selector)
                if not el or not el.is_visible():
                    continue
                el.click()
                page.wait_for_load_state("networkidle", timeout=10000)
                time.sleep(settings.discovery_request_delay)
            except Exception:
                continue

        try:
            page.mouse.wheel(0, 3000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(settings.discovery_request_delay)
        except Exception:
            pass

    def _paginate_and_collect(self, page) -> None:
        """Try to click pagination buttons to load more documents."""
        max_pages = 30
        for _ in range(max_pages):
            try:
                next_btn = page.query_selector('button:has-text("Далее"), a:has-text("Далее"), .pagination .next')
                if not next_btn or not next_btn.is_visible():
                    break
                next_btn.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(settings.discovery_request_delay)
            except Exception:
                break

    def _extract_records_from_payload(self, payload: dict) -> list[dict]:
        """Parse a network response payload into document records."""
        records = []
        data = payload.get("data")
        if not data:
            return records

        items = self._collect_candidate_items(data)

        for item in items:
            if not isinstance(item, dict):
                continue
            record = self._normalize_item(item, payload.get("url", ""))
            if record.get("title"):
                records.append(record)

        return records

    def _normalize_item(self, item: dict, source_url: str) -> dict:
        """Normalize a raw item from any API format to our registry schema."""
        record = {
            "external_id": str(
                item.get(
                    "CodeVersion",
                    item.get(
                        "codeVersion",
                        item.get(
                            "code",
                            item.get(
                                "Id",
                    "id",
                    item.get("ID", item.get("_id", item.get("external_id", item.get("code", "")))),
                            ),
                        ),
                    ),
                )
            ),
            "title": item.get(
                "Name",
                "title",
                item.get("name", item.get("Title", item.get("naim", item.get("nameClinRec", "")))),
            ),
            "card_url": item.get("url", item.get("link", "")),
            "html_url": item.get("html_url", item.get("htmlUrl", "")),
            "pdf_url": item.get("pdf_url", item.get("pdfUrl", item.get("pdf", ""))),
            "specialty": item.get("specialty", item.get("mkbGroup", item.get("rubric", ""))),
            "age_group": item.get("age_group", item.get("ageGroup", "")),
            "status": item.get("status", item.get("state", "")),
            "version_label": item.get("version", item.get("versionLabel", "")),
            "publish_date": item.get("publish_date", item.get("publishDate", item.get("datePublish", ""))),
            "update_date": item.get("update_date", item.get("updateDate", item.get("dateUpdate", ""))),
            "source_payload_json": item,
        }

        # Build card_url if only external_id available
        if record["external_id"] and not record["card_url"]:
            view_base = self._build_url(settings.rubricator_view_path)
            record["card_url"] = f"{view_base}/{record['external_id']}"

        # Normalize relative URLs
        for key in ("card_url", "html_url", "pdf_url"):
            val = record.get(key)
            if isinstance(val, str) and val.startswith("/"):
                record[key] = f"{settings.rubricator_base_url.rstrip('/')}{val}"

        return record

    def _collect_candidate_items(self, data) -> list[dict]:
        """Recursively collect list items that look like document cards."""
        out: list[dict] = []

        def looks_like_doc(item: dict) -> bool:
            text = " ".join(str(item.get(k, "")) for k in ("Name", "title", "name", "Title", "url", "link", "CodeVersion"))
            keys = {k.lower() for k in item.keys()}
            return bool(
                re.search(r"(рекомендац|клинич|clin)", text, flags=re.IGNORECASE)
                or ("id" in keys and ("title" in keys or "name" in keys))
                or "pdf" in keys
                or "html_url" in keys
                or "pdf_url" in keys
            )

        def walk(node):
            if isinstance(node, dict):
                if looks_like_doc(node):
                    out.append(node)
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(data)
        return out

    def _discover_from_runtime_state(self) -> list[dict]:
        """Try reading runtime JS objects that may hold already loaded records."""
        records: list[dict] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            try:
                list_url = self._list_urls()[0]
                page.goto(list_url, wait_until="networkidle", timeout=60000)
                time.sleep(settings.discovery_request_delay)

                state_dump = page.evaluate(
                    """
                    () => {
                      const result = [];
                      for (const k of Object.keys(window)) {
                        if (/store|state|data|list|items/i.test(k)) {
                          try {
                            const v = window[k];
                            if (v && typeof v === 'object') {
                              result.push({ key: k, value: JSON.stringify(v).slice(0, 200000) });
                            }
                          } catch (e) {}
                        }
                      }
                      return result;
                    }
                    """
                )

                for entry in state_dump or []:
                    try:
                        parsed = json.loads(entry.get("value", "{}"))
                    except Exception:
                        continue
                    for item in self._collect_candidate_items(parsed):
                        rec = self._normalize_item(item, "runtime-state")
                        if rec.get("title"):
                            records.append(rec)
            except Exception as e:
                logger.warning("Runtime state fallback failed: %s", e)
            finally:
                browser.close()
        return records

    def _deduplicate_records(self, records: list[dict]) -> list[dict]:
        """Deduplicate by external_id/card_url/title to avoid noisy payload duplication."""
        seen: set[str] = set()
        unique: list[dict] = []
        for rec in records:
            key = str(
                rec.get("external_id")
                or rec.get("card_url")
                or rec.get("html_url")
                or rec.get("title")
                or ""
            )
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(rec)
        return unique

    def _discover_from_dom(self) -> list[dict]:
        """Fallback: parse document list from DOM if no API payloads were captured."""
        records = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            try:
                list_url = self._list_urls()[0]
                page.goto(list_url, wait_until="networkidle", timeout=60000)
                time.sleep(settings.discovery_request_delay)

                self._trigger_spa_activity(page)

                view_path = settings.rubricator_view_path.strip("/")
                links = page.query_selector_all(
                    ", ".join(
                        [
                            f"a[href*='/{view_path}/']",
                            "a[href*='/schema/']",
                            "a[href*='/clin-rec/view/']",
                            "a[href*='/clin_recomend/view/']",
                        ]
                    )
                )
                for link in links:
                    href = link.get_attribute("href") or ""
                    text = (link.inner_text() or "").strip()
                    if not text:
                        continue

                    ext_id = href.rstrip("/").split("/")[-1] if "/" in href else ""
                    full_url = href if href.startswith("http") else f"{settings.rubricator_base_url}{href}"

                    records.append({
                        "external_id": ext_id,
                        "title": text,
                        "card_url": full_url,
                        "source_payload_json": {"dom_href": href, "dom_text": text},
                    })

                # New rubricator SPA often renders rows without href links; parse table cells directly.
                row_records = self._extract_records_from_table_rows(page)
                records.extend(row_records)
            except Exception as e:
                logger.warning("DOM fallback failed: %s", e)
            finally:
                browser.close()

        return records

    def _extract_records_from_table_rows(self, page) -> list[dict]:
        """Extract document rows from visible table when links are not present in markup."""
        records: list[dict] = []
        try:
            rows = page.query_selector_all("table tbody tr")
        except Exception:
            rows = []

        for row in rows:
            try:
                cells = row.query_selector_all("td")
                if len(cells) < 3:
                    continue

                external_id = (cells[1].inner_text() or "").strip()
                title = (cells[2].inner_text() or "").strip()
                if not external_id or not title:
                    continue

                view_base = self._build_url(settings.rubricator_view_path)
                records.append(
                    {
                        "external_id": external_id,
                        "title": title,
                        "card_url": f"{view_base}/{external_id}",
                        "source_payload_json": {
                            "dom_row": True,
                            "id": external_id,
                            "title": title,
                        },
                    }
                )
            except Exception:
                continue

        return records

    def _upsert_records(self, session, records: list[dict], mode: str) -> tuple[int, int]:
        """Insert or update document registry records. Returns (total, new_or_updated)."""
        discovered = len(records)
        new_count = 0
        now = datetime.now(timezone.utc)

        for rec in records:
            ext_id = rec.get("external_id")
            if not ext_id:
                continue

            existing = session.query(DocumentRegistry).filter_by(external_id=ext_id).first()
            if existing:
                existing.last_seen_at = now
                if rec.get("title"):
                    existing.title = rec["title"]
                if rec.get("html_url"):
                    existing.html_url = rec["html_url"]
                if rec.get("pdf_url"):
                    existing.pdf_url = rec["pdf_url"]
                if rec.get("specialty"):
                    existing.specialty = rec["specialty"]
                if rec.get("update_date"):
                    existing.update_date = rec["update_date"]
                if rec.get("source_payload_json"):
                    existing.source_payload_json = rec["source_payload_json"]
            else:
                doc = DocumentRegistry(
                    external_id=ext_id,
                    title=rec.get("title", ""),
                    card_url=rec.get("card_url"),
                    html_url=rec.get("html_url"),
                    pdf_url=rec.get("pdf_url"),
                    specialty=rec.get("specialty"),
                    age_group=rec.get("age_group"),
                    status=rec.get("status"),
                    version_label=rec.get("version_label"),
                    publish_date=rec.get("publish_date"),
                    update_date=rec.get("update_date"),
                    source_payload_json=rec.get("source_payload_json"),
                    discovered_at=now,
                    last_seen_at=now,
                )
                session.add(doc)
                new_count += 1

        session.commit()
        return discovered, new_count

    def _get_probe_candidates(self, session, mode: str) -> list[int]:
        """Return registry IDs that need probing."""
        from sqlalchemy import select

        from app.models.document import DocumentVersion

        query = session.query(DocumentRegistry.id)
        if mode == "incremental":
            subquery = select(DocumentVersion.id).where(
                DocumentVersion.registry_id == DocumentRegistry.id
            ).exists()
            query = query.filter(~subquery)
        return [r[0] for r in query.all()]
