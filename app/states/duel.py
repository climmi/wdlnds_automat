import random
import pygame

from .. import config
from ..ui import draw_text
from .score_base import ScoreGameState


class DuelGameState(ScoreGameState):
    game_id = "duel"
    game_name = "Duel"

    def __init__(self, app) -> None:
        super().__init__(app)
        self._active_side = None
        self._timer = 0.0
        self._window = 0.8
        self._score = 0
        self._phase = "ready"
        self._ready_timer = 0.0
        self._ready_delay = 0.0

    def on_game_start(self) -> None:
        self._active_side = random.choice(["left", "right"])
        self._timer = 0.0
        self._window = 0.8
        self._score = 0
        self._phase = "ready"
        self._ready_timer = 0.0
        self._ready_delay = random.uniform(0.7, 1.6)

    def handle_game_input(self, pressed):
        if self._phase != "go":
            if "left" in pressed or "right" in pressed:
                self.trigger_game_over(self._score)
            return
        if self._active_side in pressed:
            self._score += 1
            self._window = max(0.25, self._window - 0.04)
            self._timer = 0.0
            self._active_side = random.choice(["left", "right"])
            self._phase = "ready"
            self._ready_timer = 0.0
            self._ready_delay = random.uniform(0.5, 1.2)
        elif "left" in pressed or "right" in pressed:
            self.trigger_game_over(self._score)

    def update_game(self, dt: float) -> None:
        if self._phase == "ready":
            self._ready_timer += dt
            if self._ready_timer >= self._ready_delay:
                self._phase = "go"
                self._timer = 0.0
            return
        self._timer += dt
        if self._timer > self._window:
            self.trigger_game_over(self._score)

    def render_game(self, surface) -> None:
        self.app.draw_background(surface)
        body_font = self.app.fonts["body"]

        left_rect = pygame.Rect(160, 220, 160, 160)
        right_rect = pygame.Rect(self.app.width - 320, 220, 160, 160)
        pygame.draw.rect(surface, config.COLOR_ACCENT if self._active_side == "left" else config.COLOR_PANEL,
                         left_rect, border_radius=12)
        pygame.draw.rect(surface, config.COLOR_ACCENT if self._active_side == "right" else config.COLOR_PANEL,
                         right_rect, border_radius=12)

        draw_text(surface, "LEFT", body_font, config.COLOR_TEXT,
                  left_rect.center)
        draw_text(surface, "RIGHT", body_font, config.COLOR_TEXT,
                  right_rect.center)

        draw_text(surface, f"Score: {self._score}", body_font, config.COLOR_TEXT_DARK,
                  (self.app.center_x, 140))
        if self._phase == "ready":
            draw_text(surface, "WARTEN...", body_font, config.COLOR_TEXT_DARK,
                      (self.app.center_x, 420))
        else:
            draw_text(surface, f"DRUECKE {self._active_side.upper()} JETZT!", body_font, config.COLOR_WARNING,
                      (self.app.center_x, 420))
