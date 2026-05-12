from __future__ import annotations

from app.reminder_service import ReminderService
from app.storage import JSONReminderStorage


def make_service(tmp_path):
    return ReminderService(JSONReminderStorage(tmp_path / "reminders.json"))


def test_create_reminder_success(tmp_path):
    svc = make_service(tmp_path)
    result = svc.create_reminder(time_text="tomorrow 8am", task="take medicine")
    assert result["status"] == "success"
    assert result["state"] == "success"
    assert result["reminder"]["task"] == "take medicine"


def test_create_reminder_missing_fields(tmp_path):
    svc = make_service(tmp_path)
    result = svc.create_reminder(time_text="", task=None)
    assert result["status"] == "missing_fields"
    assert result["state"] is False
    assert "time_text" in result["missing_fields"]
    assert "task" in result["missing_fields"]


def test_query_reminder_not_found(tmp_path):
    svc = make_service(tmp_path)
    result = svc.query_reminder(task="not-exist")
    assert result["status"] == "not_found"
    assert result["state"] is False


def test_query_reminder_success(tmp_path):
    svc = make_service(tmp_path)
    svc.create_reminder(time_text="tonight 9pm", task="close window")
    result = svc.query_reminder(task="close window")
    assert result["status"] == "success"
    assert result["state"] == "success"
    assert len(result["reminders"]) == 1


def test_update_reminder_ambiguous(tmp_path):
    svc = make_service(tmp_path)
    svc.create_reminder(time_text="8am", task="pill")
    svc.create_reminder(time_text="8pm", task="pill")
    result = svc.update_reminder(task="pill", new_task="water")
    assert result["status"] == "ambiguous"
    assert result["state"] is False
    assert len(result["candidates"]) == 2


def test_delete_reminder_ambiguous(tmp_path):
    svc = make_service(tmp_path)
    svc.create_reminder(time_text="8am", task="pill")
    svc.create_reminder(time_text="8pm", task="pill")
    result = svc.delete_reminder(task="pill")
    assert result["status"] == "ambiguous"
    assert result["state"] is False


def test_update_and_delete_success(tmp_path):
    svc = make_service(tmp_path)
    created = svc.create_reminder(time_text="fri morning", task="pay bill")
    rid = created["reminder_id"]

    updated = svc.update_reminder(reminder_id=rid, new_task="pay water bill")
    assert updated["status"] == "success"
    assert updated["state"] == "success"
    assert updated["reminder"]["task"] == "pay water bill"

    deleted = svc.delete_reminder(reminder_id=rid)
    assert deleted["status"] == "success"
    assert deleted["state"] == "success"

    queried = svc.query_reminder(task="pay water bill")
    assert queried["status"] == "not_found"
    assert queried["state"] is False
