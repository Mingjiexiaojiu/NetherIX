"""Settings dialog for configuring NIX."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


_DARK_STYLE = """
    QDialog { background: #1a1030; color: #e0d0f0; }
    QTabWidget::pane { border: 1px solid #5a3d7a; background: #1a1030; }
    QTabBar::tab { background: #2b2040; color: #e0d0f0; padding: 8px 16px; border: 1px solid #5a3d7a; }
    QTabBar::tab:selected { background: #5a3d7a; }
    QLineEdit, QSpinBox, QComboBox {
        background: #2b2040; color: #e0d0f0; border: 1px solid #5a3d7a;
        border-radius: 4px; padding: 4px 8px;
    }
    QSlider::groove:horizontal { background: #2b2040; height: 6px; border-radius: 3px; }
    QSlider::handle:horizontal { background: #7a5d9a; width: 14px; margin: -4px 0; border-radius: 7px; }
    QPushButton {
        background: #5a3d7a; color: #e0d0f0; border: none;
        border-radius: 6px; padding: 8px 20px;
    }
    QPushButton:hover { background: #7a5d9a; }
    QLabel { color: #c0b0d0; }
"""


class SettingsDialog(QDialog):
    """Dark-themed settings dialog with tabs."""

    settings_saved = Signal(dict)

    def __init__(self, config: dict[str, Any], parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("NIX 设置")
        self.setFixedSize(480, 420)
        self.setStyleSheet(_DARK_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("⚙ NIX 设置")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._create_ai_tab(), "AI 模型")
        tabs.addTab(self._create_pet_tab(), "宠物行为")
        tabs.addTab(self._create_ui_tab(), "界面")
        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _create_ai_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        ai = self._config.get("ai", {})

        self._api_key = QLineEdit(ai.get("api_key", ""))
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Key:", self._api_key)

        self._base_url = QLineEdit(ai.get("base_url", ""))
        form.addRow("Base URL:", self._base_url)

        self._model = QComboBox()
        self._model.setEditable(True)
        self._model.addItems(["qwen-plus", "qwen-turbo", "gpt-4o-mini", "gpt-4o", "deepseek-chat"])
        self._model.setCurrentText(ai.get("model", "qwen-plus"))
        form.addRow("模型:", self._model)

        self._temperature = QSlider(Qt.Orientation.Horizontal)
        self._temperature.setRange(0, 100)
        self._temperature.setValue(int(ai.get("temperature", 0.7) * 100))
        form.addRow("温度:", self._temperature)

        return w

    def _create_pet_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        pet = self._config.get("pet", {})

        self._walk_speed = QSpinBox()
        self._walk_speed.setRange(1, 10)
        self._walk_speed.setValue(pet.get("walk_speed", 2))
        form.addRow("行走速度:", self._walk_speed)

        self._pet_size = QSpinBox()
        self._pet_size.setRange(64, 256)
        self._pet_size.setSingleStep(16)
        self._pet_size.setValue(pet.get("size", 128))
        form.addRow("精灵大小:", self._pet_size)

        self._fps = QSpinBox()
        self._fps.setRange(5, 30)
        self._fps.setValue(pet.get("fps", 10))
        form.addRow("动画帧率:", self._fps)

        return w

    def _create_ui_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        ui = self._config.get("ui", {})

        self._hotkey = QLineEdit(ui.get("hotkey", "ctrl+space"))
        form.addRow("唤醒快捷键:", self._hotkey)

        self._bubble_duration = QSpinBox()
        self._bubble_duration.setRange(1, 30)
        self._bubble_duration.setValue(ui.get("bubble_duration", 5))
        self._bubble_duration.setSuffix(" 秒")
        form.addRow("气泡显示时长:", self._bubble_duration)

        return w

    def _save(self):
        updated = {
            "ai": {
                "api_key": self._api_key.text(),
                "base_url": self._base_url.text(),
                "model": self._model.currentText(),
                "temperature": self._temperature.value() / 100.0,
            },
            "pet": {
                "walk_speed": self._walk_speed.value(),
                "size": self._pet_size.value(),
                "fps": self._fps.value(),
            },
            "ui": {
                "hotkey": self._hotkey.text(),
                "bubble_duration": self._bubble_duration.value(),
            },
        }
        self.settings_saved.emit(updated)
        self.accept()
