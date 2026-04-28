import random
import pygame

from .. import config
from ..ui import draw_glow_panel, draw_glow_text, draw_text
from .score_base import ScoreGameState


class HoldGameState(ScoreGameState):
    game_id = "crowd_control"
    game_name = "Crowd Control"

    def __init__(self, app) -> None:
        super().__init__(app)
        self._score = 0
        self._hype = 100.0
        self._combo = 0
        self._events = []
        self._event_index = 0
        self._active = None
        self._event_time = 0.0
        self._last_label = ""
        self._label_timer = 0.0
        self._crowd_phase = 0.0

    def on_game_start(self) -> None:
        self._score = 0
        self._hype = 100.0
        self._combo = 0
        self._event_index = 0
        self._events = self._build_events()
        self._active = self._events[0] if self._events else None
        self._event_time = 0.0
        self._last_label = "CROWD READY"
        self._label_timer = 0.7
        self._crowd_phase = 0.0

    def handle_game_input(self, pressed):
        if not self._active:
            return
        self._handle_active_input(pressed)

    def update_game(self, dt: float) -> None:
        self._crowd_phase += dt * 2.0
        self._label_timer = max(0.0, self._label_timer - dt)

        if not self._active:
            self.trigger_game_over(self._score)
            return

        self._event_time += dt
        if self._event_time > self._active["duration"]:
            if self._event_success():
                self._finish_event(True)
            else:
                self._finish_event(False)
                if self._hype <= 0:
                    self.trigger_game_over(self._score)

    def render_game(self, surface) -> None:
        self.app.draw_background(surface)
        draw_glow_text(surface, "CROWD CONTROL", self.app.fonts["title"], config.COLOR_TEXT,
                       (self.app.center_x, 90), config.COLOR_ACCENT_HOT, glow_radius=4)
        draw_text(surface, f"HYPE {int(self._hype)}  /  COMBO {self._combo}",
                  self.app.fonts["body"], config.COLOR_TEXT_SOFT, (self.app.center_x, 124))
        self._draw_crowd(surface)
        self._draw_event_panel(surface)
        draw_text(surface, f"SCORE {self._score}", self.app.fonts["body"], config.COLOR_TEXT,
                  (self.app.center_x, self.app.height - 28))

    def _draw_crowd(self, surface) -> None:
        field = pygame.Rect(80, 156, self.app.width - 160, 184)
        draw_glow_panel(surface, field, (14, 17, 25), config.COLOR_BG_GRID, config.COLOR_BG_GRID, border=1)
        center_x = field.centerx
        center_y = field.bottom - 30
        action = self._active["kind"] if self._active else "hands"
        progress = min(1.0, self._event_time / max(0.001, self._active["duration"])) if self._active else 0.0

        for row in range(4):
            for col in range(14):
                x = field.left + 44 + col * 44
                y = field.top + 52 + row * 28
                width = 12
                height = 12
                offset_x = 0
                offset_y = 0

                if action == "hands":
                    offset_y = -int(10 * (0.5 + 0.5 * ((col + row) % 2)))
                elif action == "drop":
                    offset_y = int(10 * progress) if progress < 0.7 else -int(20 * (progress - 0.7) * 3.3)
                elif action == "split":
                    direction = -1 if x < center_x else 1
                    offset_x = int(direction * 30 * progress)
                elif action == "circle_left":
                    offset_x = int(-16 * progress)
                    offset_y = int(8 * ((col + row) % 2))
                elif action == "circle_right":
                    offset_x = int(16 * progress)
                    offset_y = int(8 * ((col + row) % 2))

                pygame.draw.rect(surface, config.COLOR_TEXT, (x + offset_x, y + offset_y, width, height), border_radius=3)

        pygame.draw.rect(surface, (28, 34, 40), (field.left + 12, field.bottom - 18, field.width - 24, 8), border_radius=4)

    def _draw_event_panel(self, surface) -> None:
        panel = pygame.Rect(160, 366, self.app.width - 320, 110)
        draw_glow_panel(surface, panel, (11, 14, 21), config.COLOR_BG_GRID, config.COLOR_BG_GRID, border=1)
        if not self._active:
            return
        action_names = {
            "hands": "HANDS UP",
            "drop": "SQUAT DROP",
            "split": "WALL OF DEATH",
            "circle_left": "CIRCLE PIT L",
            "circle_right": "CIRCLE PIT R",
        }
        hint_names = {
            "hands": "PRESS LEFT RIGHT LEFT RIGHT",
            "drop": "PRESS MIDDLE EARLY, THEN MIDDLE AT DROP",
            "split": "PRESS LEFT THEN RIGHT",
            "circle_left": "MASH L",
            "circle_right": "MASH R",
        }
        draw_glow_text(surface, action_names[self._active["kind"]], self.app.fonts["big"], config.COLOR_TEXT,
                       (panel.centerx, panel.top + 28), config.COLOR_ACCENT_HOT, glow_radius=3)
        draw_text(surface, hint_names[self._active["kind"]], self.app.fonts["body"], config.COLOR_TEXT_SOFT,
                  (panel.centerx, panel.top + 62))
        progress_rect = pygame.Rect(panel.left + 28, panel.bottom - 26, panel.width - 56, 12)
        pygame.draw.rect(surface, (8, 10, 14), progress_rect, border_radius=6)
        fill = progress_rect.copy()
        fill.width = int(progress_rect.width * min(1.0, self._event_time / self._active["duration"]))
        pygame.draw.rect(surface, config.COLOR_ACCENT_GOLD, fill, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), progress_rect, width=1, border_radius=6)
        self._draw_input_guide(surface, panel)
        if self._label_timer > 0:
            draw_text(surface, self._last_label, self.app.fonts["body"], config.COLOR_TEXT,
                      (self.app.center_x, panel.bottom + 20))

    def _draw_input_guide(self, surface, panel: pygame.Rect) -> None:
        if not self._active:
            return
        guide_rect = pygame.Rect(panel.left + 24, panel.top + 76, panel.width - 48, 20)
        action = self._active["kind"]
        centers = [guide_rect.left + 80, guide_rect.centerx, guide_rect.right - 80]
        labels = ["L", "M", "R"]
        active_index = None
        if action == "hands":
            progress = min(self._active["progress"], len(self._active["pattern"]) - 1)
            active_index = {"left": 0, "right": 2}[self._active["pattern"][progress]]
        elif action == "drop":
            active_index = 1
        elif action == "split":
            progress = min(self._active["progress"], len(self._active["pattern"]) - 1)
            active_index = {"left": 0, "right": 2}[self._active["pattern"][progress]]
        elif action == "circle_left":
            active_index = 0
        elif action == "circle_right":
            active_index = 2
        for idx, cx in enumerate(centers):
            color = config.COLOR_ACCENT_GOLD if idx == active_index else config.COLOR_BG_GRID
            rect = pygame.Rect(cx - 28, guide_rect.top, 56, 18)
            pygame.draw.rect(surface, color, rect, border_radius=8)
            pygame.draw.rect(surface, (255, 255, 255), rect, width=1, border_radius=8)
            draw_text(surface, labels[idx], self.app.fonts["body"], config.COLOR_TEXT_DARK if idx == active_index else config.COLOR_TEXT_SOFT, rect.center)

    def _handle_active_input(self, pressed) -> None:
        kind = self._active["kind"]
        state = self._active["state"]

        if kind == "hands":
            if self._active["progress"] >= len(self._active["pattern"]):
                if pressed:
                    self._active["errors"] += 1
                return
            expected = self._active["pattern"][self._active["progress"]]
            if expected in pressed:
                self._active["progress"] += 1
            elif pressed:
                self._active["errors"] += 1
        elif kind == "drop":
            if state == "prep" and "middle" in pressed:
                self._active["state"] = "armed"
            elif state == "armed" and self._event_time >= self._active["drop_time"] and "middle" in pressed:
                self._active["state"] = "done"
            elif pressed:
                self._active["errors"] += 1
        elif kind == "split":
            if self._active["progress"] >= len(self._active["pattern"]):
                if pressed:
                    self._active["errors"] += 1
                return
            expected = self._active["pattern"][self._active["progress"]]
            if expected in pressed:
                self._active["progress"] += 1
            elif pressed:
                self._active["errors"] += 1
        elif kind == "circle_left":
            if "left" in pressed:
                self._active["progress"] += 1
            elif pressed:
                self._active["errors"] += 1
        elif kind == "circle_right":
            if "right" in pressed:
                self._active["progress"] += 1
            elif pressed:
                self._active["errors"] += 1

    def _event_success(self) -> bool:
        kind = self._active["kind"]
        if kind == "hands":
            return self._active["progress"] >= len(self._active["pattern"]) and self._active["errors"] == 0
        if kind == "drop":
            return self._active["state"] == "done" and self._active["errors"] == 0
        if kind == "split":
            return self._active["progress"] >= len(self._active["pattern"]) and self._active["errors"] == 0
        return self._active["progress"] >= self._active["target"] and self._active["errors"] <= 1

    def _finish_event(self, success: bool) -> None:
        if success:
            self._combo += 1
            self._score += 28 + min(55, self._combo * 2)
            self._hype = min(100.0, self._hype + 4.5)
            self._last_label = "HYPE"
        else:
            self._combo = 0
            self._hype = max(0.0, self._hype - 12.0)
            self._last_label = "CROWD LOST"
        self._label_timer = 0.45
        self._event_index += 1
        if self._event_index >= len(self._events):
            self._active = None
            return
        self._active = self._events[self._event_index]
        self._event_time = 0.0

    def _build_events(self):
        rng = random.Random(11)
        events = []
        kinds = ["hands", "drop", "split", "circle_left", "circle_right"]
        for idx in range(12):
            kind = kinds[idx % len(kinds)] if idx < 5 else rng.choice(kinds)
            if kind == "hands":
                events.append({"kind": kind, "duration": 2.0, "pattern": ["left", "right", "left", "right"], "progress": 0, "errors": 0, "state": "run"})
            elif kind == "drop":
                events.append({"kind": kind, "duration": 2.2, "drop_time": 1.45, "progress": 0, "errors": 0, "state": "prep"})
            elif kind == "split":
                events.append({"kind": kind, "duration": 2.0, "pattern": ["left", "right"], "progress": 0, "errors": 0, "state": "run"})
            elif kind == "circle_left":
                events.append({"kind": kind, "duration": 1.8, "target": 4, "progress": 0, "errors": 0, "state": "run"})
            else:
                events.append({"kind": kind, "duration": 1.8, "target": 4, "progress": 0, "errors": 0, "state": "run"})
        return events
