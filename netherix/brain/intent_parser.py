"""Intent recognition via LLM with structured classification."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from loguru import logger

from netherix.brain.llm_client import LLMClient


class Intent(Enum):
    CHAT = "chat"
    SYSTEM_OP = "system_op"
    FILE_OP = "file_op"
    SKILL_CALL = "skill_call"
    INFO_QUERY = "info_query"

    @classmethod
    def from_str(cls, s: str) -> "Intent":
        for member in cls:
            if member.value == s:
                return member
        return cls.CHAT


_CLASSIFICATION_PROMPT = """你是一个意图分类器。根据用户输入，判断意图类型并提取关键参数。

意图类型：
- chat: 日常闲聊、问候、情感交流
- system_op: 系统操作（打开应用、调节音量、截图、鼠标键盘操作等）
- file_op: 文件操作（创建、删除、移动、搜索、整理文件等）
- skill_call: 需要调用特定技能（搜索、翻译、天气、计算、提醒等）
- info_query: 信息查询（知识问答、解释概念等）

以JSON格式回复：
{"intent": "<类型>", "params": {<提取的关键参数>}, "summary": "<一句话描述用户需求>"}"""


class IntentParser:
    """Classifies user input into intents with extracted parameters."""

    def __init__(self, llm: LLMClient):
        self._llm = llm

    def parse(self, user_input: str) -> dict[str, Any]:
        """Classify intent and extract parameters.

        Returns:
            {"intent": Intent, "params": dict, "summary": str}
        """
        messages = [
            {"role": "system", "content": _CLASSIFICATION_PROMPT},
            {"role": "user", "content": user_input},
        ]
        result = self._llm.chat(messages)
        content = result.get("content", "")

        try:
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed = json.loads(content)
            return {
                "intent": Intent.from_str(parsed.get("intent", "chat")),
                "params": parsed.get("params", {}),
                "summary": parsed.get("summary", user_input),
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Intent parse failed, falling back to CHAT: {}", e)
            return {
                "intent": Intent.CHAT,
                "params": {},
                "summary": user_input,
            }
