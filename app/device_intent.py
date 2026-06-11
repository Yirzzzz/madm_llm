from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


DEVICE_CAPABILITIES: list[dict[str, Any]] = [
    {"id": 1, "intent": "call_manager", "name": "呼叫管理员", "required_slots": []},
    {"id": 2, "intent": "call_contact", "name": "呼叫联系人", "required_slots": ["contact"]},
    {"id": 3, "intent": "answer_call", "name": "接听来电", "required_slots": []},
    {"id": 4, "intent": "unlock", "name": "开锁", "required_slots": []},
    {"id": 5, "intent": "end_or_reject_call", "name": "拒接/挂断", "required_slots": ["action"]},
    {"id": 6, "intent": "change_wallpaper", "name": "更换壁纸", "required_slots": ["wallpaper_type"]},
    {"id": 7, "intent": "set_dnd", "name": "切换勿扰模式", "required_slots": ["enabled"]},
    {"id": 8, "intent": "set_volume", "name": "调节音量", "required_slots": ["adjustment"]},
    {"id": 9, "intent": "set_brightness", "name": "调节屏幕亮度", "required_slots": ["adjustment"]},
    {"id": 10, "intent": "set_security_mode", "name": "布防/撤防", "required_slots": ["enabled"]},
    {"id": 11, "intent": "query_alarm_records", "name": "查询告警记录", "required_slots": []},
    {"id": 12, "intent": "monitor_control", "name": "监控管理", "required_slots": ["action"]},
    {"id": 13, "intent": "view_messages", "name": "查看通知/短信", "required_slots": []},
]

CAPABILITY_BY_INTENT = {item["intent"]: item for item in DEVICE_CAPABILITIES}


@dataclass(frozen=True)
class IntentParse:
    intent: str | None
    slots: dict[str, Any]
    confidence: float
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "slots": self.slots,
            "confidence": self.confidence,
            "message": self.message,
        }


def parse_device_command(text: str | None) -> IntentParse:
    normalized = _normalize(text)
    if not normalized:
        return IntentParse(None, {}, 0.0, "Command text is empty.")

    if _has_any(normalized, ["管理员", "物业"]):
        return IntentParse("call_manager", {"contact": "manager"}, 0.95)

    if _has_any(normalized, ["接听", "接电话", "接一下", "接来电"]):
        return IntentParse("answer_call", {}, 0.95)

    if _has_any(normalized, ["拒接", "拒绝来电"]):
        return IntentParse("end_or_reject_call", {"action": "reject"}, 0.95)

    if _has_any(normalized, ["挂断", "挂电话", "挂了"]):
        return IntentParse("end_or_reject_call", {"action": "hangup"}, 0.95)

    if _has_any(normalized, ["开锁", "打开门锁", "远程开门", "开门"]):
        return IntentParse("unlock", {"method": "remote"}, 0.95)

    if "壁纸" in normalized:
        return IntentParse("change_wallpaper", _parse_wallpaper_slots(normalized), 0.9)

    if _has_any(normalized, ["勿扰", "免打扰"]):
        return IntentParse("set_dnd", _parse_enabled_slots(normalized), 0.9)

    if "音量" in normalized or _has_any(normalized, ["声音", "静音"]):
        return IntentParse("set_volume", _parse_level_slots(normalized), 0.9)

    if "亮度" in normalized or _has_any(normalized, ["屏幕亮", "屏幕暗"]):
        return IntentParse("set_brightness", _parse_level_slots(normalized), 0.9)

    if _has_any(normalized, ["布防", "撤防", "安防"]):
        return IntentParse("set_security_mode", _parse_security_slots(normalized), 0.9)

    if _has_any(normalized, ["告警", "报警"]):
        return IntentParse("query_alarm_records", _parse_time_range_slots(normalized), 0.9)

    if _has_any(normalized, ["监控", "摄像头", "录像", "通道", "画面"]):
        return IntentParse("monitor_control", _parse_monitor_slots(normalized), 0.9)

    if _has_any(normalized, ["通知", "短信", "消息"]):
        return IntentParse("view_messages", _parse_message_slots(normalized), 0.9)

    if _has_any(normalized, ["打电话", "拨打", "呼叫", "联系"]):
        slots = _parse_contact_slots(normalized)
        return IntentParse("call_contact", slots, 0.8)

    return IntentParse(None, {}, 0.0, "No supported device intent matched.")


