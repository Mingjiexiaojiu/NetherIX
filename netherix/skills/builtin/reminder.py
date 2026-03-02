"""Reminder/alarm skill with timer-based notifications."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable

from loguru import logger

from netherix.skills.base_skill import BaseSkill, SkillResult


class ReminderSkill(BaseSkill):
    name = "reminder"
    description = "设置提醒或闹钟，到时间后通知用户"
    parameters_schema = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "提醒内容",
            },
            "delay_seconds": {
                "type": "integer",
                "description": "延迟秒数（与 time 二选一）",
            },
            "time": {
                "type": "string",
                "description": "目标时间，格式 HH:MM（与 delay_seconds 二选一）",
            },
        },
        "required": ["message"],
    }

    _notify_callback: Callable[[str], None] | None = None
    _active_reminders: list[dict] = []

    @classmethod
    def set_notify_callback(cls, callback: Callable[[str], None]):
        cls._notify_callback = callback

    async def execute(self, params: dict[str, Any]) -> SkillResult:
        message = params.get("message", "提醒时间到了")
        delay = params.get("delay_seconds")
        target_time = params.get("time")

        if target_time:
            try:
                now = datetime.now()
                h, m = map(int, target_time.split(":"))
                target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                delay = int((target - now).total_seconds())
            except ValueError:
                return SkillResult(False, f"时间格式错误: {target_time}，请使用 HH:MM")

        if not delay or delay <= 0:
            delay = 60

        reminder_info = {
            "message": message,
            "delay": delay,
            "created": datetime.now().isoformat(),
        }
        self._active_reminders.append(reminder_info)

        def _fire():
            time.sleep(delay)
            if self._notify_callback:
                self._notify_callback(f"⏰ 提醒: {message}")
            else:
                logger.info("Reminder fired: {}", message)
            if reminder_info in self._active_reminders:
                self._active_reminders.remove(reminder_info)

        t = threading.Thread(target=_fire, daemon=True)
        t.start()

        if delay >= 3600:
            human_delay = f"{delay // 3600}小时{(delay % 3600) // 60}分钟"
        elif delay >= 60:
            human_delay = f"{delay // 60}分钟"
        else:
            human_delay = f"{delay}秒"

        return SkillResult(
            True,
            f"已设置提醒: {human_delay}后提醒你「{message}」",
            {"delay_seconds": delay},
        )
