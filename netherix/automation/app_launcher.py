"""Application launching and window management on Windows."""

from __future__ import annotations

import os
import subprocess
from typing import Any

from loguru import logger

try:
    import win32gui
    import win32con
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logger.warning("pywin32 not available, window management disabled")


class AppLauncher:
    """Launch applications and manage windows on Windows."""

    @staticmethod
    def open_app(name_or_path: str) -> bool:
        """Open an application by name or full path."""
        well_known = {
            "记事本": "notepad",
            "notepad": "notepad",
            "计算器": "calc",
            "calculator": "calc",
            "画图": "mspaint",
            "paint": "mspaint",
            "cmd": "cmd",
            "终端": "wt",
            "terminal": "wt",
            "资源管理器": "explorer",
            "explorer": "explorer",
            "浏览器": "start msedge",
            "browser": "start msedge",
            "设置": "start ms-settings:",
            "settings": "start ms-settings:",
        }
        cmd = well_known.get(name_or_path.lower(), name_or_path)
        try:
            if cmd.startswith("start "):
                os.system(cmd)
            else:
                subprocess.Popen(cmd, shell=True)
            logger.info("Opened app: {}", name_or_path)
            return True
        except Exception as e:
            logger.error("Failed to open {}: {}", name_or_path, e)
            return False

    @staticmethod
    def list_windows() -> list[dict[str, Any]]:
        """List all visible windows with title and handle."""
        if not HAS_WIN32:
            return []
        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append({"hwnd": hwnd, "title": title})
            return True

        win32gui.EnumWindows(callback, None)
        return windows

    @staticmethod
    def focus_window(title_keyword: str) -> bool:
        """Bring a window to foreground by title keyword match."""
        if not HAS_WIN32:
            return False
        for w in AppLauncher.list_windows():
            if title_keyword.lower() in w["title"].lower():
                hwnd = w["hwnd"]
                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    logger.info("Focused window: {}", w["title"])
                    return True
                except Exception as e:
                    logger.error("Focus failed: {}", e)
        return False

    @staticmethod
    def minimize_window(title_keyword: str) -> bool:
        if not HAS_WIN32:
            return False
        for w in AppLauncher.list_windows():
            if title_keyword.lower() in w["title"].lower():
                win32gui.ShowWindow(w["hwnd"], win32con.SW_MINIMIZE)
                return True
        return False

    @staticmethod
    def maximize_window(title_keyword: str) -> bool:
        if not HAS_WIN32:
            return False
        for w in AppLauncher.list_windows():
            if title_keyword.lower() in w["title"].lower():
                win32gui.ShowWindow(w["hwnd"], win32con.SW_MAXIMIZE)
                return True
        return False

    @staticmethod
    def close_window(title_keyword: str) -> bool:
        if not HAS_WIN32:
            return False
        for w in AppLauncher.list_windows():
            if title_keyword.lower() in w["title"].lower():
                win32gui.PostMessage(w["hwnd"], win32con.WM_CLOSE, 0, 0)
                logger.info("Closed window: {}", w["title"])
                return True
        return False
