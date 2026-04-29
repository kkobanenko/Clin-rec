"""Tests for scripts/quality_gate_notify.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_notify


def _gate_payload(verdict: str = "pass"):
    return {
        "verdict": verdict,
        "summary": "summary",
        "rules": [
            {"name": "r1", "status": "pass"},
            {"name": "r2", "status": "warn"},
            {"name": "r3", "status": "fail"},
        ],
    }


def test_run_dry_run_prints_json_and_returns_zero(capsys):
    with patch("scripts.quality_gate_notify._fetch_gate_report", return_value=_gate_payload("warn")):
        code = quality_gate_notify.run([
            "--api-base",
            "http://test",
            "--webhook-url",
            "http://webhook",
            "--dry-run",
        ])

    captured = capsys.readouterr()
    assert code == 0
    assert '"event": "quality_gate_verdict"' in captured.out
    assert '"verdict": "warn"' in captured.out


def test_run_missing_webhook_required_returns_two(capsys):
    code = quality_gate_notify.run(["--api-base", "http://test"])
    captured = capsys.readouterr()
    assert code == 2
    assert "webhook URL is missing" in captured.err


def test_run_missing_webhook_allowed_returns_zero(capsys):
    code = quality_gate_notify.run(["--api-base", "http://test", "--allow-missing-webhook"])
    captured = capsys.readouterr()
    assert code == 0
    assert "skipping" in captured.out


def test_run_returns_two_on_gate_fetch_error(capsys):
    with patch(
        "scripts.quality_gate_notify._fetch_gate_report",
        side_effect=RuntimeError("unreachable"),
    ):
        code = quality_gate_notify.run([
            "--api-base",
            "http://test",
            "--webhook-url",
            "http://webhook",
        ])

    captured = capsys.readouterr()
    assert code == 2
    assert "cannot fetch gate report" in captured.err


def test_run_returns_one_on_webhook_failure(capsys):
    with patch("scripts.quality_gate_notify._fetch_gate_report", return_value=_gate_payload("fail")):
        with patch(
            "scripts.quality_gate_notify._post_with_retries",
            side_effect=RuntimeError("post failed"),
        ):
            code = quality_gate_notify.run([
                "--api-base",
                "http://test",
                "--webhook-url",
                "http://webhook",
            ])

    captured = capsys.readouterr()
    assert code == 1
    assert "webhook post failed" in captured.err


def test_run_posts_and_returns_zero(capsys):
    with patch("scripts.quality_gate_notify._fetch_gate_report", return_value=_gate_payload("pass")):
        with patch("scripts.quality_gate_notify._post_with_retries") as post_mock:
            code = quality_gate_notify.run([
                "--api-base",
                "http://test",
                "--webhook-url",
                "http://webhook",
                "--retries",
                "3",
            ])

    captured = capsys.readouterr()
    assert code == 0
    assert "quality-gate notify: sent verdict=pass" in captured.out
    post_mock.assert_called_once()


def test_run_enqueue_on_failure_with_success_on_enqueue(tmp_path, capsys):
    spool_dir = tmp_path / "queue"
    with patch("scripts.quality_gate_notify._fetch_gate_report", return_value=_gate_payload("warn")):
        with patch(
            "scripts.quality_gate_notify._post_with_retries",
            side_effect=RuntimeError("post failed"),
        ):
            code = quality_gate_notify.run([
                "--api-base",
                "http://test",
                "--webhook-url",
                "http://webhook",
                "--enqueue-on-failure",
                "--succeed-on-enqueue",
                "--spool-dir",
                str(spool_dir),
            ])

    captured = capsys.readouterr()
    assert code == 0
    assert "queued payload after delivery failure" in captured.out
    assert len(list(spool_dir.glob("*.json"))) == 1


def test_run_enqueue_on_missing_webhook_when_allowed(tmp_path, capsys):
    spool_dir = tmp_path / "queue"
    with patch("scripts.quality_gate_notify._fetch_gate_report", return_value=_gate_payload("warn")):
        code = quality_gate_notify.run([
            "--api-base",
            "http://test",
            "--allow-missing-webhook",
            "--enqueue-on-missing-webhook",
            "--spool-dir",
            str(spool_dir),
        ])

    captured = capsys.readouterr()
    assert code == 0
    assert "queued payload because webhook is missing" in captured.out
    assert len(list(spool_dir.glob("*.json"))) == 1


def test_post_with_retries_succeeds_after_retry():
    calls = {"count": 0}

    def _fake_post(_url, json, timeout):  # noqa: ANN001
        del json, timeout
        calls["count"] += 1
        if calls["count"] < 2:
            raise quality_gate_notify.httpx.ConnectError("boom")

        class _Resp:
            def raise_for_status(self):
                return None

        return _Resp()

    with patch("scripts.quality_gate_notify.httpx.post", side_effect=_fake_post):
        quality_gate_notify._post_with_retries(
            webhook_url="http://webhook",
            payload={"x": 1},
            retries=2,
            timeout=1.0,
        )

    assert calls["count"] == 2
