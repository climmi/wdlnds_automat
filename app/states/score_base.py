import math
import pygame

from .. import config
from ..ui import draw_button_hints, draw_text
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
        self._name_hold = self._empty_name_hold()
        self._alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-!?*+")
        self._result_label = "GAME OVER"
        self._result_complete = False
        self._scoreboard_sound_started = False
        self._result_anim = 0.0

    def on_enter(self) -> None:
        self._game_over = False
        self._phase = "play"
        self._game_over_timer = 0.0
        self._fade = 0.0
        self._entry_timer = 0.0
        self._pending_score = 0
        self._name_chars = ["A", "A", "A"]
        self._name_index = 0
        self._name_hold = self._empty_name_hold()
        self._result_label = "GAME OVER"
        self._result_complete = False
        self._scoreboard_sound_started = False
        self._result_anim = 0.0
        self.on_game_start()

    def on_exit(self) -> None:
        self.app.sound.stop_scoreboard_loop()

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
                self._result_anim += dt
                if self._game_over_timer >= 2.0:
                    self._phase = "entry"
                    self._fade = 0.0
                    self._entry_timer = 0.0
                    if not self._scoreboard_sound_started:
                        self.app.sound.play_scoreboard_loop()
                        self._scoreboard_sound_started = True
            elif self._phase == "entry":
                self._fade = min(1.0, self._fade + dt * 2.2)
                self._entry_timer += dt
                self._update_name_entry(dt)
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
            draw_text(surface, "HIGH SCORE", title_font, config.COLOR_TEXT_DARK, (self.app.center_x, 120))
            self._render_scoreboard(surface, y=self.app.center_y - 120, include_pending=True)
            self._render_name_entry(surface)
            return

        self.render_game(surface)

        if self._game_over and self._phase == "gameover_wait":
            panel = pygame.Rect(self.app.center_x - 250, self.app.center_y - 52, 500, 104)
            pygame.draw.rect(surface, (255, 253, 240), panel, border_radius=12)
            pygame.draw.rect(surface, config.COLOR_TEXT_DARK, panel, width=2, border_radius=12)
            color = (89, 181, 96) if self._result_complete else config.COLOR_TEXT_DARK
            self._draw_result_text(surface, self._result_label, panel.center, color)

    def render_game(self, surface) -> None:
        pass

    def trigger_game_over(self, score: int, complete: bool = False) -> None:
        if self._game_over:
            return
        self._game_over = True
        self._phase = "gameover_wait"
        self._game_over_timer = 0.0
        self._result_anim = 0.0
        self._pending_score = int(score)
        self._result_complete = bool(complete)
        self._result_label = "COMPLETE!" if complete else "GAME OVER"
        if complete:
            self.app.sound.play_win()
        else:
            self.app.sound.play_game_over_early()

    def scoreboard_id(self) -> str:
        return self.game_id

    def scoreboard_title(self) -> str:
        return "Highscore Top 5"

    def _draw_result_text(self, surface, text: str, center, color) -> None:
        font = self.app.fonts["title"]
        render = font.render(text, True, color)
        if self._result_complete:
            pulse = 1.0 + 0.08 * math.sin(self._result_anim * 8.0)
            size = (max(1, int(render.get_width() * pulse)), max(1, int(render.get_height() * pulse)))
            render = pygame.transform.smoothscale(render, size)
        surface.blit(render, render.get_rect(center=center))

    def _handle_name_entry(self, pressed) -> None:
        if self._phase != "entry":
            return
        for control, index in (("left", 0), ("middle", 1), ("right", 2)):
            if control in pressed:
                self._name_index = index
                self._advance_name_char(index)
                self._name_hold[control] = {"held": 0.0, "next": 0.38}
                self._entry_timer = 0.0
        if "start" in pressed:
            self._finalize_score()

    def _update_name_entry(self, dt: float) -> None:
        for control, index in (("left", 0), ("middle", 1), ("right", 2)):
            if not self.app.buttons.is_down(control):
                self._name_hold[control] = {"held": 0.0, "next": 0.0}
                continue
            state = self._name_hold[control]
            state["held"] += dt
            if state["next"] <= 0.0:
                state["next"] = 0.38
                continue
            state["next"] -= dt
            if state["next"] > 0.0:
                continue
            self._name_index = index
            self._advance_name_char(index)
            interval = max(0.055, 0.22 - state["held"] * 0.075)
            state["next"] += interval
            self._entry_timer = 0.0

    def _advance_name_char(self, index: int) -> None:
        current = self._name_chars[index]
        idx = self._alphabet.index(current) if current in self._alphabet else 0
        self._name_chars[index] = self._alphabet[(idx + 1) % len(self._alphabet)]

    def _empty_name_hold(self):
        return {
            "left": {"held": 0.0, "next": 0.0},
            "middle": {"held": 0.0, "next": 0.0},
            "right": {"held": 0.0, "next": 0.0},
        }

    def _render_name_entry(self, surface) -> None:
        body_font = self.app.fonts["body"]
        slot_size = 54
        gap = 18
        total = slot_size * 3 + gap * 2
        start_x = self.app.center_x - total / 2
        y = self.app.center_y + 110
        for idx, ch in enumerate(self._name_chars):
            rect = pygame.Rect(int(start_x + idx * (slot_size + gap)), y, slot_size, slot_size)
            color = (255, 253, 240)
            pygame.draw.rect(surface, color, rect, border_radius=8)
            border = config.COLOR_TEXT_DARK if idx == self._name_index else (128, 118, 98)
            pygame.draw.rect(surface, border, rect, width=2, border_radius=8)
            draw_text(surface, ch, body_font, config.COLOR_TEXT_DARK, rect.center)
        draw_button_hints(
            surface,
            self.app,
            confirm=True,
            left=True,
            middle=True,
            right=True,
            confirm_label="BESTAETIGEN",
            left_label="BUCHSTABE 1",
            middle_label="BUCHSTABE 2",
            right_label="BUCHSTABE 3",
        )

    def _render_scoreboard(self, surface, y: int, include_pending: bool = False) -> None:
        body_font = self.app.fonts["body"]
        status = self.app.highscores.get_status(self.scoreboard_id())
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
        pygame.draw.rect(surface, (255, 253, 240), panel_rect, border_radius=12)
        pygame.draw.rect(surface, config.COLOR_TEXT_DARK, panel_rect, width=2, border_radius=12)
        title_y = panel_rect.top + pad_y
        if not entries:
            draw_text(surface, "Highscore: ---", body_font, config.COLOR_TEXT_DARK,
                      (self.app.center_x, title_y + title_h))
            return
        draw_text(surface, self.scoreboard_title(), body_font, config.COLOR_TEXT_DARK,
                  (self.app.center_x, title_y + title_h / 2))
        for idx, entry in enumerate(entries):
            line = f"{idx + 1}. {entry['name']}  {entry['score']}"
            color = config.COLOR_TEXT_DARK if include_pending and pending_index == idx else (92, 79, 56)
            draw_text(surface, line, body_font, color,
                      (self.app.center_x, title_y + title_h + row_h / 2 + idx * row_h))

    def _finalize_score(self) -> None:
        name = "".join(self._name_chars)
        self.app.sound.stop_scoreboard_loop()
        self.app.highscores.register_score(self.scoreboard_id(), self._pending_score, name)
        self._game_over = False
        self._phase = "play"
        self.app.state_machine.change("idle")
