"""Sprite animation engine with state machine and placeholder generation."""

import math
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
    QTransform,
)
from loguru import logger


class PetState(Enum):
    IDLE = "idle"
    WALK_LEFT = "walk_left"
    WALK_RIGHT = "walk_right"
    WANDER = "wander"
    SPIN = "spin"
    SIT = "sit"
    SLEEP = "sleep"
    TALK = "talk"
    ACTION = "action"
    CRY = "cry"
    HAPPY = "happy"
    TIRED = "tired"
    DRAGGING = "dragging"


_BODY_COLOR = QColor(180, 160, 220)
_BODY_HIGHLIGHT = QColor(210, 195, 240)
_EYE_COLOR = QColor(40, 20, 60)
_CHEEK_COLOR = QColor(230, 170, 190, 100)
_TEAR_COLOR = QColor(100, 180, 255, 180)

_FRAME_COUNT = 6
_SPIN_FRAME_COUNT = 12

_REUSE_IDLE = {PetState.DRAGGING, PetState.WANDER}
_SWEAT_COLOR = QColor(130, 200, 255, 180)


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
            if state in _REUSE_IDLE:
                continue
            state_dir = self._assets_dir / state.value
            frames = self._load_frames_from_dir(state_dir)
            if not frames:
                frames = self._generate_placeholder(state)
                logger.debug("Generated placeholder for state {}", state.value)
            self._frames[state] = frames
        for alias in _REUSE_IDLE:
            self._frames[alias] = self._frames[PetState.IDLE]

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
        count = _SPIN_FRAME_COUNT if state == PetState.SPIN else _FRAME_COUNT
        frames = []
        for i in range(count):
            pixmap = QPixmap(self._size, self._size)
            pixmap.fill(Qt.GlobalColor.transparent)
            if state == PetState.SPIN:
                base = self._frames.get(PetState.IDLE)
                if base:
                    angle = (360 / count) * i
                    t = QTransform()
                    t.translate(self._size / 2, self._size / 2)
                    t.rotate(angle)
                    t.translate(-self._size / 2, -self._size / 2)
                    p = QPainter(pixmap)
                    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    p.setTransform(t)
                    p.drawPixmap(0, 0, base[0])
                    p.end()
                else:
                    p = QPainter(pixmap)
                    p.setRenderHint(QPainter.RenderHint.Antialiasing)
                    self._draw_ghost(p, PetState.IDLE, i % _FRAME_COUNT)
                    p.end()
            else:
                p = QPainter(pixmap)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                self._draw_ghost(p, state, i)
                p.end()
            frames.append(pixmap)
        return frames

    def _draw_ghost(self, p: QPainter, state: PetState, frame: int):
        s = self._size
        bounce = [0, -4, -2, 2, 4, 1][frame % 6]
        body_y_offset = bounce

        if state == PetState.SIT:
            body_y_offset = 10
        elif state == PetState.SLEEP:
            body_y_offset = 14
        elif state == PetState.HAPPY:
            body_y_offset = [0, -8, -4, 2, -6, -1][frame % 6]
        elif state == PetState.CRY:
            body_y_offset = 6
        elif state == PetState.TIRED:
            body_y_offset = 8 + [0, 1, 2, 1, 0, -1][frame % 6]

        cx, cy = s / 2, s / 2 + body_y_offset

        bw = s * 0.55
        bh = s * 0.38

        # Wavy tail
        tail_path = QPainterPath()
        tail_top = cy + bh * 0.2
        tail_bottom = cy + bh * 0.75
        tail_path.moveTo(cx - bw * 0.8, tail_top)
        tail_path.lineTo(cx - bw * 0.8, tail_bottom)
        for j in range(5):
            x1 = cx - bw * 0.8 + (bw * 1.6) * (j + 0.5) / 5
            x2 = cx - bw * 0.8 + (bw * 1.6) * (j + 1) / 5
            peak = tail_bottom + 8 + (4 if (j + frame) % 2 == 0 else -2)
            tail_path.quadTo(x1, peak + (frame * 3) % 4, x2, tail_bottom)
        tail_path.lineTo(cx + bw * 0.8, tail_top)
        tail_path.closeSubpath()

        p.setPen(Qt.PenStyle.NoPen)

        # Body color shift for emotions
        body_col = _BODY_COLOR
        if state == PetState.CRY:
            body_col = QColor(170, 155, 215)
        elif state == PetState.HAPPY:
            body_col = QColor(200, 175, 235)

        p.setBrush(QBrush(body_col))
        p.drawPath(tail_path)
        p.drawEllipse(int(cx - bw), int(cy - bh), int(bw * 2), int(bh * 2))

        # Highlight
        p.setBrush(QBrush(_BODY_HIGHLIGHT))
        p.drawEllipse(int(cx - bw * 0.5), int(cy - bh * 0.7), int(bw * 0.7), int(bh * 0.5))

        eye_y = cy - bh * 0.1
        eye_sep = bw * 0.4
        eye_w, eye_h = s * 0.07, s * 0.09

        self._draw_eyes(p, state, frame, cx, cy, bw, bh, eye_y, eye_sep, eye_w, eye_h)
        self._draw_extras(p, state, frame, cx, cy, bw, bh, eye_y, eye_sep, eye_w, eye_h, s)

    def _draw_eyes(self, p, state, frame, cx, cy, bw, bh, eye_y, eye_sep, eye_w, eye_h):
        if state == PetState.SLEEP:
            p.setPen(QPen(_EYE_COLOR, 2))
            for side in (-1, 1):
                ex = cx + eye_sep * side
                p.drawLine(int(ex - eye_w), int(eye_y), int(ex + eye_w), int(eye_y))
        elif state == PetState.CRY:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_EYE_COLOR))
            for side in (-1, 1):
                ex = cx + eye_sep * side
                # Droopy sad eyes (flat top, round bottom)
                p.drawEllipse(int(ex - eye_w), int(eye_y - eye_h * 0.6), int(eye_w * 2), int(eye_h * 1.6))
                # Eyebrow slant (sad)
                p.setPen(QPen(_EYE_COLOR, 1.5))
                brow_inner = ex + eye_w * 0.5 * side
                brow_outer = ex - eye_w * 1.5 * side
                p.drawLine(int(brow_inner), int(eye_y - eye_h * 1.5), int(brow_outer), int(eye_y - eye_h * 2.2))
                p.setPen(Qt.PenStyle.NoPen)
        elif state == PetState.HAPPY:
            # Happy closed smile eyes (upward curves)
            p.setPen(QPen(_EYE_COLOR, 2.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            for side in (-1, 1):
                ex = cx + eye_sep * side
                path = QPainterPath()
                path.moveTo(ex - eye_w * 1.2, eye_y)
                path.quadTo(ex, eye_y - eye_h * 2, ex + eye_w * 1.2, eye_y)
                p.drawPath(path)
        elif state == PetState.TIRED:
            # Half-closed droopy eyes
            p.setPen(QPen(_EYE_COLOR, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            for side in (-1, 1):
                ex = cx + eye_sep * side
                # Top eyelid drooping down (half-closed)
                lid_y = eye_y - eye_h * 0.3
                p.drawLine(int(ex - eye_w * 1.2), int(lid_y), int(ex + eye_w * 1.2), int(lid_y + eye_h * 0.4))
                # Small visible eye underneath
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(_EYE_COLOR))
                p.drawEllipse(int(ex - eye_w * 0.7), int(lid_y + eye_h * 0.1), int(eye_w * 1.4), int(eye_h * 0.9))
                p.setPen(QPen(_EYE_COLOR, 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
        elif state == PetState.TALK:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_EYE_COLOR))
            ew, eh = eye_w * 1.3, eye_h * 1.3
            for side in (-1, 1):
                ex = cx + eye_sep * side
                p.drawEllipse(int(ex - ew), int(eye_y - eh), int(ew * 2), int(eh * 2))
            p.setBrush(QBrush(QColor(255, 255, 255)))
            for side in (-1, 1):
                ex = cx + eye_sep * side
                p.drawEllipse(int(ex + ew * 0.15), int(eye_y - eh * 0.5), int(ew * 0.6), int(eh * 0.6))
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_EYE_COLOR))
            blink = frame == 5
            for side in (-1, 1):
                ex = cx + eye_sep * side
                if blink:
                    p.setPen(QPen(_EYE_COLOR, 1.5))
                    p.drawLine(int(ex - eye_w), int(eye_y), int(ex + eye_w), int(eye_y))
                    p.setPen(Qt.PenStyle.NoPen)
                else:
                    p.drawEllipse(int(ex - eye_w), int(eye_y - eye_h), int(eye_w * 2), int(eye_h * 2))
                    p.setBrush(QBrush(QColor(255, 255, 255)))
                    p.drawEllipse(int(ex + eye_w * 0.2), int(eye_y - eye_h * 0.6), int(eye_w * 0.6), int(eye_h * 0.5))
                    p.setBrush(QBrush(_EYE_COLOR))

    def _draw_extras(self, p, state, frame, cx, cy, bw, bh, eye_y, eye_sep, eye_w, eye_h, s):
        # Cheeks (all states except sleep/cry/tired)
        if state not in (PetState.SLEEP, PetState.CRY, PetState.TIRED):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_CHEEK_COLOR))
            cheek_y = eye_y + eye_h * 2.5
            p.drawEllipse(int(cx - eye_sep - bw * 0.25), int(cheek_y), int(bw * 0.3), int(bh * 0.15))
            p.drawEllipse(int(cx + eye_sep), int(cheek_y), int(bw * 0.3), int(bh * 0.15))

        if state == PetState.SLEEP:
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

        elif state == PetState.CRY:
            # Tears streaming down
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_TEAR_COLOR))
            tear_y_base = eye_y + eye_h * 1.5
            tear_offset = (frame * 4) % int(bh)
            for side in (-1, 1):
                tx = cx + eye_sep * side - eye_w * 0.3
                for drop in range(3):
                    dy = tear_y_base + tear_offset + drop * 6
                    if dy < cy + bh * 0.8:
                        radius = 2.5 - drop * 0.5
                        p.drawEllipse(int(tx - radius), int(dy), int(radius * 2), int(radius * 3))
            # Sad mouth
            p.setPen(QPen(_EYE_COLOR, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            mouth_y = eye_y + eye_h * 4
            mouth_path = QPainterPath()
            mouth_path.moveTo(cx - bw * 0.15, mouth_y)
            mouth_path.quadTo(cx, mouth_y + bh * 0.15, cx + bw * 0.15, mouth_y)
            p.drawPath(mouth_path)

        elif state == PetState.HAPPY:
            # Little sparkles
            p.setPen(QPen(QColor(255, 230, 100, 200), 2))
            offsets = [
                (0.75, -0.95), (-0.8, -0.9), (0.9, -0.4),
                (-0.85, -0.5), (0.6, -0.75), (-0.65, -0.7),
            ]
            ox, oy = offsets[frame % len(offsets)]
            sx = cx + bw * ox
            sy = cy + bh * oy
            arm = s * 0.04
            p.drawLine(int(sx - arm), int(sy), int(sx + arm), int(sy))
            p.drawLine(int(sx), int(sy - arm), int(sx), int(sy + arm))
            # Happy mouth (smile)
            p.setPen(QPen(_EYE_COLOR, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            mouth_y = eye_y + eye_h * 3
            mouth_path = QPainterPath()
            mouth_path.moveTo(cx - bw * 0.2, mouth_y)
            mouth_path.quadTo(cx, mouth_y + bh * 0.25, cx + bw * 0.2, mouth_y)
            p.drawPath(mouth_path)

        elif state == PetState.TIRED:
            # Sweat drops
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_SWEAT_COLOR))
            sweat_x = cx + bw * 0.7
            sweat_base_y = cy - bh * 0.6
            drop_offset = (frame * 3) % 12
            p.drawEllipse(int(sweat_x - 2), int(sweat_base_y + drop_offset), 5, 7)
            if frame % 3 != 0:
                p.drawEllipse(int(sweat_x + 4), int(sweat_base_y + drop_offset * 0.6 + 2), 3, 5)

            # Open panting mouth
            p.setPen(QPen(_EYE_COLOR, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            mouth_y = eye_y + eye_h * 3.5
            # Alternating open/close for panting effect
            mouth_open = s * 0.03 * ([1.0, 1.8, 1.2, 1.8, 1.0, 0.6][frame % 6])
            mouth_path = QPainterPath()
            mouth_path.moveTo(cx - bw * 0.1, mouth_y)
            mouth_path.quadTo(cx, mouth_y + mouth_open, cx + bw * 0.1, mouth_y)
            p.drawPath(mouth_path)

            # Flushed cheeks (redder than normal)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(240, 150, 170, 130)))
            cheek_y = eye_y + eye_h * 2
            p.drawEllipse(int(cx - eye_sep - bw * 0.25), int(cheek_y), int(bw * 0.35), int(bh * 0.2))
            p.drawEllipse(int(cx + eye_sep - bw * 0.05), int(cheek_y), int(bw * 0.35), int(bh * 0.2))

        elif state == PetState.ACTION:
            p.setPen(QPen(QColor(255, 220, 100), 2))
            offsets = [(0.8, -0.9), (-0.7, -0.85), (0.9, -0.5), (-0.85, -0.6), (0.7, -0.7), (-0.75, -0.95)]
            ox, oy = offsets[frame % len(offsets)]
            sx = cx + bw * ox
            sy = cy + bh * oy
            arm = s * 0.05
            p.drawLine(int(sx - arm), int(sy), int(sx + arm), int(sy))
            p.drawLine(int(sx), int(sy - arm), int(sx), int(sy + arm))

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
