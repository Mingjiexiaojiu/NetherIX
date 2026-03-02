"""Floating input box triggered by global hotkey, similar to Spotlight/uTools."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FloatingInputBox(QWidget):
    """A centered floating input box for talking to NIX."""

    message_submitted = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 56)

        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            #container {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2b2040, stop:1 #1a1030);
                border: 1px solid #5a3d7a;
                border-radius: 12px;
            }
        """)
        container.setGeometry(0, 0, 520, 56)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.GlobalColor.black)
        container.setGraphicsEffect(shadow)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 8, 8, 8)
        layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("对 NIX 说些什么...")
        self._input.setFont(QFont("Microsoft YaHei", 12))
        self._input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #e0d0f0;
                selection-background-color: #5a3d7a;
            }
        """)
        self._input.returnPressed.connect(self._submit)

        self._send_btn = QPushButton("⏎")
        self._send_btn.setFixedSize(36, 36)
        self._send_btn.setFont(QFont("Segoe UI Symbol", 14))
        self._send_btn.setStyleSheet("""
            QPushButton {
                background: #5a3d7a;
                color: #e0d0f0;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background: #7a5d9a; }
            QPushButton:pressed { background: #4a2d6a; }
        """)
        self._send_btn.clicked.connect(self._submit)

        layout.addWidget(self._input)
        layout.addWidget(self._send_btn)

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_centered()

    def show_centered(self):
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + geo.height() // 3
            self.move(x, y)
        self._input.clear()
        self.show()
        self.activateWindow()
        self._input.setFocus()

    def _submit(self):
        text = self._input.text().strip()
        if text:
            self.message_submitted.emit(text)
            self._input.clear()
            self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
