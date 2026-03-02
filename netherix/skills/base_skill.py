"""Base class for all skills (built-in and user-defined)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillResult:
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    """Abstract base for a NIX skill (plugin)."""

    name: str = ""
    description: str = ""
    parameters_schema: dict[str, Any] = {}

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> SkillResult:
        """Execute this skill with the given parameters."""
        ...

    def as_function_schema(self) -> dict:
        """Export as OpenAI function-calling tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema or {
                    "type": "object",
                    "properties": {},
                },
            },
        }
