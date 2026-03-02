"""Multi-step task planner: decomposes complex tasks into executable steps."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from netherix.brain.intent_parser import Intent
from netherix.brain.llm_client import LLMClient


class StepType(Enum):
    AUTOMATION = "automation"
    SKILL = "skill"
    REPLY = "reply"


@dataclass
class PlanStep:
    step_type: StepType
    action: str
    params: dict = field(default_factory=dict)
    description: str = ""


@dataclass
class ExecutionPlan:
    summary: str
    steps: list[PlanStep]
    original_input: str = ""


_PLANNER_PROMPT = """你是任务规划器。将用户需求分解为可执行步骤。

每步的格式：
{"type": "automation|skill|reply", "action": "<具体动作>", "params": {<参数>}, "desc": "<描述>"}

动作类型：
- automation: 系统自动化操作（open_app, click, type_text, hotkey, volume, screenshot, file_create, file_delete, file_move, file_search, file_list）
- skill: 调用技能（web_search, translate, calculate, weather, remind, file_organize）
- reply: 直接回复用户

以JSON返回步骤列表：
{"summary": "<任务摘要>", "steps": [<步骤列表>]}"""


class TaskPlanner:
    """Breaks down complex requests into executable step sequences."""

    def __init__(self, llm: LLMClient):
        self._llm = llm

    def plan(self, user_input: str, intent: Intent, params: dict) -> ExecutionPlan:
        """Generate an execution plan for the given intent."""
        if intent == Intent.CHAT:
            return ExecutionPlan(
                summary="闲聊回复",
                steps=[PlanStep(StepType.REPLY, "chat_reply", {"input": user_input})],
                original_input=user_input,
            )

        messages = [
            {"role": "system", "content": _PLANNER_PROMPT},
            {"role": "user", "content": f"用户需求: {user_input}\n意图: {intent.value}\n提取参数: {json.dumps(params, ensure_ascii=False)}"},
        ]

        result = self._llm.chat(messages)
        content = result.get("content", "")

        try:
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed = json.loads(content)
            steps = []
            for s in parsed.get("steps", []):
                step_type = StepType(s.get("type", "reply"))
                steps.append(PlanStep(
                    step_type=step_type,
                    action=s.get("action", ""),
                    params=s.get("params", {}),
                    description=s.get("desc", ""),
                ))
            return ExecutionPlan(
                summary=parsed.get("summary", user_input),
                steps=steps or [PlanStep(StepType.REPLY, "chat_reply", {"input": user_input})],
                original_input=user_input,
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Plan parse failed, fallback to reply: {}", e)
            return ExecutionPlan(
                summary=user_input,
                steps=[PlanStep(StepType.REPLY, "chat_reply", {"input": user_input})],
                original_input=user_input,
            )
