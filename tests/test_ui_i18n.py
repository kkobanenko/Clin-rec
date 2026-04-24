import pandas as pd
import pytest

from app.ui.app import append_recent_task
from app.ui import ui_i18n
from app.ui.ui_i18n import (
    load_language_preference,
    save_language_preference,
    set_current_language,
    tr,
    translate_dataframe,
    translate_markup_text,
)


def test_tr_uses_selected_language_for_exact_keys() -> None:
    set_current_language("ru")
    assert tr("Dashboard") == "Панель"
    assert tr("Status: {status}", status="ok") == "Статус: ok"

    set_current_language("en")
    assert tr("Dashboard") == "Dashboard"


def test_translate_dataframe_translates_columns_values_and_booleans() -> None:
    set_current_language("ru")

    dataframe = pd.DataFrame(
        [
            {
                "review_status": "approved",
                "is_active": True,
                "status": "active",
            }
        ]
    )

    translated = translate_dataframe(dataframe)

    assert list(translated.columns) == ["статус ревью", "активна", "статус"]
    assert translated.iloc[0].to_dict() == {
        "статус ревью": "подтверждено",
        "активна": "да",
        "статус": "активный",
    }


def test_translate_markup_text_translates_wrapped_bold_labels() -> None:
    set_current_language("ru")
    assert translate_markup_text("**Latest Outputs**") == "**Последние выходы**"


def test_language_preference_roundtrip(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    preference_path = tmp_path / "ui_preferences.json"
    monkeypatch.setattr(ui_i18n, "LANGUAGE_STORAGE_PATH", preference_path)

    assert load_language_preference() == "ru"

    save_language_preference("en")

    assert load_language_preference() == "en"


def test_append_recent_task_deduplicates_and_keeps_latest_first() -> None:
    recent_tasks = [
        {"task_id": "old-1", "label": "kb_compile", "origin": "knowledge_base", "queued_at": "t1"},
        {"task_id": "old-2", "label": "output_generate", "origin": "outputs", "queued_at": "t2"},
    ]

    updated_tasks = append_recent_task(
        recent_tasks,
        task_id="old-1",
        label="kb_lint",
        origin="knowledge_base",
    )

    assert [item["task_id"] for item in updated_tasks[:2]] == ["old-1", "old-2"]
    assert updated_tasks[0]["label"] == "kb_lint"
    assert updated_tasks[0]["origin"] == "knowledge_base"