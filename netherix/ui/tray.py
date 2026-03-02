"""System tray icon with context menu."""

from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QBrush
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QApplication
from loguru import logger


def _generate_tray_icon() -> QIcon:
    """Generate a simple NIX icon if no icon file exists."""
    px = QPixmap(64, 64)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(140, 110, 200)))
    p.setPen(QColor(100, 70, 170))
    p.drawEllipse(8, 8, 48, 48)
    p.setPen(QColor(255, 255, 255))
    font = p.font()
    font.setPixelSize(22)
    font.setBold(True)
    p.setFont(font)
    p.drawText(px.rect(), 0x0084, "NIX")  # AlignCenter
    p.end()
    return QIcon(px)


class TrayManager(QObject):
    """Manages the system tray icon and its context menu."""

    show_input_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, icon_path: str | None = None):
        super().__init__()
        if icon_path:
            self._icon = QIcon(icon_path)
        else:
            self._icon = _generate_tray_icon()

        self._tray = QSystemTrayIcon(self._icon)
        self._tray.setToolTip("NetherIX · 冥九灵")
        self._tray.activated.connect(self._on_activated)

        self._menu = QMenu()
        self._menu.setStyleSheet(
            "QMenu { background: #2b2040; color: #e0d0f0; border: 1px solid #5a3d7a; }"
            "QMenu::item:selected { background: #5a3d7a; }"
        )

        self._menu.addAction("召唤 NIX (Ctrl+Space)", self.show_input_requested.emit)
        self._menu.addSeparator()
        self._menu.addAction("设置", self.settings_requested.emit)
        self._menu.addSeparator()
        self._menu.addAction("退出", self.quit_requested.emit)

        self._tray.setContextMenu(self._menu)

    def show(self):
        self._tray.show()
        logger.info("Tray icon shown")

    def hide(self):
        self._tray.hide()

    def show_message(self, title: str, message: str, duration: int = 3000):
        self._tray.showMessage(title, message, self._icon, duration)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_input_requested.emit()
