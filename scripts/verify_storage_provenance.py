#!/usr/bin/env python3
"""
Runtime check: configured rubricator URLs vs document_registry / source_artifact.
Writes NDJSON to .cursor/debug-9bf364.log for DEBUG MODE evidence.
"""
# region agent log
import json
import time
from pathlib import Path

_DEBUG_LOG = Path(__file__).resolve().parent.parent / ".cursor" / "debug-9bf364.log"
_SESSION = "9bf364"


def _dbg(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    payload = {
        "sessionId": _SESSION,
        "timestamp": int(time.time() * 1000),
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "runId": "verify_storage_provenance",
    }
    _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(_DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


# endregion agent log


def main() -> None:
    # H1: настроенные URL рубрикатора — домены Минздрава
    from app.core.config import settings

    _dbg(
        "H1",
        "verify_storage_provenance:config",
        "rubricator URLs from Settings",
        {
            "rubricator_base_url": settings.rubricator_base_url,
            "rubricator_api_base_url": settings.rubricator_api_base_url,
            "h1_minzdrav_base": "minzdrav.gov.ru" in settings.rubricator_base_url,
            "h1_minzdrav_api": "minzdrav.gov.ru" in settings.rubricator_api_base_url,
        },
    )

    # H2–H4: БД — сколько документов, домены в URL, есть ли raw после fetch
    try:
        from sqlalchemy import func, select

        from app.core.sync_database import get_sync_session
        from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact

        s = get_sync_session()
        try:
            n_reg = s.scalar(select(func.count()).select_from(DocumentRegistry)) or 0
            n_ver = s.scalar(select(func.count()).select_from(DocumentVersion)) or 0
            n_art = s.scalar(select(func.count()).select_from(SourceArtifact)) or 0
            _dbg(
                "H4",
                "verify_storage_provenance:db_counts",
                "table row counts",
                {"document_registry": n_reg, "document_version": n_ver, "source_artifact": n_art},
            )

            rows = s.execute(select(DocumentRegistry).order_by(DocumentRegistry.id).limit(5)).scalars().all()
            samples = []
            minzdrav_urls = 0
            total_urls_checked = 0
            for r in rows:
                for u in (r.card_url, r.html_url, r.pdf_url):
                    if u:
                        total_urls_checked += 1
                        if "minzdrav.gov.ru" in u:
                            minzdrav_urls += 1
                samples.append(
                    {
                        "id": r.id,
                        "external_id": r.external_id,
                        "title": (r.title or "")[:120],
                        "card_url": r.card_url,
                    }
                )
            _dbg(
                "H2",
                "verify_storage_provenance:registry_sample",
                "first N registry rows URL check",
                {
                    "sample_count": len(samples),
                    "urls_with_minzdrav": minzdrav_urls,
                    "non_null_urls": total_urls_checked,
                    "samples": samples,
                },
            )
            _dbg(
                "H3",
                "verify_storage_provenance:fetch_layer",
                "raw artifacts vs catalog",
                {
                    "has_fetched_raw": n_art > 0,
                    "registry_without_fetch": n_reg > 0 and n_art == 0,
                },
            )
        except Exception as e:  # noqa: BLE001
            _dbg(
                "H4",
                "verify_storage_provenance:db_error",
                "query failed",
                {"error_type": type(e).__name__, "error": str(e)[:500]},
            )
        finally:
            s.close()
    except Exception as e:  # noqa: BLE001
        _dbg(
            "H4",
            "verify_storage_provenance:db_connect",
            "cannot use sync DB",
            {"error_type": type(e).__name__, "error": str(e)[:500]},
        )


if __name__ == "__main__":
    main()
