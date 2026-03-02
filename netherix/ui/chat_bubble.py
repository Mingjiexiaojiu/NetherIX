"""Floating chat bubble that appears above the pet sprite."""

from PySide6.QtCore import QPropertyAnimation, QTimer, Qt, QEasingCurve, QPoint, Property
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect


class ChatBubble(QWidget):
    """Semi-transparent speech bubble positioned relative to the pet."""

    def __init__(self, parent=None, duration: int = 5000):
        super().__init__(parent)
        self._duration = duration
        self._text = ""
        self._padding = 12
        self._max_width = 280
        self._bg_color = QColor(43, 32, 64, 230)
        self._text_color = QColor(224, 208, 240)
        self._border_color = QColor(90, 61, 122)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(500)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self._fade_anim.finished.connect(self.hide)

        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.fade_out)

        self.hide()

    def show_message(self, text: str, anchor: QPoint, duration: int | None = None):
        self._auto_hide_timer.stop()
        self._fade_anim.stop()
        self._opacity_effect.setOpacity(1.0)
        self._text = text

        font = QFont("Microsoft YaHei", 10)
        from PySide6.QtGui import QFontMetrics
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(
            0, 0, self._max_width - self._padding * 2, 9999,
            Qt.TextFlag.TextWordWrap, text,
        )
        w = text_rect.width() + self._padding * 2 + 4
        h = text_rect.height() + self._padding * 2 + 16  # +16 for tail

        self.setFixedSize(w, h)
        self.move(anchor.x() - w // 2, anchor.y() - h - 4)
        self.show()
        self.update()

        d = duration if duration is not None else self._duration
        if d > 0:
            self._auto_hide_timer.start(d)

    def fade_out(self):
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        tail_h = 12
        body_h = h - tail_h

        path = QPainterPath()
        radius = 10
        path.addRoundedRect(0, 0, w, body_h, radius, radius)

        # Small triangle tail pointing down-center
        tail_x = w / 2
        path.moveTo(tail_x - 8, body_h)
        path.lineTo(tail_x, h)
        path.lineTo(tail_x + 8, body_h)

        p.setPen(self._border_color)
        p.setBrush(self._bg_color)
        p.drawPath(path)

        p.setPen(self._text_color)
        font = QFont("Microsoft YaHei", 10)
        p.setFont(font)
        text_rect = p.boundingRect(
            self._padding, self._padding,
            w - self._padding * 2, body_h - self._padding * 2,
            Qt.TextFlag.TextWordWrap, self._text,
        )
        p.drawText(text_rect, Qt.TextFlag.TextWordWrap, self._text)
        p.end()
