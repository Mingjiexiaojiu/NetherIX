"""Autonomous behavior controller: random walks, idle transitions, etc."""

import random
import time

from loguru import logger

from netherix.pet.sprite_engine import PetState


class BehaviorController:
    """Decides what the pet does when idle based on timers and randomness."""

    def __init__(
        self,
        walk_speed: int = 2,
        idle_timeout: float = 30.0,
        sleep_timeout: float = 300.0,
        auto_walk: bool = True,
    ):
        self._walk_speed = walk_speed
        self._idle_timeout = idle_timeout
        self._sleep_timeout = sleep_timeout
        self._auto_walk = auto_walk

        self._last_interaction = time.time()
        self._walk_target_x: int | None = None
        self._walk_direction: int = 0  # -1 left, +1 right
        self._state = PetState.IDLE
        self._forced = False  # True when AI forced a state

    @property
    def state(self) -> PetState:
        return self._state

    @property
    def walk_direction(self) -> int:
        return self._walk_direction

    def notify_interaction(self):
        self._last_interaction = time.time()
        if self._state in (PetState.SIT, PetState.SLEEP) and not self._forced:
            self._state = PetState.IDLE

    def force_state(self, state: PetState):
        self._forced = True
        self._state = state
        self._walk_target_x = None

    def release_force(self):
        self._forced = False
        self._state = PetState.IDLE
        self._last_interaction = time.time()

    def start_walk_to(self, target_x: int, current_x: int):
        self._walk_target_x = target_x
        self._walk_direction = 1 if target_x > current_x else -1
        self._state = PetState.WALK_RIGHT if self._walk_direction > 0 else PetState.WALK_LEFT
        self._forced = False

    def tick(self, current_x: int, screen_left: int, screen_right: int) -> tuple[PetState, int]:
        """Called every frame. Returns (new_state, dx)."""
        if self._forced:
            return self._state, 0

        idle_duration = time.time() - self._last_interaction

        # Walking logic
        if self._state in (PetState.WALK_LEFT, PetState.WALK_RIGHT):
            dx = self._walk_speed * self._walk_direction
            new_x = current_x + dx

            if self._walk_target_x is not None:
                reached = (self._walk_direction > 0 and new_x >= self._walk_target_x) or \
                          (self._walk_direction < 0 and new_x <= self._walk_target_x)
                if reached:
                    self._state = PetState.IDLE
                    self._walk_target_x = None
                    self._last_interaction = time.time()
                    return self._state, 0

            if new_x <= screen_left or new_x >= screen_right:
                self._walk_direction *= -1
                self._state = PetState.WALK_RIGHT if self._walk_direction > 0 else PetState.WALK_LEFT
                return self._state, 0

            return self._state, dx

        # Idle -> sit -> sleep transitions
        if self._state == PetState.IDLE:
            if idle_duration > self._sleep_timeout:
                self._state = PetState.SLEEP
                return self._state, 0
            if idle_duration > self._idle_timeout:
                self._state = PetState.SIT
                return self._state, 0
            if self._auto_walk and random.random() < 0.008:
                target = random.randint(screen_left, screen_right)
                self.start_walk_to(target, current_x)
                return self._state, 0

        if self._state == PetState.SIT:
            if idle_duration > self._sleep_timeout:
                self._state = PetState.SLEEP
            return self._state, 0

        return self._state, 0
