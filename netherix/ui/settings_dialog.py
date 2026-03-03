"""Full-featured settings dialog with sidebar navigation."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QIcon, QPixmap, QBrush
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


def _icon_circle(color: QColor, size: int = 24) -> QIcon:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, size - 4, size - 4)
    p.end()
    return QIcon(px)


_STYLE = """
QDialog {
    background: #12091f;
    color: #e0d0f0;
}
QListWidget {
    background: #1a0f2e;
    border: none;
    border-right: 1px solid #2d1f4e;
    color: #c0b0d0;
    font-size: 13px;
    outline: none;
}
QListWidget::item {
    padding: 12px 18px;
    border-radius: 0;
}
QListWidget::item:selected {
    background: #2d1f4e;
    color: #e8d8ff;
    border-left: 3px solid #9b6dff;
}
QListWidget::item:hover:!selected {
    background: #221638;
}
QStackedWidget {
    background: #12091f;
}
QGroupBox {
    font-size: 13px;
    font-weight: bold;
    color: #b8a0e0;
    border: 1px solid #2d1f4e;
    border-radius: 8px;
    margin-top: 16px;
    padding: 20px 14px 14px 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}
QLineEdit, QSpinBox, QComboBox, QPlainTextEdit {
    background: #1a0f2e;
    color: #e0d0f0;
    border: 1px solid #3a2860;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #5a3d8a;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {
    border: 1px solid #9b6dff;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #1a0f2e;
    color: #e0d0f0;
    border: 1px solid #3a2860;
    selection-background-color: #5a3d8a;
}
QSlider::groove:horizontal {
    background: #2d1f4e;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #9b6dff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #6b4daf;
    border-radius: 3px;
}
QCheckBox {
    color: #c0b0d0;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #3a2860;
    background: #1a0f2e;
}
QCheckBox::indicator:checked {
    background: #9b6dff;
    border: 1px solid #9b6dff;
}
QPushButton {
    background: #9b6dff;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 28px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover {
    background: #b48aff;
}
QPushButton:pressed {
    background: #7b50df;
}
QPushButton#cancelBtn {
    background: #2d1f4e;
    color: #c0b0d0;
}
QPushButton#cancelBtn:hover {
    background: #3a2860;
}
QLabel {
    color: #a090c0;
}
QLabel#sectionTitle {
    color: #e8d8ff;
    font-size: 18px;
    font-weight: bold;
}
QLabel#sectionDesc {
    color: #7a6a9a;
    font-size: 12px;
}
QLabel#aboutTitle {
    color: #e8d8ff;
    font-size: 22px;
    font-weight: bold;
}
QLabel#aboutVersion {
    color: #9b6dff;
    font-size: 14px;
}
QScrollArea {
    border: none;
    background: transparent;
}
"""

_SECTIONS = [
    ("AI 模型", "配置大语言模型连接"),
    ("宠物行为", "精灵外观与动作偏好"),
    ("界面交互", "快捷键和气泡设置"),
    ("语音", "TTS 语音合成设置"),
    ("技能管理", "启用或禁用内置技能"),
    ("关于", "关于冥九灵"),
]

_ALL_BUILTIN_SKILLS = {
    "calculator": "计算器 — 数学表达式求值",
    "translator": "翻译 — 多语言互译",
    "web_search": "网页搜索 — 浏览器搜索",
    "reminder": "提醒 — 定时提醒/闹钟",
    "weather": "天气 — 城市天气查询",
    "file_organizer": "文件整理 — 按类型归类文件",
}


class SettingsDialog(QDialog):
    """Modern dark-themed settings with sidebar navigation."""

    settings_saved = Signal(dict)

    def __init__(self, config: dict[str, Any], parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("NIX 设置")
        self.setMinimumSize(720, 520)
        self.resize(740, 540)
        self.setStyleSheet(_STYLE)
        self._skill_checks: dict[str, QCheckBox] = {}
        self._setup_ui()

    # ── Layout ──

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._nav = QListWidget()
        self._nav.setFixedWidth(160)
        self._nav.setIconSize(QSize(18, 18))
        colors = [
            QColor("#9b6dff"), QColor("#6dcfff"), QColor("#ff9b6d"),
            QColor("#6dff9b"), QColor("#ff6d9b"), QColor("#b8a0e0"),
        ]
        for i, (label, _) in enumerate(_SECTIONS):
            item = QListWidgetItem(_icon_circle(colors[i % len(colors)]), label)
            item.setSizeHint(QSize(160, 44))
            self._nav.addItem(item)
        self._nav.setCurrentRow(0)
        self._nav.currentRowChanged.connect(self._on_nav_changed)
        root.addWidget(self._nav)

        right = QVBoxLayout()
        right.setContentsMargins(24, 20, 24, 16)
        right.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_ai())
        self._stack.addWidget(self._page_pet())
        self._stack.addWidget(self._page_ui())
        self._stack.addWidget(self._page_voice())
        self._stack.addWidget(self._page_skills())
        self._stack.addWidget(self._page_about())
        right.addWidget(self._stack, 1)

        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 16, 0, 0)
        btn_bar.addStretch()
        cancel = QPushButton("取消")
        cancel.setObjectName("cancelBtn")
        cancel.clicked.connect(self.reject)
        save = QPushButton("保存设置")
        save.clicked.connect(self._save)
        btn_bar.addWidget(cancel)
        btn_bar.addSpacing(10)
        btn_bar.addWidget(save)
        right.addLayout(btn_bar)

        root.addLayout(right, 1)

    def _on_nav_changed(self, index: int):
        self._stack.setCurrentIndex(index)

    @staticmethod
    def _section_header(title: str, desc: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 12)
        lay.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("sectionTitle")
        d = QLabel(desc)
        d.setObjectName("sectionDesc")
        lay.addWidget(t)
        lay.addWidget(d)
        return w

    @staticmethod
    def _scrollable(inner: QWidget) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(inner)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return sa

    # ── Page: AI ──

    def _page_ai(self) -> QWidget:
        ai = self._config.get("ai", {})

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._section_header("AI 模型", "配置大语言模型的 API 连接和参数"))

        g = QGroupBox("API 连接")
        form = QFormLayout(g)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._api_key = QLineEdit(ai.get("api_key", ""))
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setPlaceholderText("sk-...")
        form.addRow("API Key:", self._api_key)

        self._base_url = QLineEdit(ai.get("base_url", ""))
        self._base_url.setPlaceholderText("https://api.openai.com/v1")
        form.addRow("Base URL:", self._base_url)

        self._model = QComboBox()
        self._model.setEditable(True)
        self._model.addItems([
            "qwen-plus", "qwen-turbo", "qwen-max",
            "gpt-4o-mini", "gpt-4o",
            "deepseek-chat", "deepseek-reasoner",
        ])
        self._model.setCurrentText(ai.get("model", "qwen-plus"))
        form.addRow("模型:", self._model)

        lay.addWidget(g)

        g2 = QGroupBox("生成参数")
        form2 = QFormLayout(g2)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        temp_row = QHBoxLayout()
        self._temperature = QSlider(Qt.Orientation.Horizontal)
        self._temperature.setRange(0, 100)
        self._temperature.setValue(int(ai.get("temperature", 0.7) * 100))
        self._temp_label = QLabel(f"{ai.get('temperature', 0.7):.2f}")
        self._temp_label.setFixedWidth(40)
        self._temperature.valueChanged.connect(
            lambda v: self._temp_label.setText(f"{v / 100:.2f}")
        )
        temp_row.addWidget(self._temperature)
        temp_row.addWidget(self._temp_label)
        form2.addRow("温度:", temp_row)

        self._max_tokens = QSpinBox()
        self._max_tokens.setRange(256, 32768)
        self._max_tokens.setSingleStep(256)
        self._max_tokens.setValue(ai.get("max_tokens", 2048))
        form2.addRow("最大 Tokens:", self._max_tokens)

        lay.addWidget(g2)

        g3 = QGroupBox("系统提示词")
        g3_lay = QVBoxLayout(g3)
        self._system_prompt = QPlainTextEdit(ai.get("system_prompt", ""))
        self._system_prompt.setFixedHeight(90)
        self._system_prompt.setPlaceholderText("设定 NIX 的性格和行为方式...")
        g3_lay.addWidget(self._system_prompt)
        lay.addWidget(g3)

        lay.addStretch()
        return self._scrollable(page)

    # ── Page: Pet ──

    def _page_pet(self) -> QWidget:
        pet = self._config.get("pet", {})

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._section_header("宠物行为", "调整精灵外观尺寸和行为偏好"))

        g = QGroupBox("外观")
        form = QFormLayout(g)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._pet_size = QSpinBox()
        self._pet_size.setRange(64, 256)
        self._pet_size.setSingleStep(16)
        self._pet_size.setValue(pet.get("size", 128))
        self._pet_size.setSuffix(" px")
        form.addRow("精灵大小:", self._pet_size)

        self._fps = QSpinBox()
        self._fps.setRange(5, 30)
        self._fps.setValue(pet.get("fps", 10))
        self._fps.setSuffix(" FPS")
        form.addRow("动画帧率:", self._fps)

        lay.addWidget(g)

        g2 = QGroupBox("行为")
        form2 = QFormLayout(g2)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._walk_speed = QSpinBox()
        self._walk_speed.setRange(1, 10)
        self._walk_speed.setValue(pet.get("walk_speed", 2))
        self._walk_speed.setSuffix(" px/帧")
        form2.addRow("行走速度:", self._walk_speed)

        self._auto_walk = QCheckBox("启用自主行走")
        self._auto_walk.setChecked(pet.get("auto_walk", True))
        form2.addRow("", self._auto_walk)

        self._gravity = QCheckBox("启用重力（掉落到屏幕底部）")
        self._gravity.setChecked(pet.get("gravity", True))
        form2.addRow("", self._gravity)

        self._idle_timeout = QSpinBox()
        self._idle_timeout.setRange(5, 600)
        self._idle_timeout.setValue(pet.get("idle_timeout", 30))
        self._idle_timeout.setSuffix(" 秒")
        form2.addRow("闲置→坐下:", self._idle_timeout)

        self._sleep_timeout = QSpinBox()
        self._sleep_timeout.setRange(30, 3600)
        self._sleep_timeout.setSingleStep(30)
        self._sleep_timeout.setValue(pet.get("sleep_timeout", 300))
        self._sleep_timeout.setSuffix(" 秒")
        form2.addRow("闲置→睡觉:", self._sleep_timeout)

        lay.addWidget(g2)
        lay.addStretch()
        return self._scrollable(page)

    # ── Page: UI ──

    def _page_ui(self) -> QWidget:
        ui = self._config.get("ui", {})

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._section_header("界面交互", "快捷键、对话气泡和主题设置"))

        g = QGroupBox("快捷键")
        form = QFormLayout(g)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._hotkey = QLineEdit(ui.get("hotkey", "ctrl+space"))
        self._hotkey.setPlaceholderText("例如: ctrl+space")
        form.addRow("唤醒 NIX:", self._hotkey)

        lay.addWidget(g)

        g2 = QGroupBox("对话气泡")
        form2 = QFormLayout(g2)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._bubble_duration = QSpinBox()
        self._bubble_duration.setRange(1, 30)
        self._bubble_duration.setValue(ui.get("bubble_duration", 5))
        self._bubble_duration.setSuffix(" 秒")
        form2.addRow("显示时长:", self._bubble_duration)

        lay.addWidget(g2)

        g3 = QGroupBox("主题")
        form3 = QFormLayout(g3)
        form3.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._theme = QComboBox()
        self._theme.addItems(["dark", "light"])
        self._theme.setCurrentText(ui.get("theme", "dark"))
        form3.addRow("主题风格:", self._theme)

        lay.addWidget(g3)
        lay.addStretch()
        return self._scrollable(page)

    # ── Page: Voice ──

    def _page_voice(self) -> QWidget:
        voice = self._config.get("voice", {})

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._section_header("语音", "文字转语音（TTS）设置"))

        g = QGroupBox("TTS 语音合成")
        form = QFormLayout(g)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._tts_enabled = QCheckBox("启用语音播报（NIX 说话时朗读）")
        self._tts_enabled.setChecked(voice.get("tts_enabled", False))
        form.addRow("", self._tts_enabled)

        self._tts_voice = QComboBox()
        voices = [
            ("zh-CN-XiaoyiNeural", "晓艺 (女声·活泼)"),
            ("zh-CN-XiaoxiaoNeural", "晓晓 (女声·温柔)"),
            ("zh-CN-YunxiNeural", "云希 (男声·温暖)"),
            ("zh-CN-YunjianNeural", "云健 (男声·沉稳)"),
            ("en-US-JennyNeural", "Jenny (English·Female)"),
            ("en-US-GuyNeural", "Guy (English·Male)"),
            ("ja-JP-NanamiNeural", "Nanami (日本語·女性)"),
        ]
        for voice_id, display in voices:
            self._tts_voice.addItem(display, voice_id)
        current_voice = voice.get("tts_voice", "zh-CN-XiaoyiNeural")
        idx = self._tts_voice.findData(current_voice)
        if idx >= 0:
            self._tts_voice.setCurrentIndex(idx)
        form.addRow("语音角色:", self._tts_voice)

        lay.addWidget(g)

        note = QLabel(
            "需要安装 edge-tts: pip install edge-tts\n"
            "语音通过微软 Edge TTS 在线合成，需要网络连接。"
        )
        note.setStyleSheet("color: #5a4a7a; font-size: 11px; padding: 8px;")
        note.setWordWrap(True)
        lay.addWidget(note)

        lay.addStretch()
        return self._scrollable(page)

    # ── Page: Skills ──

    def _page_skills(self) -> QWidget:
        enabled = self._config.get("skills", {}).get("enabled_builtin", [])

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._section_header("技能管理", "启用或禁用 NIX 的内置技能"))

        g = QGroupBox("内置技能")
        g_lay = QVBoxLayout(g)
        g_lay.setSpacing(10)
        for skill_id, desc in _ALL_BUILTIN_SKILLS.items():
            cb = QCheckBox(desc)
            cb.setChecked(skill_id in enabled)
            self._skill_checks[skill_id] = cb
            g_lay.addWidget(cb)
        lay.addWidget(g)

        g2 = QGroupBox("自定义技能")
        g2_lay = QVBoxLayout(g2)
        self._custom_dir = QLineEdit(
            self._config.get("skills", {}).get("custom_dir", "skills")
        )
        self._custom_dir.setPlaceholderText("skills")
        lbl = QLabel("自定义技能目录:")
        lbl.setStyleSheet("color: #a090c0;")
        g2_lay.addWidget(lbl)
        g2_lay.addWidget(self._custom_dir)
        note = QLabel("在该目录中放置 .py 文件，继承 BaseSkill 即可自动加载。")
        note.setStyleSheet("color: #5a4a7a; font-size: 11px;")
        note.setWordWrap(True)
        g2_lay.addWidget(note)
        lay.addWidget(g2)

        lay.addStretch()
        return self._scrollable(page)

    # ── Page: About ──

    def _page_about(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addSpacing(20)

        # Ghost icon placeholder
        icon_label = QLabel()
        icon_px = QPixmap(80, 80)
        icon_px.fill(Qt.GlobalColor.transparent)
        p = QPainter(icon_px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(155, 109, 255)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(4, 4, 72, 72)
        p.setPen(QColor(255, 255, 255))
        font = p.font()
        font.setPixelSize(28)
        font.setBold(True)
        p.setFont(font)
        p.drawText(icon_px.rect(), Qt.AlignmentFlag.AlignCenter, "NIX")
        p.end()
        icon_label.setPixmap(icon_px)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon_label)

        lay.addSpacing(8)

        title = QLabel("NetherIX")
        title.setObjectName("aboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        from netherix import __version__
        ver = QLabel(f"v{__version__}")
        ver.setObjectName("aboutVersion")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ver)

        lay.addSpacing(16)

        desc = QLabel(
            "冥九灵 — 来自冥界第九层的桌面智能宠物\n\n"
            "Nether → 冥界之幽深\n"
            "IX → 罗马数字 9，复古而神秘\n"
            "NIX → Logo 缩写，亦是北欧水域精灵之名\n\n"
            "沉默、神秘，却始终陪伴。"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #8070a0; font-size: 12px; line-height: 1.6;")
        desc.setWordWrap(True)
        lay.addWidget(desc)

        lay.addSpacing(20)

        links = QLabel(
            '<a style="color: #9b6dff;" '
            'href="https://github.com/Mingjiexiaojiu/NetherIX">'
            "GitHub</a>"
        )
        links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        links.setOpenExternalLinks(True)
        lay.addWidget(links)

        lay.addStretch()
        return page

    # ── Save ──

    def _save(self):
        updated = {
            "ai": {
                "api_key": self._api_key.text(),
                "base_url": self._base_url.text(),
                "model": self._model.currentText(),
                "temperature": self._temperature.value() / 100.0,
                "max_tokens": self._max_tokens.value(),
                "system_prompt": self._system_prompt.toPlainText(),
            },
            "pet": {
                "size": self._pet_size.value(),
                "fps": self._fps.value(),
                "walk_speed": self._walk_speed.value(),
                "auto_walk": self._auto_walk.isChecked(),
                "gravity": self._gravity.isChecked(),
                "idle_timeout": self._idle_timeout.value(),
                "sleep_timeout": self._sleep_timeout.value(),
            },
            "ui": {
                "hotkey": self._hotkey.text(),
                "bubble_duration": self._bubble_duration.value(),
                "theme": self._theme.currentText(),
            },
            "voice": {
                "tts_enabled": self._tts_enabled.isChecked(),
                "tts_voice": self._tts_voice.currentData() or "zh-CN-XiaoyiNeural",
            },
            "skills": {
                "custom_dir": self._custom_dir.text(),
                "enabled_builtin": [
                    k for k, cb in self._skill_checks.items() if cb.isChecked()
                ],
            },
        }
        self.settings_saved.emit(updated)
        self.accept()
