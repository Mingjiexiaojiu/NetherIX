"""Transparent frameless pet widget that renders the sprite on the desktop."""

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QWidget
from loguru import logger

from netherix.pet.behavior import BehaviorController
from netherix.pet.physics import DesktopPhysics
from netherix.pet.sprite_engine import PetState, SpriteEngine


class PetWidget(QWidget):
    """The main pet window: transparent, frameless, always-on-top."""

    message_requested = Signal(str)
    double_clicked = Signal()

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

        # Place at bottom-right of screen
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
        rect = self._physics.available_rect()

        state, dx = self._behavior.tick(
            pos.x(),
            rect.left(),
            rect.right() - self._size,
        )
        self._sprite.set_state(state)

        new_x = pos.x() + dx
        new_y = pos.y()

        new_x, new_y, _ = self._physics.apply_gravity(new_x, new_y)
        new_x, new_y = self._physics.clamp_position(new_x, new_y)

        self.move(new_x, new_y)
        self._sprite.advance_frame()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        frame = self._sprite.current_frame()
        if not frame.isNull():
            p.drawPixmap(0, 0, frame)
        p.end()

    # --- Mouse interaction ---

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

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._behavior.notify_interaction()
            self._behavior.release_force()
            self._sprite.set_state(PetState.IDLE)

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
        menu.addAction("召唤 NIX", self.double_clicked.emit)
        menu.addSeparator()
        walk_action = menu.addAction("散步")
        walk_action.triggered.connect(self._random_walk)
        sit_action = menu.addAction("坐下")
        sit_action.triggered.connect(lambda: self.set_pet_state(PetState.SIT))
        sleep_action = menu.addAction("睡觉")
        sleep_action.triggered.connect(lambda: self.set_pet_state(PetState.SLEEP))
        wake_action = menu.addAction("醒来")
        wake_action.triggered.connect(self.release_pet_state)
        menu.exec(event.globalPos())

    def _random_walk(self):
        import random
        rect = self._physics.available_rect()
        target = random.randint(rect.left(), rect.right() - self._size)
        self._behavior.start_walk_to(target, self.pos().x())
