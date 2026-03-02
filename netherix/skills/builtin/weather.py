"""Weather skill: queries weather via wttr.in free API."""

from __future__ import annotations

import urllib.request
import json
from typing import Any

from loguru import logger

from netherix.skills.base_skill import BaseSkill, SkillResult


class WeatherSkill(BaseSkill):
    name = "weather"
    description = "查询城市天气信息（温度、天气状况、湿度、风速）"
    parameters_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称，如：北京、Shanghai、Tokyo",
            },
        },
        "required": ["city"],
    }

    async def execute(self, params: dict[str, Any]) -> SkillResult:
        city = params.get("city", "Beijing")
        try:
            url = f"https://wttr.in/{city}?format=j1"
            req = urllib.request.Request(url, headers={"User-Agent": "NIX/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            current = data.get("current_condition", [{}])[0]
            temp_c = current.get("temp_C", "?")
            feels_like = current.get("FeelsLikeC", "?")
            desc_cn = current.get("lang_zh", [{}])
            desc = desc_cn[0].get("value", "") if desc_cn else current.get("weatherDesc", [{}])[0].get("value", "")
            humidity = current.get("humidity", "?")
            wind_speed = current.get("windspeedKmph", "?")

            msg = (
                f"🌤 {city} 天气\n"
                f"温度: {temp_c}°C（体感 {feels_like}°C）\n"
                f"天气: {desc}\n"
                f"湿度: {humidity}%\n"
                f"风速: {wind_speed} km/h"
            )
            return SkillResult(True, msg, {
                "city": city, "temp_c": temp_c,
                "description": desc, "humidity": humidity,
            })
        except Exception as e:
            logger.error("Weather query failed: {}", e)
            return SkillResult(False, f"天气查询失败: {e}")
