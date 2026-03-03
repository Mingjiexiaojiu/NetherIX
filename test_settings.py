"""Quick preview of the settings dialog without launching the full app."""

import sys
import yaml
from pathlib import Path
from PySide6.QtWidgets import QApplication

from netherix.ui.settings_dialog import SettingsDialog

config_path = Path(__file__).parent / "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

app = QApplication(sys.argv)
dialog = SettingsDialog(config)
dialog.settings_saved.connect(lambda d: print("Saved:", d))
dialog.exec()
