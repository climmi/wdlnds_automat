import time
import pygame

from .. import config
from ..ui import draw_text
from .base import BaseState


class IdleState(BaseState):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._blink_on = True
        self._last_blink = time.time()
        self._coin_anim = False
        self._coin_t = 0.0
        self._fade = 0.0
        self._transitioning = False

    def on_enter(self) -> None:
        self._blink_on = True
        self._last_blink = time.time()
        self._coin_anim = False
        self._coin_t = 0.0
        self._fade = 0.0
        self._transitioning = False
        self.app.esp32.send("MODE standby")

    def update(self, dt: float) -> None:
        if time.time() - self._last_blink > 0.6:
            self._blink_on = not self._blink_on
            self._last_blink = time.time()

        if self._transitioning:
            self._fade = min(1.0, self._fade + dt * 1.35)
            if self._fade >= 1.0:
                self.app.state_machine.change("song_select")
            return

        if self._coin_anim:
            self._coin_t = min(1.0, self._coin_t + dt * 1.6)
            if self._coin_t >= 1.0:
                self._coin_anim = False
                self._transitioning = True
            return

        if self.app.consume_coin_event():
            self._coin_anim = True
            self._coin_t = 0.0

    def render(self, surface) -> None:
        self.app.draw_background(surface)
        title_font = self.app.fonts["title"]
        big_font = self.app.fonts.get("big", title_font)
        ink = config.COLOR_TEXT_DARK
        soft = (92, 79, 56)

        draw_text(surface, "COIN-O-MAT", title_font, ink, (self.app.center_x, 154))

        panel_rect = pygame.Rect(108, 224, self.app.width - 216, 206)
        pygame.draw.rect(surface, (255, 253, 240), panel_rect, border_radius=12)
        pygame.draw.rect(surface, ink, panel_rect, width=2, border_radius=12)

        prompt_color = ink if self._blink_on else (128, 118, 98)
        draw_text(surface, "PFANDMARKE", title_font, prompt_color, (self.app.center_x, 278))
        draw_text(surface, "EINWERFEN", big_font, prompt_color, (self.app.center_x, 322))

        self._render_slot(surface, panel_rect)
        if self._coin_anim:
            self._render_coin(surface, panel_rect)
        if self._transitioning:
            self._draw_fade(surface)

    def _draw_fade(self, surface) -> None:
        overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
        overlay.fill((255, 253, 240, int(self._fade * 255)))
        surface.blit(overlay, (0, 0))

    def _render_slot(self, surface, panel_rect) -> None:
        slot_rect = pygame.Rect(panel_rect.centerx - 116, panel_rect.top + 144, 232, 26)
        pygame.draw.rect(surface, (249, 246, 232), slot_rect, border_radius=12)
        pygame.draw.rect(surface, config.COLOR_TEXT_DARK, slot_rect, width=2, border_radius=12)
        draw_text(surface, "INSERT", self.app.fonts["body"], config.COLOR_TEXT_DARK, slot_rect.center)

    def _render_coin(self, surface, panel_rect) -> None:
        coin = self.app.images.get("player")
        if not coin:
            return
        slot_x = panel_rect.centerx
        slot_y = panel_rect.top + 180
        start_x = self.app.width - 120
        start_y = 40
        t = self._coin_t
        ease = 1 - (1 - t) * (1 - t)
        x = start_x + (slot_x - start_x) * ease
        y = start_y + (slot_y - start_y) * ease
        size = 78 - int(18 * t)
        sprite = pygame.transform.smoothscale(coin, (size, size))
        rect = sprite.get_rect(center=(int(x), int(y)))
        surface.blit(sprite, rect)
