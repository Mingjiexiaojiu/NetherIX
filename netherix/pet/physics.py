"""Desktop physics: screen boundaries, gravity, ground-level detection."""

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication


class DesktopPhysics:
    """Keeps the pet within screen bounds and simulates gravity."""

    def __init__(self, pet_size: int = 128, gravity_enabled: bool = True):
        self._pet_size = pet_size
        self._gravity_enabled = gravity_enabled
        self._velocity_y = 0.0
        self._gravity_accel = 1.5
        self._max_fall_speed = 12.0

    def available_rect(self) -> QRect:
        screen = QApplication.primaryScreen()
        if screen is None:
            return QRect(0, 0, 1920, 1080)
        return screen.availableGeometry()

    @property
    def ground_y(self) -> int:
        return self.available_rect().bottom() - self._pet_size + 1

    def clamp_position(self, x: int, y: int) -> tuple[int, int]:
        r = self.available_rect()
        x = max(r.left(), min(x, r.right() - self._pet_size + 1))
        y = max(r.top(), min(y, r.bottom() - self._pet_size + 1))
        return x, y

    def screen_bounds(self) -> tuple[int, int, int, int]:
        """Return (left, top, right, bottom) for the pet's usable area."""
        r = self.available_rect()
        return (
            r.left(),
            r.top(),
            r.right() - self._pet_size + 1,
            r.bottom() - self._pet_size + 1,
        )

    def apply_gravity(self, x: int, y: int, is_moving: bool = False) -> tuple[int, int, bool]:
        """Returns (new_x, new_y, on_ground).

        Gravity is suppressed while the pet is actively moving (walking/wandering).
        """
        if not self._gravity_enabled or is_moving:
            self._velocity_y = 0.0
            return x, y, (y >= self.ground_y)

        ground = self.ground_y
        if y >= ground:
            self._velocity_y = 0.0
            return x, ground, True

        self._velocity_y = min(self._velocity_y + self._gravity_accel, self._max_fall_speed)
        new_y = int(y + self._velocity_y)
        if new_y >= ground:
            new_y = ground
            self._velocity_y = 0.0
            return x, new_y, True
        return x, new_y, False

    def is_at_left_edge(self, x: int) -> bool:
        return x <= self.available_rect().left()

    def is_at_right_edge(self, x: int) -> bool:
        return x >= self.available_rect().right() - self._pet_size + 1

    def reset_velocity(self):
        self._velocity_y = 0.0
