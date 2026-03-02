"""Mouse and keyboard automation via pyautogui."""

from __future__ import annotations

import time

import pyautogui
import pyperclip
from loguru import logger

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class MouseKeyboardController:
    """High-level API for mouse and keyboard operations."""

    # --- Mouse ---

    @staticmethod
    def click(x: int, y: int, button: str = "left", clicks: int = 1):
        logger.info("Click ({},{}) button={} clicks={}", x, y, button, clicks)
        pyautogui.click(x, y, button=button, clicks=clicks)

    @staticmethod
    def double_click(x: int, y: int):
        pyautogui.doubleClick(x, y)

    @staticmethod
    def right_click(x: int, y: int):
        pyautogui.rightClick(x, y)

    @staticmethod
    def move_to(x: int, y: int, duration: float = 0.3):
        pyautogui.moveTo(x, y, duration=duration)

    @staticmethod
    def drag_to(x: int, y: int, duration: float = 0.5, button: str = "left"):
        pyautogui.dragTo(x, y, duration=duration, button=button)

    @staticmethod
    def scroll(clicks: int, x: int | None = None, y: int | None = None):
        pyautogui.scroll(clicks, x, y)

    @staticmethod
    def get_position() -> tuple[int, int]:
        pos = pyautogui.position()
        return pos.x, pos.y

    # --- Keyboard ---

    @staticmethod
    def type_text(text: str, interval: float = 0.02):
        """Type text using clipboard to support CJK characters."""
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)

    @staticmethod
    def press_key(key: str):
        logger.info("Press key: {}", key)
        pyautogui.press(key)

    @staticmethod
    def hotkey(*keys: str):
        logger.info("Hotkey: {}", "+".join(keys))
        pyautogui.hotkey(*keys)

    @staticmethod
    def key_down(key: str):
        pyautogui.keyDown(key)

    @staticmethod
    def key_up(key: str):
        pyautogui.keyUp(key)

    # --- Screen ---

    @staticmethod
    def screenshot(region: tuple[int, int, int, int] | None = None) -> str:
        """Take a screenshot and save to temp file. Returns file path."""
        import tempfile
        import os
        path = os.path.join(tempfile.gettempdir(), "nix_screenshot.png")
        img = pyautogui.screenshot(region=region)
        img.save(path)
        logger.info("Screenshot saved to {}", path)
        return path

    @staticmethod
    def screen_size() -> tuple[int, int]:
        size = pyautogui.size()
        return size.width, size.height
