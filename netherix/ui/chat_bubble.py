"""Chat bubble that floats above the pet: shows replies and accepts input."""

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QKeyEvent,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_BG_START = QColor(38, 28, 58, 240)
_BG_END = QColor(26, 18, 42, 245)
_BORDER = QColor(110, 75, 160, 180)
_ACCENT = QColor(140, 100, 200)
_TEXT = QColor(224, 210, 245)
_SUBTLE = QColor(160, 140, 190)
_INPUT_BG = QColor(50, 38, 75, 200)

_BUBBLE_W = 340
_TAIL_H = 30
_CLOUD_PAD = 26
_FONT = "Microsoft YaHei"


class ChatBubble(QWidget):
    """Integrated Q&A bubble: shows AI replies above the pet with an input bar."""

    message_submitted = Signal(str)

    def __init__(self, parent=None, duration: int = 8000):
        super().__init__(parent)
        self._duration = duration
        self._anchor = QPoint(0, 0)
        self._input_mode = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._opacity_fx = QGraphicsOpacityEffect(self)
        self._opacity_fx.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_fx)

        self._fade_anim = QPropertyAnimation(self._opacity_fx, b"opacity")
        self._fade_anim.setDuration(400)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self._fade_anim.finished.connect(self._on_fade_done)

        self._auto_hide = QTimer(self)
        self._auto_hide.setSingleShot(True)
        self._auto_hide.timeout.connect(self._begin_fade)

        self._build_ui()
        self.hide()

    # ── UI construction ──

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(
            _CLOUD_PAD + 14, _CLOUD_PAD + 10,
            _CLOUD_PAD + 14, _TAIL_H + _CLOUD_PAD + 4,
        )
        root.setSpacing(8)

        self._reply_label = QLabel()
        self._reply_label.setWordWrap(True)
        self._reply_label.setFont(QFont(_FONT, 10))
        self._reply_label.setStyleSheet(f"color: {_TEXT.name()}; background: transparent;")
        self._reply_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._reply_label.setMinimumWidth(_BUBBLE_W - 40)
        self._reply_label.setMaximumWidth(_BUBBLE_W - 40)
        root.addWidget(self._reply_label)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {_BORDER.name()};")
        self._sep = sep
        root.addWidget(sep)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText("对 NIX 说些什么…")
        self._input.setFont(QFont(_FONT, 9))
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {_INPUT_BG.name()};
                border: 1px solid {_BORDER.name()};
                border-radius: 8px;
                color: {_TEXT.name()};
                padding: 5px 10px;
                selection-background-color: {_ACCENT.name()};
            }}
            QLineEdit:focus {{
                border-color: {_ACCENT.name()};
            }}
        """)
        self._input.returnPressed.connect(self._submit)

        self._send_btn = QPushButton("➤")
        self._send_btn.setFixedSize(30, 30)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.setFont(QFont("Segoe UI Symbol", 11))
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_ACCENT.name()};
                color: white;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background: {_ACCENT.lighter(120).name()}; }}
            QPushButton:pressed {{ background: {_ACCENT.darker(120).name()}; }}
        """)
        self._send_btn.clicked.connect(self._submit)

        row.addWidget(self._input, 1)
        row.addWidget(self._send_btn)
        self._input_row = QWidget()
        self._input_row.setLayout(row)
        root.addWidget(self._input_row)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)

        self._opacity_fx = QGraphicsOpacityEffect(self)
        self._opacity_fx.setOpacity(1.0)

    # ── Public API ──

    def show_message(self, text: str, anchor: QPoint, duration: int | None = None):
        """Show a reply from NIX above the pet, keep input bar visible."""
        self._auto_hide.stop()
        self._fade_anim.stop()
        self._opacity_fx.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_fx)

        self._reply_label.setText(text)
        self._reply_label.show()
        self._sep.show()
        self._input_row.show()

        self._reflow(anchor)
        self.show()
        self.raise_()

        d = duration if duration is not None else self._duration
        if d > 0 and not self._input_mode:
            self._auto_hide.start(d)

    def show_input(self, anchor: QPoint):
        """Open the bubble in input mode (no reply text yet)."""
        self._auto_hide.stop()
        self._fade_anim.stop()
        self._opacity_fx.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_fx)

        self._input_mode = True
        self._reply_label.setText("")
        self._reply_label.hide()
        self._sep.hide()
        self._input_row.show()

        self._reflow(anchor)
        self.show()
        self.raise_()
        self.activateWindow()
        self._input.setFocus()
        self._input.clear()

    def follow(self, anchor: QPoint):
        """Reposition the bubble to track the pet without rebuilding."""
        if self.isVisible():
            self._anchor = anchor
            x = anchor.x() - self.width() // 2
            y = anchor.y() - self.height() - 4
            self.move(x, y)

    def toggle_input(self, anchor: QPoint):
        if self.isVisible() and self._input_mode:
            self.hide()
            self._input_mode = False
        else:
            self.show_input(anchor)

    # ── Painting ──

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        body_h = h - _TAIL_H

        grad = QLinearGradient(0, 0, 0, body_h)
        grad.setColorAt(0, _BG_START)
        grad.setColorAt(1, _BG_END)

        cloud = self._cloud_path(w, body_h)
        p.setPen(QPen(_BORDER, 1.4))
        p.setBrush(grad)
        p.drawPath(cloud)

        cx = w / 2
        p.setPen(QPen(_BORDER, 1.0))
        p.setBrush(_BG_END)
        p.drawEllipse(int(cx - 5), int(body_h + 3), 10, 9)
        p.drawEllipse(int(cx + 1), int(body_h + 14), 7, 6)
        p.drawEllipse(int(cx - 2), int(body_h + 22), 5, 5)

        p.end()

    @staticmethod
    def _cloud_path(w: float, h: float) -> QPainterPath:
        """Hand-drawn cloud outline using quadratic bezier curves.

        All points stay within [safe, w-safe] x [safe, h-safe].
        """
        pad = _CLOUD_PAD
        safe = 3
        bump = pad - safe

        bx, by = pad, pad
        bw, bh = w - pad * 2, h - pad * 2

        path = QPainterPath()

        # Start at left edge, 70 % down
        path.moveTo(bx, by + bh * 0.7)

        # ── Left edge ↑  (2 bumps) ──
        path.quadTo(bx - bump, by + bh * 0.55, bx, by + bh * 0.4)
        path.quadTo(bx - bump, by + bh * 0.18, bx + bw * 0.06, by)

        # ── Top edge →  (3 bumps) ──
        path.quadTo(bx + bw * 0.18, by - bump, bx + bw * 0.33, by)
        path.quadTo(bx + bw * 0.50, by - bump, bx + bw * 0.67, by)
        path.quadTo(bx + bw * 0.82, by - bump, bx + bw * 0.94, by)

        # ── Right edge ↓  (2 bumps) ──
        path.quadTo(bx + bw + bump, by + bh * 0.18, bx + bw, by + bh * 0.4)
        path.quadTo(bx + bw + bump, by + bh * 0.55, bx + bw, by + bh * 0.7)

        # ── Bottom edge ←  (3 bumps) ──
        path.quadTo(bx + bw * 0.82, by + bh + bump, bx + bw * 0.67, by + bh)
        path.quadTo(bx + bw * 0.50, by + bh + bump, bx + bw * 0.33, by + bh)
        path.quadTo(bx + bw * 0.18, by + bh + bump, bx, by + bh * 0.7)

        path.closeSubpath()
        return path

    # ── Internals ──

    def _reflow(self, anchor: QPoint):
        self._anchor = anchor
        self.adjustSize()
        w = max(self.sizeHint().width(), _BUBBLE_W)
        h = self.sizeHint().height() + _TAIL_H
        self.setFixedSize(w, h)
        x = anchor.x() - w // 2
        y = anchor.y() - h - 4

        screen = None
        from PySide6.QtWidgets import QApplication
        s = QApplication.primaryScreen()
        if s:
            screen = s.availableGeometry()
        if screen:
            if x < screen.left():
                x = screen.left()
            if x + w > screen.right():
                x = screen.right() - w
            if y < screen.top():
                y = anchor.y() + 40

        self.move(x, y)

    def _submit(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._input_mode = False
        self._reply_label.setText("让我想想…")
        self._reply_label.show()
        self._sep.show()
        self.adjustSize()
        self._reflow(self._anchor)
        self.message_submitted.emit(text)

    def _begin_fade(self):
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setTargetObject(self._opacity_fx)
        self._fade_anim.start()

    def _on_fade_done(self):
        if not self._input_mode:
            self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self._input_mode = False
            self.hide()
        else:
            super().keyPressEvent(event)
