"""Transparent frameless pet widget that renders the sprite on the desktop."""

import random

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import QMenu, QWidget
from loguru import logger

from netherix.pet.behavior import BehaviorController
from netherix.pet.physics import DesktopPhysics
from netherix.pet.sprite_engine import PetState, SpriteEngine

_MOVING_STATES = {
    PetState.WALK_LEFT, PetState.WALK_RIGHT, PetState.WANDER,
}

_GRAVITY_SUPPRESSED = set(PetState)


class PetWidget(QWidget):
    """The main pet window: transparent, frameless, always-on-top."""

    message_requested = Signal(str)
    double_clicked = Signal()
    position_changed = Signal(QPoint)
    action_triggered = Signal()

    def __init__(
        self,
        assets_dir: str,
        size: int = 128,
        fps: int = 10,
        walk_speed: int = 2,
        idle_timeout: float = 30.0,
        sleep_timeout: float = 300.0,
        auto_walk: bool = True,
        gravity: bool = True,
    ):
        super().__init__()
        self._size = size

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(size, size)

        self._sprite = SpriteEngine(assets_dir, size)
        self._physics = DesktopPhysics(size, gravity)
        self._behavior = BehaviorController(
            walk_speed=walk_speed,
            idle_timeout=idle_timeout,
            sleep_timeout=sleep_timeout,
            auto_walk=auto_walk,
        )

        self._dragging = False
        self._drag_offset = QPoint()

        rect = self._physics.available_rect()
        start_x = rect.right() - size - 100
        start_y = self._physics.ground_y
        self.move(start_x, start_y)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_tick)
        self._anim_timer.start(1000 // fps)

    @property
    def sprite_engine(self) -> SpriteEngine:
        return self._sprite

    @property
    def behavior(self) -> BehaviorController:
        return self._behavior

    def set_pet_state(self, state: PetState):
        self._behavior.force_state(state)
        self._sprite.set_state(state)

    def release_pet_state(self):
        self._behavior.release_force()
        self._sprite.set_state(PetState.IDLE)

    def _on_tick(self):
        if self._dragging:
            self._sprite.set_state(PetState.DRAGGING)
            self._sprite.advance_frame()
            self.update()
            return

        pos = self.pos()
        sl, st, sr, sb = self._physics.screen_bounds()

        state, dx, dy = self._behavior.tick(
            pos.x(), pos.y(), sl, st, sr, sb,
        )
        self._sprite.set_state(state)

        new_x = pos.x() + dx
        new_y = pos.y() + dy

        suppress_gravity = state in _GRAVITY_SUPPRESSED
        new_x, new_y, _ = self._physics.apply_gravity(new_x, new_y, is_moving=suppress_gravity)
        new_x, new_y = self._physics.clamp_position(new_x, new_y)

        self.move(new_x, new_y)
        self._sprite.advance_frame()
        self.update()
        self.position_changed.emit(QPoint(new_x + self._size // 2, new_y))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        frame = self._sprite.current_frame()
        if not frame.isNull():
            p.drawPixmap(0, 0, frame)
        p.end()

    # ── Mouse interaction ──

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            self._behavior.notify_interaction()
            self._physics.reset_velocity()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)
            self.position_changed.emit(
                QPoint(new_pos.x() + self._size // 2, new_pos.y())
            )

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._behavior.notify_interaction()
            self._behavior.release_force()
            self._sprite.set_state(PetState.IDLE)
            self._start_random_walk()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._behavior.notify_interaction()
            self.double_clicked.emit()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #2b2040; color: #e0d0f0; border: 1px solid #5a3d7a; }"
            "QMenu::item:selected { background: #5a3d7a; }"
        )
        menu.addAction("对话", self.double_clicked.emit)
        menu.addSeparator()
        menu.addAction("散步", self._action_random_walk)
        menu.addAction("转圈圈", self._action_spin)
        menu.addAction("开心", self._action_happy)
        menu.addAction("哭泣", self._action_cry)
        menu.addSeparator()
        menu.addAction("坐下", self._action_sit)
        is_sleeping = self._behavior.state == PetState.SLEEP
        if is_sleeping:
            menu.addAction("醒来", self._action_wake)
        else:
            menu.addAction("睡觉", self._action_sleep)
        menu.exec(event.globalPos())

    def _start_random_walk(self):
        sl, st, sr, sb = self._physics.screen_bounds()
        tx = random.randint(sl, sr)
        ty = random.randint(st, sb)
        self._behavior.start_walk_to(tx, ty, self.pos().x(), self.pos().y())

    def _action_random_walk(self):
        self.action_triggered.emit()
        self._start_random_walk()

    def _action_spin(self):
        self.action_triggered.emit()
        self._behavior._begin_spin()

    def _action_happy(self):
        self.action_triggered.emit()
        self._behavior.trigger_emotion(PetState.HAPPY, 5.0)

    def _action_cry(self):
        self.action_triggered.emit()
        self._behavior.trigger_emotion(PetState.CRY, 5.0)

    def _action_sit(self):
        self.action_triggered.emit()
        self.set_pet_state(PetState.SIT)

    def _action_sleep(self):
        self.action_triggered.emit()
        self.set_pet_state(PetState.SLEEP)

    def _action_wake(self):
        self.action_triggered.emit()
        self.release_pet_state()