def missing_required_slots(intent: str, slots: dict[str, Any]) -> list[str]:
    capability = CAPABILITY_BY_INTENT.get(intent)
    if capability is None:
        return []
    return [slot for slot in capability["required_slots"] if slots.get(slot) in (None, "", [])]


def _normalize(text: str | None) -> str:
    return (text or "").strip().replace(" ", "")


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _parse_contact_slots(text: str) -> dict[str, Any]:
    if "家人" in text:
        return {"contact": "family"}
    if "常用联系人" in text:
        return {"contact": "frequent_contacts"}
    if "服务电话" in text:
        return {"contact": "service_phone"}

    match = re.search(r"(?:给|帮我给|拨打|呼叫|联系)([^，。！？、]+?)(?:打电话|电话|$)", text)
    if match:
        contact = match.group(1).strip()
        if contact and contact not in {"我", "一下"}:
            return {"contact": contact}
    return {}


def _parse_wallpaper_slots(text: str) -> dict[str, Any]:
    for wallpaper_type in ["风景", "默认", "家庭", "节日", "卡通", "纯色", "深色", "浅色"]:
        if wallpaper_type in text:
            return {"wallpaper_type": wallpaper_type}
    return {}


def _parse_enabled_slots(text: str) -> dict[str, Any]:
    if _has_any(text, ["开启", "打开", "启用", "开一下", "设为"]):
        return {"enabled": True}
    if _has_any(text, ["关闭", "取消", "关掉", "停用"]):
        return {"enabled": False}
    return {}


def _parse_security_slots(text: str) -> dict[str, Any]:
    if "布防" in text or _has_any(text, ["开启安防", "打开安防"]):
        return {"enabled": True}
    if "撤防" in text or _has_any(text, ["关闭安防", "取消安防"]):
        return {"enabled": False}
    return {}


def _parse_level_slots(text: str) -> dict[str, Any]:
    if _has_any(text, ["最大", "最高", "最亮"]):
        return {"adjustment": "set", "level": "max"}
    if _has_any(text, ["最小", "最低", "最暗"]):
        return {"adjustment": "set", "level": "min"}
    if _has_any(text, ["调高", "调大", "大一点", "高一点", "亮一点", "增加"]):
        return {"adjustment": "up"}
    if _has_any(text, ["调低", "调小", "小一点", "低一点", "暗一点", "降低"]):
        return {"adjustment": "down"}
    number = re.search(r"(\d{1,3})", text)
    if number:
        return {"adjustment": "set", "level": min(int(number.group(1)), 100)}
    if "静音" in text:
        return {"adjustment": "set", "level": 0}
    return {}


def _parse_time_range_slots(text: str) -> dict[str, Any]:
    for label in ["今天", "昨天", "前天", "最近一周", "近一周", "最近三天", "这个月", "上个月"]:
        if label in text:
            return {"time_range": label}
    return {}


def _parse_monitor_slots(text: str) -> dict[str, Any]:
    slots: dict[str, Any] = {}
    if _has_any(text, ["打开", "开启"]):
        slots["action"] = "open"
    elif _has_any(text, ["关闭", "关掉"]):
        slots["action"] = "close"
    elif _has_any(text, ["回放", "录像"]):
        slots["action"] = "playback"
    elif _has_any(text, ["切换", "换到"]):
        slots["action"] = "switch_channel"
    elif _has_any(text, ["查看", "看一下", "看看"]):
        slots["action"] = "view"

    for scene in ["门口", "客厅", "卧室", "电梯", "走廊", "车库"]:
        if scene in text:
            slots["scene"] = scene
            break

    channel = re.search(r"(\d+)通道", text)
    if channel:
        slots["channel"] = int(channel.group(1))
    return slots


def _parse_message_slots(text: str) -> dict[str, Any]:
    slots: dict[str, Any] = {}
    if "短信" in text:
        slots["message_type"] = "sms"
    elif "通知" in text:
        slots["message_type"] = "notification"
    else:
        slots["message_type"] = "all"
    if _has_any(text, ["新", "未读"]):
        slots["unread_only"] = True
    return slots
