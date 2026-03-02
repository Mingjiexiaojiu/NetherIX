"""File organizer skill: sort files into folders by type/date."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from loguru import logger

from netherix.skills.base_skill import BaseSkill, SkillResult

_CATEGORY_MAP = {
    "图片": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"},
    "文档": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".csv", ".rtf"},
    "视频": {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"},
    "音频": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"},
    "压缩包": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "代码": {".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".html", ".css"},
    "可执行": {".exe", ".msi", ".bat", ".cmd", ".ps1", ".sh"},
}


def _categorize(suffix: str) -> str:
    suffix = suffix.lower()
    for category, exts in _CATEGORY_MAP.items():
        if suffix in exts:
            return category
    return "其他"


class FileOrganizerSkill(BaseSkill):
    name = "file_organize"
    description = "按文件类型自动整理指定目录下的文件到子文件夹"
    parameters_schema = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "要整理的目录路径",
            },
            "dry_run": {
                "type": "boolean",
                "description": "如果为true，只预览不实际移动",
                "default": True,
            },
        },
        "required": ["directory"],
    }

    async def execute(self, params: dict[str, Any]) -> SkillResult:
        directory = params.get("directory", "")
        dry_run = params.get("dry_run", True)

        p = Path(directory)
        if not p.exists() or not p.is_dir():
            return SkillResult(False, f"目录不存在: {directory}")

        plan: dict[str, list[str]] = defaultdict(list)
        for item in p.iterdir():
            if item.is_file() and not item.name.startswith("."):
                cat = _categorize(item.suffix)
                plan[cat].append(item.name)

        if not plan:
            return SkillResult(True, "目录中没有需要整理的文件")

        if not dry_run:
            moved = 0
            for cat, files in plan.items():
                target_dir = p / cat
                target_dir.mkdir(exist_ok=True)
                for fname in files:
                    src = p / fname
                    dst = target_dir / fname
                    if dst.exists():
                        dst = target_dir / f"{src.stem}_1{src.suffix}"
                    src.rename(dst)
                    moved += 1
            msg = f"已整理 {moved} 个文件到 {len(plan)} 个分类文件夹"
        else:
            lines = ["📁 整理预览:"]
            for cat, files in sorted(plan.items()):
                lines.append(f"  [{cat}] ({len(files)}个): {', '.join(files[:5])}")
                if len(files) > 5:
                    lines.append(f"    ... 还有 {len(files) - 5} 个文件")
            msg = "\n".join(lines)

        return SkillResult(True, msg, {"plan": dict(plan), "dry_run": dry_run})
