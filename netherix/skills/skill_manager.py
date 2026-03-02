"""Skill manager: discovery, loading, registration, and dispatch."""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Any

from loguru import logger

from netherix.skills.base_skill import BaseSkill, SkillResult


class SkillManager:
    """Discovers, loads, and dispatches skills."""

    def __init__(self):
        self._skills: dict[str, BaseSkill] = {}

    @property
    def skills(self) -> dict[str, BaseSkill]:
        return dict(self._skills)

    def register(self, skill: BaseSkill):
        self._skills[skill.name] = skill
        logger.info("Registered skill: {}", skill.name)

    def load_builtin(self, enabled: list[str] | None = None):
        """Load built-in skills from netherix.skills.builtin."""
        from netherix.skills.builtin import (
            calculator,
            file_organizer,
            reminder,
            translator,
            weather,
            web_search,
        )
        all_builtins: dict[str, type[BaseSkill]] = {
            "calculator": calculator.CalculatorSkill,
            "translator": translator.TranslatorSkill,
            "web_search": web_search.WebSearchSkill,
            "reminder": reminder.ReminderSkill,
            "weather": weather.WeatherSkill,
            "file_organizer": file_organizer.FileOrganizerSkill,
        }
        for name, cls in all_builtins.items():
            if enabled is None or name in enabled:
                self.register(cls())

    def load_custom_dir(self, directory: str):
        """Dynamically load skills from a directory of .py files."""
        skill_dir = Path(directory)
        if not skill_dir.exists():
            logger.debug("Custom skill dir not found: {}", directory)
            return
        for py_file in skill_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    f"custom_skill.{py_file.stem}", str(py_file),
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                            self.register(obj())
                            logger.info("Loaded custom skill from {}", py_file.name)
            except Exception as e:
                logger.error("Failed to load skill {}: {}", py_file.name, e)

    def get_tools_schema(self) -> list[dict]:
        """Export all skills as OpenAI function-calling tools list."""
        return [skill.as_function_schema() for skill in self._skills.values()]

    async def execute(self, skill_name: str, params: dict[str, Any]) -> SkillResult:
        skill = self._skills.get(skill_name)
        if not skill:
            return SkillResult(False, f"未找到技能: {skill_name}")
        try:
            return await skill.execute(params)
        except Exception as e:
            logger.error("Skill {} failed: {}", skill_name, e)
            return SkillResult(False, f"技能执行失败: {e}")

    def execute_sync(self, skill_name: str, params: dict[str, Any]) -> SkillResult:
        """Synchronous wrapper for execute."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.execute(skill_name, params))
                    return future.result(timeout=30)
            return loop.run_until_complete(self.execute(skill_name, params))
        except RuntimeError:
            return asyncio.run(self.execute(skill_name, params))
