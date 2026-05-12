from __future__ import annotations

from typing import Any

from app.models import Reminder, ServiceResult, now_iso
from app.storage import JSONReminderStorage


class ReminderService:
    def __init__(self, storage: JSONReminderStorage) -> None:
        self.storage = storage

    def _next_id(self, reminders: list[dict[str, Any]]) -> str:
        if not reminders:
            return "rem_0001"
        nums = []
        for r in reminders:
            rid = r.get("reminder_id", "")
            if rid.startswith("rem_"):
                try:
                    nums.append(int(rid.split("_")[1]))
                except (IndexError, ValueError):
                    pass
        return f"rem_{(max(nums) + 1 if nums else 1):04d}"

    def _result(self, status: str, **kwargs: Any) -> dict[str, Any]:
        payload = ServiceResult(status=status, **kwargs).model_dump(exclude_none=True)
        payload["state"] = "success" if status == "success" else False
        return payload

    def create_reminder(self, time_text: str | None, task: str | None, target: str = "self") -> dict[str, Any]:
        missing = []
        if not time_text:
            missing.append("time_text")
        if not task:
            missing.append("task")
        if missing:
            return self._result(
                status="missing_fields",
                missing_fields=missing,
                message="Missing required fields: " + ", ".join(missing),
            )

        reminders = self.storage.load()
        ts = now_iso()
        reminder = Reminder(
            reminder_id=self._next_id(reminders),
            task=task,
            scheduled_time=time_text,
            time_text=time_text,
            target="self" if target != "self" else target,
            status="active",
            created_at=ts,
            updated_at=ts,
        )
        reminders.append(reminder.model_dump())
        self.storage.save(reminders)
        return self._result(
            status="success",
            reminder_id=reminder.reminder_id,
            reminder=reminder.model_dump(),
        )

    def query_reminder(self, time_text: str | None = None, task: str | None = None, target: str = "self") -> dict[str, Any]:
        reminders = [r for r in self.storage.load() if r.get("status") == "active"]
        matches = [
            r for r in reminders
            if (not time_text or r.get("time_text") == time_text)
            and (not task or r.get("task") == task)
            and r.get("target") == ("self" if target != "self" else target)
        ]
        if not matches:
            return self._result(status="not_found", message="No matching reminder found.")
        return self._result(status="success", reminders=matches)

    def _find_candidates(self, reminder_id: str | None = None, time_text: str | None = None, task: str | None = None, target: str = "self") -> list[dict[str, Any]]:
        reminders = [r for r in self.storage.load() if r.get("status") == "active"]
        if reminder_id:
            return [r for r in reminders if r.get("reminder_id") == reminder_id]
        return [
            r for r in reminders
            if (not time_text or r.get("time_text") == time_text)
            and (not task or r.get("task") == task)
            and r.get("target") == ("self" if target != "self" else target)
        ]

    def delete_reminder(self, reminder_id: str | None = None, time_text: str | None = None, task: str | None = None, target: str = "self") -> dict[str, Any]:
        if not reminder_id and not time_text and not task:
            return self._result(
                status="missing_fields",
                missing_fields=["reminder_id|time_text|task"],
                message="Provide reminder_id or filter fields.",
            )

        candidates = self._find_candidates(reminder_id, time_text, task, target)
        if not candidates:
            return self._result(status="not_found", message="No matching reminder found.")
        if len(candidates) > 1:
            compact = [{"reminder_id": r["reminder_id"], "task": r["task"], "scheduled_time": r["scheduled_time"]} for r in candidates]
            return self._result(status="ambiguous", candidates=compact)

        reminders = self.storage.load()
        rid = candidates[0]["reminder_id"]
        ok = False
        for r in reminders:
            if r.get("reminder_id") == rid and r.get("status") == "active":
                r["status"] = "deleted"
                r["updated_at"] = now_iso()
                ok = True
                break
        self.storage.save(reminders)
        if not ok:
            return self._result(status="error", message="Failed to delete reminder.")
        return self._result(status="success", reminder_id=rid)

    def update_reminder(self, reminder_id: str | None = None, time_text: str | None = None, task: str | None = None, new_time_text: str | None = None, new_task: str | None = None, target: str = "self") -> dict[str, Any]:
        if not new_time_text and not new_task:
            return self._result(
                status="missing_fields",
                missing_fields=["new_time_text|new_task"],
                message="At least one update field is required.",
            )
        if not reminder_id and not time_text and not task:
            return self._result(
                status="missing_fields",
                missing_fields=["reminder_id|time_text|task"],
                message="Provide reminder_id or filter fields.",
            )

        candidates = self._find_candidates(reminder_id, time_text, task, target)
        if not candidates:
            return self._result(status="not_found", message="No matching reminder found.")
        if len(candidates) > 1:
            compact = [{"reminder_id": r["reminder_id"], "task": r["task"], "scheduled_time": r["scheduled_time"]} for r in candidates]
            return self._result(status="ambiguous", candidates=compact)

        reminders = self.storage.load()
        rid = candidates[0]["reminder_id"]
        updated = None
        for r in reminders:
            if r.get("reminder_id") == rid and r.get("status") == "active":
                if new_time_text:
                    r["time_text"] = new_time_text
                    r["scheduled_time"] = new_time_text
                if new_task:
                    r["task"] = new_task
                r["updated_at"] = now_iso()
                updated = r
                break
        self.storage.save(reminders)
        if not updated:
            return self._result(status="error", message="Failed to update reminder.")
        return self._result(status="success", reminder_id=rid, reminder=updated)
