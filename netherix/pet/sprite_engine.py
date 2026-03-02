"""Sprite animation engine with state machine and placeholder generation."""

from enum import Enum
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from loguru import logger


class PetState(Enum):
    IDLE = "idle"
    WALK_LEFT = "walk_left"
    WALK_RIGHT = "walk_right"
    SIT = "sit"
    SLEEP = "sleep"
    TALK = "talk"
    ACTION = "action"
    DRAGGING = "dragging"


# Ghost body color palette
_BODY_COLOR = QColor(180, 160, 220)
_BODY_HIGHLIGHT = QColor(210, 195, 240)
_EYE_COLOR = QColor(40, 20, 60)
_CHEEK_COLOR = QColor(230, 170, 190, 100)

_FRAME_COUNT = 4


class SpriteEngine:
    """Manages sprite frames per state with automatic placeholder generation."""

    def __init__(self, assets_dir: str, size: int = 128):
        self._assets_dir = Path(assets_dir) / "sprites"
        self._size = size
        self._state = PetState.IDLE
        self._frames: dict[PetState, list[QPixmap]] = {}
        self._frame_index = 0
        self._load_all_sprites()

    def _load_all_sprites(self):
        for state in PetState:
            if state == PetState.DRAGGING:
                continue
            state_dir = self._assets_dir / state.value
            frames = self._load_frames_from_dir(state_dir)
            if not frames:
                frames = self._generate_placeholder(state)
                logger.debug("Generated placeholder for state {}", state.value)
            self._frames[state] = frames
        self._frames[PetState.DRAGGING] = self._frames[PetState.IDLE]

    def _load_frames_from_dir(self, directory: Path) -> list[QPixmap]:
        if not directory.exists():
            return []
        frames = []
        for f in sorted(directory.iterdir()):
            if f.suffix.lower() in (".png", ".gif", ".jpg", ".bmp"):
                pixmap = QPixmap(str(f))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        self._size, self._size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    frames.append(scaled)
        return frames

    def _generate_placeholder(self, state: PetState) -> list[QPixmap]:
        frames = []
        for i in range(_FRAME_COUNT):
            pixmap = QPixmap(self._size, self._size)
            pixmap.fill(Qt.GlobalColor.transparent)
            p = QPainter(pixmap)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._draw_ghost(p, state, i)
            p.end()
            frames.append(pixmap)
        return frames

    def _draw_ghost(self, p: QPainter, state: PetState, frame: int):
        s = self._size
        bounce = [0, -3, 0, 3][frame]
        body_y_offset = bounce

        if state == PetState.SIT:
            body_y_offset = 10
        elif state == PetState.SLEEP:
            body_y_offset = 14

        cx, cy = s / 2, s / 2 + body_y_offset

        # Wavy bottom tail
        tail_path = QPainterPath()
        bw = s * 0.55
        bh = s * 0.38
        tail_top = cy + bh * 0.2
        tail_bottom = cy + bh * 0.75

        wave_shift = frame * 3
        tail_path.moveTo(cx - bw * 0.8, tail_top)
        tail_path.lineTo(cx - bw * 0.8, tail_bottom)
        for j in range(5):
            x1 = cx - bw * 0.8 + (bw * 1.6) * (j + 0.5) / 5
            x2 = cx - bw * 0.8 + (bw * 1.6) * (j + 1) / 5
            peak = tail_bottom + 8 + (4 if (j + frame) % 2 == 0 else -2)
            tail_path.quadTo(x1, peak + wave_shift % 4, x2, tail_bottom)
        tail_path.lineTo(cx + bw * 0.8, tail_top)
        tail_path.closeSubpath()

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(_BODY_COLOR))
        p.drawPath(tail_path)

        # Main body ellipse
        p.drawEllipse(int(cx - bw), int(cy - bh), int(bw * 2), int(bh * 2))

        # Highlight
        p.setBrush(QBrush(_BODY_HIGHLIGHT))
        p.drawEllipse(int(cx - bw * 0.5), int(cy - bh * 0.7), int(bw * 0.7), int(bh * 0.5))

        # Eyes
        eye_y = cy - bh * 0.1
        eye_sep = bw * 0.4
        eye_w, eye_h = s * 0.07, s * 0.09

        if state == PetState.SLEEP:
            # Closed eyes (lines)
            p.setPen(QPen(_EYE_COLOR, 2))
            p.drawLine(int(cx - eye_sep - eye_w), int(eye_y), int(cx - eye_sep + eye_w), int(eye_y))
            p.drawLine(int(cx + eye_sep - eye_w), int(eye_y), int(cx + eye_sep + eye_w), int(eye_y))
            # Zzz
            p.setPen(QPen(QColor(100, 80, 160, 180), 1.5))
            font = p.font()
            font.setPixelSize(int(s * 0.12))
            font.setBold(True)
            p.setFont(font)
            zx = cx + bw * 0.6 + frame * 2
            zy = cy - bh * 0.8 - frame * 3
            p.drawText(int(zx), int(zy), "z")
            font.setPixelSize(int(s * 0.09))
            p.setFont(font)
            p.drawText(int(zx + 8), int(zy - 10), "z")
        elif state == PetState.TALK:
            # Excited eyes (bigger)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_EYE_COLOR))
            ew, eh = eye_w * 1.3, eye_h * 1.3
            p.drawEllipse(int(cx - eye_sep - ew), int(eye_y - eh), int(ew * 2), int(eh * 2))
            p.drawEllipse(int(cx + eye_sep - ew), int(eye_y - eh), int(ew * 2), int(eh * 2))
            # Eye shine
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(int(cx - eye_sep), int(eye_y - eh * 0.5), int(ew * 0.6), int(eh * 0.6))
            p.drawEllipse(int(cx + eye_sep), int(eye_y - eh * 0.5), int(ew * 0.6), int(eh * 0.6))
        else:
            # Normal eyes with blink on frame 3
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_EYE_COLOR))
            if frame == 3:
                p.drawLine(int(cx - eye_sep - eye_w), int(eye_y), int(cx - eye_sep + eye_w), int(eye_y))
                p.drawLine(int(cx + eye_sep - eye_w), int(eye_y), int(cx + eye_sep + eye_w), int(eye_y))
            else:
                p.drawEllipse(int(cx - eye_sep - eye_w), int(eye_y - eye_h), int(eye_w * 2), int(eye_h * 2))
                p.drawEllipse(int(cx + eye_sep - eye_w), int(eye_y - eye_h), int(eye_w * 2), int(eye_h * 2))
                p.setBrush(QBrush(QColor(255, 255, 255)))
                p.drawEllipse(int(cx - eye_sep + eye_w * 0.2), int(eye_y - eye_h * 0.6), int(eye_w * 0.6), int(eye_h * 0.5))
                p.drawEllipse(int(cx + eye_sep + eye_w * 0.2), int(eye_y - eye_h * 0.6), int(eye_w * 0.6), int(eye_h * 0.5))

        # Cheeks
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(_CHEEK_COLOR))
        cheek_y = eye_y + eye_h * 2.5
        p.drawEllipse(int(cx - eye_sep - bw * 0.25), int(cheek_y), int(bw * 0.3), int(bh * 0.15))
        p.drawEllipse(int(cx + eye_sep), int(cheek_y), int(bw * 0.3), int(bh * 0.15))

        # Walking lean
        if state == PetState.WALK_LEFT:
            pass  # body is already drawn centered, slight lean via bounce
        elif state == PetState.WALK_RIGHT:
            pass

        # Action sparkles
        if state == PetState.ACTION:
            p.setPen(QPen(QColor(255, 220, 100), 2))
            offsets = [(0.8, -0.9), (-0.7, -0.85), (0.9, -0.5), (-0.85, -0.6)]
            ox, oy = offsets[frame]
            sx_pos = cx + bw * ox
            sy_pos = cy + bh * oy
            arm = s * 0.05
            p.drawLine(int(sx_pos - arm), int(sy_pos), int(sx_pos + arm), int(sy_pos))
            p.drawLine(int(sx_pos), int(sy_pos - arm), int(sx_pos), int(sy_pos + arm))

    @property
    def state(self) -> PetState:
        return self._state

    @property
    def frame_index(self) -> int:
        return self._frame_index

    def set_state(self, new_state: PetState):
        if new_state != self._state:
            logger.trace("State {} -> {}", self._state.value, new_state.value)
            self._state = new_state
            self._frame_index = 0

    def advance_frame(self) -> QPixmap:
        frames = self._frames.get(self._state, self._frames[PetState.IDLE])
        self._frame_index = (self._frame_index + 1) % len(frames)
        return frames[self._frame_index]

    def current_frame(self) -> QPixmap:
        frames = self._frames.get(self._state, self._frames[PetState.IDLE])
        return frames[self._frame_index % len(frames)]
