import math
import pygame

from .. import config
from ..ui import draw_text
from .score_base import ScoreGameState


class TimingGameState(ScoreGameState):
    game_id = "timing"
    game_name = "Timing"

    def __init__(self, app) -> None:
        super().__init__(app)
        self._cursor_pos = 0.0
        self._cursor_dir = 1.0
        self._cursor_speed = 0.55
        self._target_pos = 0.5
        self._target_offset = 0.0
        self._target_offset_dir = 1.0
        self._target_offset_speed = 0.0
        self._pulse = 0.0
        self._base_width = 120.0
        self._score = 0
        self._missed = False
        self._flash = 0.0

    def on_game_start(self) -> None:
        self._cursor_pos = 0.0
        self._cursor_dir = 1.0
        self._cursor_speed = 0.55
        self._target_pos = 0.5
        self._target_offset = 0.0
        self._target_offset_dir = 1.0
        self._target_offset_speed = 0.0
        self._pulse = 0.0
        self._base_width = 120.0
        self._score = 0
        self._missed = False
        self._flash = 0.0

    def handle_game_input(self, pressed):
        if "middle" in pressed or "start" in pressed:
            self._check_hit()

    def update_game(self, dt: float) -> None:
        self._cursor_pos += self._cursor_dir * self._cursor_speed * dt
        if self._cursor_pos >= 1.0:
            self._cursor_pos = 1.0
            self._cursor_dir = -1.0
        elif self._cursor_pos <= 0.0:
            self._cursor_pos = 0.0
            self._cursor_dir = 1.0

        if self._target_offset_speed > 0.0:
            self._target_offset += self._target_offset_dir * self._target_offset_speed * dt
            if abs(self._target_offset) >= 0.22:
                self._target_offset = max(-0.22, min(0.22, self._target_offset))
                self._target_offset_dir *= -1.0
            self._target_offset_speed = max(0.0, self._target_offset_speed - dt * 0.35)
        self._pulse += dt * 2.5
        # slowly shrink base size as score grows
        self._base_width = max(50.0, 120.0 - self._score * 4.0)
        self._flash = max(0.0, self._flash - dt)

    def render_game(self, surface) -> None:
        self.app.draw_background(surface)
        body_font = self.app.fonts["body"]

        bar_rect = pygame.Rect(140, 240, self.app.width - 280, 40)
        pygame.draw.rect(surface, (255, 255, 255), bar_rect, border_radius=12)

        pulse = 0.5 + 0.5 * math.sin(self._pulse)
        width = int(self._base_width * (0.75 + 0.25 * pulse))
        width = max(40, min(width, bar_rect.width - 20))
        target_center = self._target_pos + self._target_offset
        target_center = max(0.0, min(1.0, target_center))
        target_x = bar_rect.left + int(target_center * (bar_rect.width - width)) + width // 2
        target_rect = pygame.Rect(target_x - width // 2, bar_rect.top + 6, width, bar_rect.height - 12)
        pygame.draw.rect(surface, config.COLOR_ACCENT, target_rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), target_rect, width=2, border_radius=10)

        knob_x = bar_rect.left + int(self._cursor_pos * bar_rect.width)
        cursor = self.app.images.get("cursor")
        if cursor:
            size = 36
            sprite = pygame.transform.smoothscale(cursor, (size, size))
            rect = sprite.get_rect(center=(knob_x, bar_rect.centery))
            surface.blit(sprite, rect)
        else:
            knob_color = config.COLOR_WARNING if self._flash > 0 else (0, 0, 0)
            pygame.draw.circle(surface, knob_color, (knob_x, bar_rect.centery), 18)

        draw_text(surface, f"Score: {self._score}", body_font, config.COLOR_TEXT_DARK,
                  (self.app.center_x, 140))
        if target_rect.left <= knob_x <= target_rect.right:
            draw_text(surface, "JETZT DRUECKEN!", body_font, config.COLOR_WARNING,
                      (self.app.center_x, 320))
        else:
            draw_text(surface, "WARTEN BIS IM ZIEL", body_font, config.COLOR_TEXT_DARK,
                      (self.app.center_x, 320))

    def _check_hit(self) -> None:
        # success window around center
        bar_rect = pygame.Rect(140, 240, self.app.width - 280, 40)
        pulse = 0.5 + 0.5 * math.sin(self._pulse)
        width = int(self._base_width * (0.75 + 0.25 * pulse))
        width = max(40, min(width, bar_rect.width - 20))
        target_center = self._target_pos + self._target_offset
        target_center = max(0.0, min(1.0, target_center))
        target_x = bar_rect.left + int(target_center * (bar_rect.width - width)) + width // 2
        knob_x = bar_rect.left + int(self._cursor_pos * bar_rect.width)
        hit = (target_x - width // 2) <= knob_x <= (target_x + width // 2)
        if hit:
            self._score += 1
            self._cursor_speed = min(1.4, self._cursor_speed + 0.08)
            self._target_offset_speed = min(1.0, self._target_offset_speed + 0.45)
            self._target_offset_dir *= -1.0
            self._flash = 0.15
        else:
            self.trigger_game_over(self._score)
