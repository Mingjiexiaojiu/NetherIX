"""Web search skill: opens browser with search query."""

from __future__ import annotations

import urllib.parse
import webbrowser
from typing import Any

from netherix.skills.base_skill import BaseSkill, SkillResult


class WebSearchSkill(BaseSkill):
    name = "web_search"
    description = "在浏览器中搜索关键词，支持百度和Google"
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词",
            },
            "engine": {
                "type": "string",
                "description": "搜索引擎: baidu, google, bing",
                "default": "bing",
            },
        },
        "required": ["query"],
    }

    _ENGINES = {
        "baidu": "https://www.baidu.com/s?wd={}",
        "google": "https://www.google.com/search?q={}",
        "bing": "https://www.bing.com/search?q={}",
    }

    async def execute(self, params: dict[str, Any]) -> SkillResult:
        query = params.get("query", "")
        engine = params.get("engine", "bing").lower()

        url_template = self._ENGINES.get(engine, self._ENGINES["bing"])
        url = url_template.format(urllib.parse.quote(query))

        try:
            webbrowser.open(url)
            return SkillResult(True, f"已在{engine}中搜索: {query}", {"url": url})
        except Exception as e:
            return SkillResult(False, f"搜索失败: {e}")
