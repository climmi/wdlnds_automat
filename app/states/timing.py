import random
import pygame

from .. import config
from ..ui import draw_glow_panel, draw_glow_text, draw_text
from .score_base import ScoreGameState


class TimingGameState(ScoreGameState):
    game_id = "light_ops"
    game_name = "Light Ops"

    CUE_TYPES = [
        ("left", "HEADS L", config.COLOR_ACCENT_CYAN),
        ("middle", "BLINDER", config.COLOR_ACCENT_GOLD),
        ("right", "LED FX", config.COLOR_ACCENT_HOT),
    ]

    def __init__(self, app) -> None:
        super().__init__(app)
        self._timeline = 0.0
        self._duration = 0.0
        self._cues = []
        self._sections = []
        self._score = 0
        self._show_energy = 100.0
        self._combo = 0
        self._flash = {"left": 0.0, "middle": 0.0, "right": 0.0}
        self._last_label = ""
        self._label_timer = 0.0

    def on_game_start(self) -> None:
        self._timeline = 0.0
        self._score = 0
        self._show_energy = 100.0
        self._combo = 0
        self._flash = {"left": 0.0, "middle": 0.0, "right": 0.0}
        self._last_label = "STANDBY"
        self._label_timer = 0.7
        self._cues, self._sections, self._duration = self._build_show()

    def handle_game_input(self, pressed):
        for lane, _, _ in self.CUE_TYPES:
            if lane in pressed:
                self._flash[lane] = 0.22
                self._trigger_lane(lane)
        if "start" in pressed:
            self._flash["middle"] = 0.22
            self._trigger_lane("middle")

    def update_game(self, dt: float) -> None:
        self._timeline += dt
        self._label_timer = max(0.0, self._label_timer - dt)
        for lane in self._flash:
            self._flash[lane] = max(0.0, self._flash[lane] - dt)

        for cue in self._cues:
            if cue["done"]:
                continue
            if self._timeline - cue["time"] > 0.16:
                cue["done"] = True
                self._register_miss("MISSED CUE")

        if self._show_energy <= 0:
            self.trigger_game_over(self._score)
            return
        if self._timeline >= self._duration:
            self.trigger_game_over(self._score)

    def render_game(self, surface) -> None:
        self.app.draw_background(surface)
        draw_glow_text(surface, "LIGHT OPS", self.app.fonts["title"], config.COLOR_TEXT,
                       (self.app.center_x, 88), config.COLOR_ACCENT_GOLD, glow_radius=4)
        draw_text(surface, f"{self._current_section_name()}  /  SHOW ENERGY {int(self._show_energy)}  /  COMBO {self._combo}",
                  self.app.fonts["body"], config.COLOR_TEXT_SOFT, (self.app.center_x, 122))

        self._draw_stage(surface)
        self._draw_timeline(surface)
        draw_text(surface, f"SCORE {self._score}", self.app.fonts["body"], config.COLOR_TEXT, (self.app.center_x, self.app.height - 28))

    def _draw_stage(self, surface) -> None:
        stage_rect = pygame.Rect(110, 154, self.app.width - 220, 170)
        draw_glow_panel(surface, stage_rect, (13, 17, 24), config.COLOR_BG_GRID, config.COLOR_BG_GRID, border=1)
        crowd_rect = pygame.Rect(stage_rect.left + 24, stage_rect.bottom - 48, stage_rect.width - 48, 26)
        for idx in range(18):
            x = crowd_rect.left + idx * 24
            h = 8 + (idx % 3) * 6
            pygame.draw.rect(surface, config.COLOR_TEXT_SOFT, (x, crowd_rect.bottom - h, 12, h), border_radius=3)

        left_alpha = int(180 * self._flash["left"])
        mid_alpha = int(180 * self._flash["middle"])
        right_alpha = int(180 * self._flash["right"])
        if left_alpha:
            pygame.draw.polygon(surface, (*config.COLOR_ACCENT_CYAN, left_alpha),
                                [(stage_rect.left + 80, stage_rect.top + 18), (stage_rect.left + 180, stage_rect.bottom - 30), (stage_rect.left + 24, stage_rect.bottom - 30)])
        if mid_alpha:
            pygame.draw.rect(surface, config.COLOR_ACCENT_GOLD, (stage_rect.centerx - 22, stage_rect.top + 18, 44, 92), border_radius=8)
            pygame.draw.rect(surface, (255, 255, 255), (stage_rect.centerx - 22, stage_rect.top + 18, 44, 92), width=2, border_radius=8)
        if right_alpha:
            pygame.draw.polygon(surface, (*config.COLOR_ACCENT_HOT, right_alpha),
                                [(stage_rect.right - 80, stage_rect.top + 18), (stage_rect.right - 180, stage_rect.bottom - 30), (stage_rect.right - 24, stage_rect.bottom - 30)])

        draw_text(surface, "HEADS", self.app.fonts["body"], config.COLOR_ACCENT_CYAN, (stage_rect.left + 86, stage_rect.top + 24))
        draw_text(surface, "DROP", self.app.fonts["body"], config.COLOR_ACCENT_GOLD, (stage_rect.centerx, stage_rect.top + 24))
        draw_text(surface, "LED", self.app.fonts["body"], config.COLOR_ACCENT_HOT, (stage_rect.right - 86, stage_rect.top + 24))

        if self._label_timer > 0:
            draw_glow_text(surface, self._last_label, self.app.fonts["body"], config.COLOR_TEXT,
                           (self.app.center_x, stage_rect.bottom + 20), config.COLOR_ACCENT_GOLD, glow_radius=3)

    def _draw_timeline(self, surface) -> None:
        line_rect = pygame.Rect(110, 366, self.app.width - 220, 120)
        draw_glow_panel(surface, line_rect, (12, 16, 24), config.COLOR_BG_GRID, config.COLOR_BG_GRID, border=1)
        lane_y = {
            "left": line_rect.top + 28,
            "middle": line_rect.top + 58,
            "right": line_rect.top + 88,
        }
        for lane, label, color in self.CUE_TYPES:
            pygame.draw.line(surface, color, (line_rect.left + 24, lane_y[lane]), (line_rect.right - 24, lane_y[lane]), 2)
            draw_text(surface, label, self.app.fonts["body"], color, (line_rect.left + 68, lane_y[lane] - 12))

        target_x = line_rect.centerx + 90
        pygame.draw.line(surface, (255, 255, 255), (target_x, line_rect.top + 18), (target_x, line_rect.bottom - 14), 3)
        for cue in self._cues:
            if cue["done"]:
                continue
            delta = cue["time"] - self._timeline
            if delta < -0.2 or delta > 2.4:
                continue
            x = target_x + int(delta * 180)
            y = lane_y[cue["lane"]]
            rect = pygame.Rect(x - 16, y - 12, 32, 24)
            pygame.draw.rect(surface, cue["color"], rect, border_radius=8)
            pygame.draw.rect(surface, (255, 255, 255), rect, width=2, border_radius=8)

    def _trigger_lane(self, lane: str) -> None:
        hit_window_perfect = 0.10
        hit_window_good = 0.18
        candidates = [cue for cue in self._cues if cue["lane"] == lane and not cue["done"]]
        if not candidates:
            self._register_miss("WRONG")
            return
        cue = min(candidates, key=lambda item: abs(item["time"] - self._timeline))
        delta = abs(cue["time"] - self._timeline)
        if delta <= hit_window_perfect:
            cue["done"] = True
            self._register_hit(18, "PERFECT")
        elif delta <= hit_window_good:
            cue["done"] = True
            self._register_hit(10, "GOOD")
        else:
            self._register_miss("EARLY")

    def _register_hit(self, points: int, label: str) -> None:
        self._combo += 1
        self._score += points + min(45, self._combo // 3)
        self._show_energy = min(100.0, self._show_energy + 2.4)
        self._last_label = label
        self._label_timer = 0.35

    def _register_miss(self, label: str) -> None:
        self._combo = 0
        self._show_energy = max(0.0, self._show_energy - 9.0)
        self._last_label = label
        self._label_timer = 0.45

    def _current_section_name(self) -> str:
        for start, end, name in self._sections:
            if start <= self._timeline < end:
                return name
        return self._sections[-1][2] if self._sections else "SHOW"

    def _build_show(self):
        rng = random.Random(8)
        cues = []
        sections = []
        time_pos = 0.8
        structure = [
            ("CHECK", 6, 0.82),
            ("BUILD", 8, 0.62),
            ("DROP", 10, 0.46),
        ]
        order = ["left", "right", "middle"]
        for name, beats, spacing in structure:
            start = time_pos
            for beat in range(beats):
                lane = order[(beat + rng.randrange(0, 1 if name == "CHECK" else 2)) % 3]
                color = next(color for key, _, color in self.CUE_TYPES if key == lane)
                cues.append({"time": round(time_pos, 3), "lane": lane, "color": color, "done": False})
                if name == "DROP" and beat % 5 == 4:
                    cues.append({"time": round(time_pos + spacing * 0.45, 3), "lane": "middle", "color": config.COLOR_ACCENT_GOLD, "done": False})
                time_pos += spacing
            sections.append((start, time_pos, name))
            time_pos += 0.45
        cues.sort(key=lambda item: item["time"])
        return cues, sections, time_pos + 0.8
