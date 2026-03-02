"""Conversation memory management with sliding window and summarization."""

from __future__ import annotations

from dataclasses import dataclass, field
from loguru import logger


@dataclass
class MemoryEntry:
    role: str
    content: str
    tool_call_id: str | None = None
    name: str | None = None


class ConversationMemory:
    """Sliding-window memory with optional LLM-based summarization."""

    def __init__(self, max_turns: int = 20, summary_threshold: int = 15):
        self._history: list[MemoryEntry] = []
        self._max_turns = max_turns
        self._summary_threshold = summary_threshold
        self._summary: str = ""

    @property
    def summary(self) -> str:
        return self._summary

    def add(self, role: str, content: str, **kwargs):
        self._history.append(MemoryEntry(role=role, content=content, **kwargs))
        if len(self._history) > self._max_turns:
            self._trim()

    def add_tool_result(self, tool_call_id: str, name: str, content: str):
        self._history.append(MemoryEntry(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            name=name,
        ))

    def get_messages(self) -> list[dict]:
        """Return messages formatted for the LLM API."""
        messages = []
        if self._summary:
            messages.append({
                "role": "system",
                "content": f"之前的对话摘要：{self._summary}",
            })
        for entry in self._history:
            msg: dict = {"role": entry.role, "content": entry.content}
            if entry.tool_call_id:
                msg["tool_call_id"] = entry.tool_call_id
            if entry.name:
                msg["name"] = entry.name
            messages.append(msg)
        return messages

    def _trim(self):
        overflow = len(self._history) - self._max_turns
        if overflow > 0:
            trimmed = self._history[:overflow]
            self._history = self._history[overflow:]
            snippets = [f"{e.role}: {e.content[:80]}" for e in trimmed]
            self._summary += "\n".join(snippets) + "\n"
            logger.debug("Trimmed {} messages from memory", overflow)

    def clear(self):
        self._history.clear()
        self._summary = ""
