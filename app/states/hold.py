import math
import pygame

from .. import config
from ..ui import draw_text
from .score_base import ScoreGameState


class HoldGameState(ScoreGameState):
    game_id = "hold"
    game_name = "Hold"

    def __init__(self, app) -> None:
        super().__init__(app)
        self._theta = 0.0
        self._dir = 1.0
        self._speed = 1.9
        self._score = 0
        self._arc_center = (0, 0)
        self._arc_radius = 180
        self._ball = None
        self._serve_window = (0.0, math.pi)
        self._last_side = None
        self._end_wait = False
        self._end_timer = 0.0

    def on_game_start(self) -> None:
        self._theta = math.pi
        self._dir = -1.0
        self._speed = 1.9
        self._score = 0
        self._arc_center = (self.app.center_x, int(self.app.height * 0.74))
        self._arc_radius = 200
        self._ball = self.app.images.get("ball")
        self._serve_window = (0.0, math.pi)
        self._last_side = None
        self._end_wait = False
        self._end_timer = 0.0

    def handle_game_input(self, pressed):
        right_limit = 0.18 * math.pi
        left_limit = 0.82 * math.pi
        side = None
        if self._theta <= right_limit:
            side = "right"
        elif self._theta >= left_limit:
            side = "left"

        if side is None:
            self._last_side = None
            return

        required_side = "right" if self._dir < 0 else "left"
        if side == required_side and side != self._last_side:
            if side == "left" and "left" in pressed:
                self._attempt_hit()
                self._last_side = side
            elif side == "right" and "right" in pressed:
                self._attempt_hit()
                self._last_side = side
        # ignore all other presses

    def update_game(self, dt: float) -> None:
        if self._end_wait:
            self._end_timer += dt
            if self._end_timer >= 0.2:
                self.trigger_game_over(self._score)
            return

        speed_mod = 0.55 + 0.5 * math.sin(self._theta) - 0.15 * math.sin(2 * self._theta)
        speed_mod = max(0.15, min(1.2, speed_mod))
        self._theta += self._dir * (self._speed * speed_mod) * dt
        if self._theta <= 0.0:
            self._theta = 0.0
            self._end_wait = True
            self._end_timer = 0.0
        elif self._theta >= math.pi:
            self._theta = math.pi
            self._end_wait = True
            self._end_timer = 0.0

    def render_game(self, surface) -> None:
        self.app.draw_background(surface)
        body_font = self.app.fonts["body"]

        center = self._arc_center
        pygame.draw.arc(surface, config.COLOR_PANEL, (center[0] - self._arc_radius, center[1] - self._arc_radius,
                                                      self._arc_radius * 2, self._arc_radius * 2),
                        0.0, math.pi, 4)
        self._draw_timing_zones(surface)

        pos = self._ball_position()
        if self._ball:
            sprite = pygame.transform.smoothscale(self._ball, (42, 42))
            rect = sprite.get_rect(center=pos)
            surface.blit(sprite, rect)
        else:
            pygame.draw.circle(surface, config.COLOR_ACCENT, pos, 20)

        draw_text(surface, f"Score: {self._score}", body_font, config.COLOR_TEXT_DARK,
                  (self.app.center_x, 120))
        draw_text(surface, "A links / D rechts", body_font, config.COLOR_TEXT_DARK,
                  (self.app.center_x, 420))

    def _ball_position(self):
        cx, cy = self._arc_center
        x = cx + math.cos(self._theta) * self._arc_radius
        y = cy - math.sin(self._theta) * self._arc_radius
        return int(x), int(y)

    def _attempt_hit(self) -> None:
        low, high = self._serve_window
        if not (low <= self._theta <= high):
            self.trigger_game_over(self._score)
            return
        self._score += 1
        left_center = low + (high - low) * 0.25
        right_center = low + (high - low) * 0.75
        dist = min(abs(self._theta - left_center), abs(self._theta - right_center))
        band = (high - low) / 4
        ratio = dist / max(0.0001, band)
        if ratio <= 0.33:
            self._speed = min(4.0, self._speed + 0.8)
        elif ratio <= 0.66:
            self._speed = min(4.0, self._speed + 0.45)
        else:
            self._speed = min(4.0, self._speed + 0.2)
        self._dir *= -1.0
        # shrink timing window slowly
        # keep timing window fixed
        self._serve_window = (0.0, math.pi)
        self._end_wait = False
        self._end_timer = 0.0

    def _draw_timing_zones(self, surface) -> None:
        low, high = self._serve_window
        left_center = low
        right_center = high
        band = (high - low) / 10
        good = band * 0.33
        ok = band * 0.66
        center = self._arc_center
        rect = (center[0] - self._arc_radius, center[1] - self._arc_radius,
                self._arc_radius * 2, self._arc_radius * 2)
        # slow zones (left/right)
        pygame.draw.arc(surface, (120, 120, 120), rect, left_center - ok, left_center + ok, 6)
        pygame.draw.arc(surface, (120, 120, 120), rect, right_center - ok, right_center + ok, 6)
        # medium zones
        pygame.draw.arc(surface, config.COLOR_ACCENT, rect, left_center - good, left_center + good, 8)
        pygame.draw.arc(surface, config.COLOR_ACCENT, rect, right_center - good, right_center + good, 8)
        # optimal zones
        pygame.draw.arc(surface, config.COLOR_WARNING, rect, left_center - good * 0.4, left_center + good * 0.4, 10)
        pygame.draw.arc(surface, config.COLOR_WARNING, rect, right_center - good * 0.4, right_center + good * 0.4, 10)
