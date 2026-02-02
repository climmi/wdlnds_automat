import pygame

from .. import config
from ..ui import draw_text, draw_panel
from .base import BaseState


class ScoreGameState(BaseState):
    game_id = "game"
    game_name = "Game"

    def __init__(self, app) -> None:
        super().__init__(app)
        self._game_over = False
        self._phase = "play"
        self._game_over_timer = 0.0
        self._fade = 0.0
        self._entry_timer = 0.0
        self._pending_score = 0
        self._name_chars = ["A", "A", "A"]
        self._name_index = 0
        self._alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-!?*+")

    def on_enter(self) -> None:
        self._game_over = False
        self._phase = "play"
        self._game_over_timer = 0.0
        self._fade = 0.0
        self._entry_timer = 0.0
        self._pending_score = 0
        self._name_chars = ["A", "A", "A"]
        self._name_index = 0
        self.on_game_start()

    def on_game_start(self) -> None:
        pass

    def handle_input(self, pressed):
        if self._game_over:
            if self._phase == "entry":
                self._handle_name_entry(pressed)
            return
        self.handle_game_input(pressed)

    def handle_game_input(self, pressed):
        pass

    def update(self, dt: float) -> None:
        if self._game_over:
            if self._phase == "gameover_wait":
                self._game_over_timer += dt
                if self._game_over_timer >= 2.0:
                    self._phase = "entry"
                    self._fade = 0.0
                    self._entry_timer = 0.0
            elif self._phase == "entry":
                self._fade = min(1.0, self._fade + dt * 2.2)
                self._entry_timer += dt
                if self._entry_timer >= 25.0:
                    self._finalize_score()
            return

        self.update_game(dt)

    def update_game(self, dt: float) -> None:
        pass

    def render(self, surface) -> None:
        if self._game_over and self._phase == "entry":
            self.app.draw_background(surface)
            title_font = self.app.fonts["title"]
            draw_text(surface, "HIGH SCORE", title_font, config.COLOR_TEXT_DARK,
                      (self.app.center_x, 120))
            self._render_scoreboard(surface, y=self.app.center_y - 120, include_pending=True)
            self._render_name_entry(surface)
            return

        self.render_game(surface)

        if self._game_over and self._phase == "gameover_wait":
            overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
            overlay.fill((180, 180, 180, 140))
            surface.blit(overlay, (0, 0))
            draw_text(surface, "GAME OVER", self.app.fonts["title"], config.COLOR_WARNING,
                      (self.app.center_x, self.app.center_y))

    def render_game(self, surface) -> None:
        pass

    def trigger_game_over(self, score: int) -> None:
        if self._game_over:
            return
        self._game_over = True
        self._phase = "gameover_wait"
        self._game_over_timer = 0.0
        self._pending_score = int(score)
        self.app.sound.play_win()

    def _handle_name_entry(self, pressed) -> None:
        if self._phase != "entry":
            return
        if "left" in pressed:
            current = self._name_chars[self._name_index]
            idx = self._alphabet.index(current) if current in self._alphabet else 0
            self._name_chars[self._name_index] = self._alphabet[(idx - 1) % len(self._alphabet)]
            self.app.sound.play_beep()
            self._entry_timer = 0.0
        if "right" in pressed:
            current = self._name_chars[self._name_index]
            idx = self._alphabet.index(current) if current in self._alphabet else 0
            self._name_chars[self._name_index] = self._alphabet[(idx + 1) % len(self._alphabet)]
            self.app.sound.play_beep()
            self._entry_timer = 0.0
        if "middle" in pressed:
            self._name_index = (self._name_index + 1) % len(self._name_chars)
            self.app.sound.play_beep()
            self._entry_timer = 0.0
        if "start" in pressed:
            self._finalize_score()

    def _render_name_entry(self, surface) -> None:
        body_font = self.app.fonts["body"]
        slot_size = 54
        gap = 18
        total = slot_size * 3 + gap * 2
        start_x = self.app.center_x - total / 2
        y = self.app.center_y + 110
        for idx, ch in enumerate(self._name_chars):
            rect = pygame.Rect(int(start_x + idx * (slot_size + gap)), y, slot_size, slot_size)
            color = config.COLOR_ACCENT if idx == self._name_index else config.COLOR_PANEL
            pygame.draw.rect(surface, color, rect, border_radius=8)
            draw_text(surface, ch, body_font, config.COLOR_TEXT, rect.center)
        draw_text(surface, "Links/Rechts: Zeichen | Mitte: Feld | Start: OK", body_font,
                  config.COLOR_TEXT_DARK, (self.app.center_x, y + 80))

    def _render_scoreboard(self, surface, y: int, include_pending: bool = False) -> None:
        body_font = self.app.fonts["body"]
        status = self.app.highscores.get_status(self.game_id)
        entries = list(status.scores[:5])
        pending_index = None
        if include_pending:
            name = "".join(self._name_chars)
            pending = {"name": name, "score": int(self._pending_score)}
            inserted = False
            for idx, entry in enumerate(entries):
                if pending["score"] > int(entry["score"]):
                    entries.insert(idx, pending)
                    pending_index = idx
                    inserted = True
                    break
            if not inserted and len(entries) < 5:
                pending_index = len(entries)
                entries.append(pending)
            entries = entries[:5]

        row_count = max(1, len(entries))
        title_h = 24
        row_h = 22
        pad_y = 14
        panel_height = pad_y * 2 + title_h + row_count * row_h
        panel_width = 420
        panel_rect = pygame.Rect(
            int(self.app.center_x - panel_width / 2),
            int(min(y - pad_y, self.app.height - panel_height - 18)),
            panel_width,
            panel_height,
        )
        draw_panel(surface, panel_rect, config.COLOR_PANEL, config.COLOR_ACCENT, border=2)
        title_y = panel_rect.top + pad_y
        if not entries:
            draw_text(surface, "Highscore: ---", body_font, config.COLOR_TEXT,
                      (self.app.center_x, title_y + title_h))
            return
        draw_text(surface, "Highscore Top 5", body_font, config.COLOR_TEXT,
                  (self.app.center_x, title_y + title_h / 2))
        for idx, entry in enumerate(entries):
            line = f"{idx + 1}. {entry['name']}  {entry['score']}"
            color = config.COLOR_ACCENT if include_pending and pending_index == idx else config.COLOR_TEXT
            draw_text(surface, line, body_font, color,
                      (self.app.center_x, title_y + title_h + row_h / 2 + idx * row_h))

    def _finalize_score(self) -> None:
        name = "".join(self._name_chars)
        self.app.highscores.register_score(self.game_id, self._pending_score, name)
        self._game_over = False
        self._phase = "play"
        self.app.state_machine.change("idle")
