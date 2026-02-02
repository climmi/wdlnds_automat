import pygame

from .. import config
from ..ui import draw_text, draw_panel
from .base import BaseState


class GameSelectState(BaseState):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._options = [
            ("runner", "RUNNER"),
            ("timing", "TIMING"),
            ("hold", "HOLD"),
        ]
        self._index = 0

    def on_enter(self) -> None:
        if self.app.credits <= 0:
            self.app.state_machine.change("idle")
            return
        # keep last selected if possible
        for idx, (gid, _) in enumerate(self._options):
            if gid == self.app.current_game:
                self._index = idx
                break

    def handle_input(self, pressed):
        if "left" in pressed:
            self._index = (self._index - 1) % len(self._options)
            self.app.sound.play_beep()
        if "right" in pressed:
            self._index = (self._index + 1) % len(self._options)
            self.app.sound.play_beep()
        if "middle" in pressed or "start" in pressed:
            self._start_game()

    def update(self, dt: float) -> None:
        if self.app.credits <= 0:
            self.app.state_machine.change("idle")

    def render(self, surface) -> None:
        self.app.draw_background(surface)
        title_font = self.app.fonts["title"]
        body_font = self.app.fonts["body"]

        draw_text(surface, "GAME WAHL", title_font, config.COLOR_TEXT_DARK,
                  (self.app.center_x, 120))

        panel_rect = pygame.Rect(140, 190, self.app.width - 280, 200)
        draw_panel(surface, panel_rect, config.COLOR_PANEL, config.COLOR_ACCENT, border=2)

        for idx, (_, name) in enumerate(self._options):
            color = config.COLOR_ACCENT if idx == self._index else config.COLOR_TEXT
            draw_text(surface, name, body_font, color,
                      (self.app.center_x, 230 + idx * 50))

        game_id, _ = self._options[self._index]
        status = self.app.highscores.get_status(game_id)
        draw_text(surface, f"Highscore: {status.top_name} {status.top_score}", body_font,
                  config.COLOR_TEXT_DARK, (self.app.center_x, 420))

    def _start_game(self) -> None:
        game_id, _ = self._options[self._index]
        self.app.current_game = game_id
        self.app.consume_credit()
        if game_id == "runner":
            self.app.state_machine.change("minigame")
        elif game_id == "timing":
            self.app.state_machine.change("timing")
        else:
            self.app.state_machine.change("hold")
