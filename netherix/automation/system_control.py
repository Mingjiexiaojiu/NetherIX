"""System-level controls: volume, brightness, screenshot, system info."""

from __future__ import annotations

import os
import platform
import subprocess
from typing import Any

from loguru import logger


class SystemController:
    """Windows system control operations."""

    @staticmethod
    def set_volume(level: int) -> dict[str, Any]:
        """Set system volume (0-100) using PowerShell on Windows."""
        level = max(0, min(100, level))
        try:
            ps_cmd = (
                f"$vol = (New-Object -ComObject WScript.Shell); "
                f"1..50 | ForEach-Object {{ $vol.SendKeys([char]174) }}; "
                f"1..{level // 2} | ForEach-Object {{ $vol.SendKeys([char]175) }}"
            )
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
            logger.info("Volume set to {}", level)
            return {"success": True, "volume": level}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def mute_volume() -> dict[str, Any]:
        try:
            import pyautogui
            pyautogui.hotkey("volumemute")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def volume_up(steps: int = 1) -> dict[str, Any]:
        try:
            import pyautogui
            for _ in range(steps):
                pyautogui.hotkey("volumeup")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def volume_down(steps: int = 1) -> dict[str, Any]:
        try:
            import pyautogui
            for _ in range(steps):
                pyautogui.hotkey("volumedown")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def take_screenshot(save_path: str | None = None) -> dict[str, Any]:
        try:
            from netherix.automation.mouse_keyboard import MouseKeyboardController
            path = MouseKeyboardController.screenshot()
            if save_path:
                import shutil
                shutil.copy2(path, save_path)
                path = save_path
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def lock_screen() -> dict[str, Any]:
        try:
            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def shutdown(delay: int = 0) -> dict[str, Any]:
        try:
            subprocess.run(f"shutdown /s /t {delay}", shell=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def restart(delay: int = 0) -> dict[str, Any]:
        try:
            subprocess.run(f"shutdown /r /t {delay}", shell=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def cancel_shutdown() -> dict[str, Any]:
        try:
            subprocess.run("shutdown /a", shell=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def system_info() -> dict[str, Any]:
        info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "machine": platform.machine(),
            "hostname": platform.node(),
        }
        try:
            import psutil
            info["cpu_percent"] = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            info["memory_total_gb"] = round(mem.total / (1024**3), 1)
            info["memory_used_percent"] = mem.percent
            disk = psutil.disk_usage("/")
            info["disk_total_gb"] = round(disk.total / (1024**3), 1)
            info["disk_used_percent"] = round(disk.percent, 1)
        except ImportError:
            pass
        return info

    @staticmethod
    def open_url(url: str) -> dict[str, Any]:
        try:
            import webbrowser
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
