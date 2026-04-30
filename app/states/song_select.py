import pygame
import random

from .. import config
from ..storage import load_json
from ..ui import draw_text
from .base import BaseState


class SongSelectState(BaseState):
    OPTIONS = [
        {"label": "LEICHT", "difficulty": "easy", "caption": "LOCKERER GROOVE"},
        {"label": "MITTEL", "difficulty": "medium", "caption": "VOLLER FLOOR"},
        {"label": "SCHWER", "difficulty": "hard", "caption": "SPAEtes SET"},
    ]

    def __init__(self, app) -> None:
        super().__init__(app)
        self._selected = 1
        self._fade_in = 0.0
        self._fade_out = 0.0
        self._leaving = False
        self._catalog = []

    def on_enter(self) -> None:
        self._selected = 1
        self._fade_in = 0.0
        self._fade_out = 0.0
        self._leaving = False
        self._catalog = self._load_catalog()
        self.app.esp32.send("MODE standby")

    def handle_input(self, pressed):
        if self._leaving:
            return
        if "left" in pressed:
            self._selected = (self._selected - 1) % len(self.OPTIONS)
            self.app.esp32.send("LED flash left")
        if "right" in pressed:
            self._selected = (self._selected + 1) % len(self.OPTIONS)
            self.app.esp32.send("LED flash right")
        if "middle" in pressed or "start" in pressed:
            option = self.OPTIONS[self._selected]
            self.app.selected_song = self._pick_song(option)
            self.app.current_game = "show_control"
            self.app.consume_credit()
            self._leaving = True
            self._fade_out = 0.0
            self.app.esp32.send("LED flash middle")

    def update(self, dt: float) -> None:
        if self._leaving:
            self._fade_out = min(1.0, self._fade_out + dt * 1.35)
            if self._fade_out >= 1.0:
                self.app.state_machine.change("minigame")
            return
        self._fade_in = min(1.0, self._fade_in + dt * 1.35)

    def render(self, surface) -> None:
        self.app.draw_background(surface)
        ink = config.COLOR_TEXT_DARK
        soft = (92, 79, 56)

        draw_text(surface, "DJ SET WAEHLEN", self.app.fonts["title"], ink, (self.app.center_x, 130))

        card_w = 252
        card_h = 166
        gap = 28
        total_w = card_w * 3 + gap * 2
        start_x = self.app.center_x - total_w // 2
        y = 220

        for index, option in enumerate(self.OPTIONS):
            x = start_x + index * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            active = index == self._selected
            fill = (255, 253, 240) if active else (246, 238, 222)
            border = (245, 174, 57) if active else (75, 56, 38)
            pygame.draw.rect(surface, fill, rect, border_radius=10)
            pygame.draw.rect(surface, border, rect, width=4 if active else 2, border_radius=10)
            draw_text(surface, option["label"], self.app.fonts["body_bold"], ink, (rect.centerx, rect.top + 54))
            draw_text(surface, option["caption"], self.app.fonts["body"], soft, (rect.centerx, rect.top + 98))
            count = len([song for song in self._catalog if song.get("difficulty") == option["difficulty"]])
            if count > 1:
                draw_text(surface, f"{count} TRACKS", self.app.fonts["body"], soft, (rect.centerx, rect.top + 132))

        draw_text(surface, "LINKS / RECHTS", self.app.fonts["body"], soft, (self.app.center_x, 446))
        draw_text(surface, "MITTE STARTET", self.app.fonts["body_bold"], ink, (self.app.center_x, 480))

        if self._fade_in < 1.0:
            self._draw_fade(surface, 1.0 - self._fade_in)
        if self._leaving:
            self._draw_fade(surface, self._fade_out)

    def _draw_fade(self, surface, amount: float) -> None:
        overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
        overlay.fill((255, 253, 240, int(max(0.0, min(1.0, amount)) * 255)))
        surface.blit(overlay, (0, 0))

    def _load_catalog(self):
        path = f"{config.DATA_DIR}/song_catalog.json"
        payload = load_json(path, [])
        return payload if isinstance(payload, list) else []

    def _pick_song(self, option):
        matches = [song for song in self._catalog if song.get("difficulty") == option["difficulty"]]
        if not matches:
            return option
        picked = dict(random.choice(matches))
        picked.setdefault("label", option["label"])
        picked.setdefault("caption", option["caption"])
        return picked
