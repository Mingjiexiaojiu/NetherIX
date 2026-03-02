"""Translator skill: uses LLM for translation between languages."""

from __future__ import annotations

from typing import Any

from netherix.skills.base_skill import BaseSkill, SkillResult


class TranslatorSkill(BaseSkill):
    name = "translate"
    description = "翻译文本，支持中英日韩等多语言互译"
    parameters_schema = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要翻译的文本",
            },
            "target_language": {
                "type": "string",
                "description": "目标语言，如：中文、English、日本語、한국어",
                "default": "中文",
            },
        },
        "required": ["text"],
    }

    _llm = None

    @classmethod
    def set_llm(cls, llm):
        cls._llm = llm

    async def execute(self, params: dict[str, Any]) -> SkillResult:
        text = params.get("text", "")
        target = params.get("target_language", "中文")

        if not self._llm:
            return SkillResult(False, "翻译服务未初始化（需要 LLM 支持）")

        messages = [
            {"role": "system", "content": f"你是一个翻译器。将用户的文本翻译为{target}。只输出翻译结果，不要解释。"},
            {"role": "user", "content": text},
        ]
        result = self._llm.chat(messages)
        translated = result.get("content", "").strip()
        if translated:
            return SkillResult(True, translated, {"original": text, "translated": translated, "target": target})
        return SkillResult(False, "翻译失败")
