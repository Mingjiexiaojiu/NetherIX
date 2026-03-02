"""NetherIX (冥九灵) - Desktop Intelligent Pet
Entry point for the application.
"""

import sys
from pathlib import Path

import yaml
from loguru import logger
from PySide6.QtWidgets import QApplication

from netherix.app import NetherIXApp

_ROOT = Path(__file__).resolve().parent


def load_config() -> dict:
    config_path = _ROOT / "config.yaml"
    if not config_path.exists():
        logger.warning("config.yaml not found, using defaults")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")

    config = load_config()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("NetherIX")
    app.setApplicationDisplayName("冥九灵")

    nix = NetherIXApp(config)
    nix.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
