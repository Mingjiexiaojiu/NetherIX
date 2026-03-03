"""Autonomous behavior controller: free 2D roaming, emotions, spinning."""

import math
import random
import time

from loguru import logger

from netherix.pet.sprite_engine import PetState


class BehaviorController:
    """Decides what the pet does based on timers, randomness, and AI commands.

    Movement is fully 2D -- the pet can walk in any direction, wander
    diagonally, spin in place, or exhibit emotional states (cry, happy).
    """

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
        self._state = PetState.IDLE
        self._forced = False

        # 2D movement
        self._target_x: float | None = None
        self._target_y: float | None = None
        self._move_angle: float = 0.0  # radians
        self._move_dx: float = 0.0
        self._move_dy: float = 0.0

        # Spin
        self._spin_remaining: int = 0

        # Timed emotion (cry / happy)
        self._emotion_end: float = 0.0

        # Fatigue tracking
        self._walk_steps: int = 0
        self._tired_threshold: int = random.randint(280, 500)
        self._tired_end: float = 0.0

    # ── Properties ──

    @property
    def state(self) -> PetState:
        return self._state

    @property
    def walk_direction(self) -> int:
        if self._move_dx > 0.3:
            return 1
        if self._move_dx < -0.3:
            return -1
        return 0

    # ── External triggers ──

    def notify_interaction(self):
        self._last_interaction = time.time()
        if self._state in (PetState.SIT, PetState.SLEEP, PetState.CRY, PetState.TIRED) and not self._forced:
            self._stop_movement()
            self._state = PetState.IDLE

    def force_state(self, state: PetState):
        self._forced = True
        self._state = state
        self._stop_movement()

    def release_force(self):
        self._forced = False
        self._state = PetState.IDLE
        self._last_interaction = time.time()
        self._stop_movement()
        self._reset_fatigue()

    def start_walk_to(self, target_x: int, target_y: int, current_x: int, current_y: int):
        """Walk toward a specific 2D target."""
        self._target_x = float(target_x)
        self._target_y = float(target_y)
        self._compute_direction(current_x, current_y)
        self._state = self._walk_state_from_dx()
        self._forced = False

    def trigger_emotion(self, emotion: PetState, duration: float = 4.0):
        if emotion in (PetState.CRY, PetState.HAPPY):
            self._state = emotion
            self._emotion_end = time.time() + duration
            self._stop_movement()

    # ── Core tick ──

    def tick(
        self,
        current_x: int,
        current_y: int,
        screen_left: int,
        screen_top: int,
        screen_right: int,
        screen_bottom: int,
    ) -> tuple[PetState, int, int]:
        """Called every frame. Returns (state, dx, dy)."""
        if self._forced:
            return self._state, 0, 0

        # Emotion timeout
        if self._state in (PetState.CRY, PetState.HAPPY):
            if time.time() >= self._emotion_end:
                self._state = PetState.IDLE
            return self._state, 0, 0

        # Tired timeout
        if self._state == PetState.TIRED:
            if time.time() >= self._tired_end:
                self._state = PetState.IDLE
                self._walk_steps = 0
                self._tired_threshold = random.randint(280, 500)
            return self._state, 0, 0

        # Spinning
        if self._state == PetState.SPIN:
            self._spin_remaining -= 1
            if self._spin_remaining <= 0:
                self._state = PetState.IDLE
            return self._state, 0, 0

        # Active movement (walk / wander)
        if self._state in (PetState.WALK_LEFT, PetState.WALK_RIGHT, PetState.WANDER):
            dx = int(round(self._move_dx))
            dy = int(round(self._move_dy))

            # Accumulate steps & check fatigue
            self._walk_steps += 1
            if self._walk_steps >= self._tired_threshold:
                self._stop_movement()
                self._state = PetState.TIRED
                self._tired_end = time.time() + random.uniform(4.0, 8.0)
                return self._state, 0, 0

            # Reached target?
            if self._target_x is not None:
                dist = math.hypot(self._target_x - current_x, self._target_y - current_y)
                if dist < self._walk_speed * 2:
                    self._stop_movement()
                    self._state = PetState.IDLE
                    return self._state, 0, 0

            # Bounce off edges with reflection angle + slight random perturbation
            nx, ny = current_x + dx, current_y + dy
            bounced = False
            if nx <= screen_left or nx >= screen_right:
                self._move_dx *= -1
                bounced = True
            if ny <= screen_top or ny >= screen_bottom:
                self._move_dy *= -1
                bounced = True
            if bounced:
                # Add slight angle perturbation so bounces feel natural
                angle = math.atan2(self._move_dy, self._move_dx)
                angle += random.uniform(-0.25, 0.25)
                speed = math.hypot(self._move_dx, self._move_dy)
                self._move_dx = speed * math.cos(angle)
                self._move_dy = speed * math.sin(angle)
                dx = int(round(self._move_dx))
                dy = int(round(self._move_dy))
                self._target_x = None
                self._target_y = None
                self._state = self._walk_state_from_dx()

            return self._state, dx, dy

        # Idle progression
        idle_dur = time.time() - self._last_interaction

        if self._state == PetState.IDLE:
            if idle_dur > self._sleep_timeout:
                self._state = PetState.SLEEP
                return self._state, 0, 0
            if idle_dur > self._idle_timeout:
                self._state = PetState.SIT
                return self._state, 0, 0
            if self._auto_walk:
                self._try_random_action(current_x, current_y,
                                        screen_left, screen_top, screen_right, screen_bottom)
            return self._state, 0, 0

        if self._state == PetState.SIT:
            if idle_dur > self._sleep_timeout:
                self._state = PetState.SLEEP
            elif self._auto_walk and random.random() < 0.003:
                # Wake up and stretch / walk
                self._state = PetState.IDLE
            return self._state, 0, 0

        return self._state, 0, 0

    # ── Random actions ──

    def _try_random_action(self, cx, cy, sl, st, sr, sb):
        roll = random.random()
        if roll < 0.006:
            self._begin_random_wander(cx, cy, sl, st, sr, sb)
        elif roll < 0.008:
            self._begin_spin()
        elif roll < 0.0095:
            self.trigger_emotion(PetState.HAPPY, random.uniform(2.0, 5.0))
        elif roll < 0.010:
            self.trigger_emotion(PetState.CRY, random.uniform(3.0, 6.0))

    def _begin_random_wander(self, cx, cy, sl, st, sr, sb):
        """Pick a random 2D target and walk toward it."""
        tx = random.randint(sl, sr)
        ty = random.randint(st, sb)
        self._target_x = float(tx)
        self._target_y = float(ty)
        self._compute_direction(cx, cy)
        self._state = self._walk_state_from_dx()

    def _begin_spin(self):
        self._state = PetState.SPIN
        self._spin_remaining = random.randint(12, 36)
        self._stop_movement()

    # ── Helpers ──

    def _compute_direction(self, cx: float, cy: float):
        if self._target_x is None or self._target_y is None:
            return
        dx = self._target_x - cx
        dy = self._target_y - cy
        dist = math.hypot(dx, dy)
        if dist < 1:
            self._move_dx = 0.0
            self._move_dy = 0.0
            return
        speed = self._walk_speed
        self._move_dx = speed * dx / dist
        self._move_dy = speed * dy / dist

    def _walk_state_from_dx(self) -> PetState:
        if abs(self._move_dy) > abs(self._move_dx) * 0.8:
            return PetState.WANDER
        if self._move_dx >= 0:
            return PetState.WALK_RIGHT
        return PetState.WALK_LEFT

    def _stop_movement(self):
        self._target_x = None
        self._target_y = None
        self._move_dx = 0.0
        self._move_dy = 0.0
        self._spin_remaining = 0

    def _reset_fatigue(self):
        self._walk_steps = 0
        self._tired_threshold = random.randint(280, 500)
