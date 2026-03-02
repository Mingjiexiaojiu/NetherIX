"""Example custom skill: demonstrates how to create a NIX skill plugin."""

from __future__ import annotations

from typing import Any

from netherix.skills.base_skill import BaseSkill, SkillResult


class GreetingSkill(BaseSkill):
    """A simple greeting skill for demonstration."""

    name = "greeting"
    description = "向用户打招呼，可以自定义问候语"
    parameters_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "要问候的人的名字",
                "default": "主人",
            },
            "style": {
                "type": "string",
                "description": "问候风格: normal, formal, cute",
                "default": "normal",
            },
        },
    }

    _GREETINGS = {
        "normal": "你好, {}! 冥九灵在此为你服务~",
        "formal": "尊敬的{}，冥九灵向您问安。",
        "cute": "{}~ 嘿嘿，NIX来啦! ✨",
    }

    async def execute(self, params: dict[str, Any]) -> SkillResult:
        name = params.get("name", "主人")
        style = params.get("style", "normal")
        template = self._GREETINGS.get(style, self._GREETINGS["normal"])
        msg = template.format(name)
        return SkillResult(True, msg, {"name": name, "style": style})
