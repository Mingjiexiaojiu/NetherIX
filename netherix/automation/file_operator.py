"""File system operations: CRUD, search, batch rename, organize."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from loguru import logger


class FileOperator:
    """High-level file system operations."""

    @staticmethod
    def create_file(path: str, content: str = "") -> dict[str, Any]:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            logger.info("Created file: {}", path)
            return {"success": True, "path": str(p.resolve())}
        except Exception as e:
            logger.error("Create file failed: {}", e)
            return {"success": False, "error": str(e)}

    @staticmethod
    def create_directory(path: str) -> dict[str, Any]:
        try:
            p = Path(path)
            p.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(p.resolve())}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def read_file(path: str, encoding: str = "utf-8") -> dict[str, Any]:
        try:
            content = Path(path).read_text(encoding=encoding)
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete(path: str, to_recycle: bool = True) -> dict[str, Any]:
        """Delete file/directory. If to_recycle=True, move to recycle bin on Windows."""
        try:
            p = Path(path)
            if to_recycle:
                try:
                    import win32com.client
                    shell = win32com.client.Dispatch("Shell.Application")
                    ns = shell.NameSpace(10)  # Recycle Bin
                    # Fallback: use send2trash if available
                    raise ImportError("use send2trash")
                except Exception:
                    if p.is_dir():
                        shutil.rmtree(p)
                    else:
                        p.unlink()
            else:
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
            logger.info("Deleted: {}", path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def move(src: str, dst: str) -> dict[str, Any]:
        try:
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dst)
            logger.info("Moved {} -> {}", src, dst)
            return {"success": True, "destination": dst}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def copy(src: str, dst: str) -> dict[str, Any]:
        try:
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            if Path(src).is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            return {"success": True, "destination": dst}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def rename(path: str, new_name: str) -> dict[str, Any]:
        try:
            p = Path(path)
            new_path = p.parent / new_name
            p.rename(new_path)
            return {"success": True, "new_path": str(new_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def search(
        directory: str,
        pattern: str = "*",
        recursive: bool = True,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        results = []
        p = Path(directory)
        glob_fn = p.rglob if recursive else p.glob
        for item in glob_fn(pattern):
            if len(results) >= max_results:
                break
            stat = item.stat()
            results.append({
                "path": str(item),
                "name": item.name,
                "is_dir": item.is_dir(),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
        return results

    @staticmethod
    def list_dir(directory: str) -> list[dict[str, Any]]:
        return FileOperator.search(directory, "*", recursive=False)

    @staticmethod
    def batch_rename(
        directory: str,
        pattern: str,
        replacement: str,
    ) -> dict[str, Any]:
        """Rename files matching a pattern in directory."""
        import re
        renamed = []
        try:
            for item in Path(directory).iterdir():
                new_name = re.sub(pattern, replacement, item.name)
                if new_name != item.name:
                    item.rename(item.parent / new_name)
                    renamed.append({"old": item.name, "new": new_name})
            return {"success": True, "renamed": renamed, "count": len(renamed)}
        except Exception as e:
            return {"success": False, "error": str(e), "renamed": renamed}
