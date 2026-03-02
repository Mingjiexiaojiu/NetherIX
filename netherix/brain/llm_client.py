"""OpenAI-compatible LLM client with function calling support."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger
from openai import OpenAI


class LLMClient:
    """Thin wrapper around the OpenAI chat completions API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: str = "",
    ):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt

    def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Send a chat completion request.

        Returns a dict with keys:
            - content: str | None
            - tool_calls: list[dict] | None  (each has id, function.name, function.arguments)
            - usage: dict
        """
        full_messages = []
        if self._system_prompt:
            full_messages.append({"role": "system", "content": self._system_prompt})
        full_messages.extend(messages)

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": full_messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            resp = self._client.chat.completions.create(**kwargs)
        except Exception as e:
            logger.error("LLM request failed: {}", e)
            return {"content": f"抱歉，AI 服务暂时不可用：{e}", "tool_calls": None, "usage": {}}

        choice = resp.choices[0]
        msg = choice.message

        tool_calls = None
        if msg.tool_calls:
            tool_calls = []
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        return {
            "content": msg.content,
            "tool_calls": tool_calls,
            "usage": {
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
            },
        }

    def chat_stream(self, messages: list[dict[str, str]]):
        """Streaming chat, yields content chunks."""
        full_messages = []
        if self._system_prompt:
            full_messages.append({"role": "system", "content": self._system_prompt})
        full_messages.extend(messages)

        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=full_messages,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            logger.error("LLM stream failed: {}", e)
            yield f"[AI 服务错误: {e}]"
