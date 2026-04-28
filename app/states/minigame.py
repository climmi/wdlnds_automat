import math
import os
import random

import pygame

from .. import config
from ..storage import load_json
from ..ui import draw_text
from .score_base import ScoreGameState


class MiniGameState(ScoreGameState):
    game_id = "show_control"
    game_name = "Show Control"

    CONTROLS = {
        "left": ("MOVE", (75, 154, 225)),
        "middle": ("DROP", (245, 174, 57)),
        "right": ("FX", (235, 96, 78)),
    }
    CONTROL_ORDER = ["left", "middle", "right"]
    BEAT_INTERVAL = 0.68
    LEAD_TIME = 2.4
    PERFECT_WINDOW = 0.14
    GOOD_WINDOW = 0.30
    HOLD_RELEASE_GRACE = 0.16
    DJ_ACTS = [
        "Konfusia",
        "Maka",
        "Cocoloris",
        "Elbatos",
        "Papu",
        "Federkern",
        "ELS Music",
        "Doddy",
        "DJ KRSN",
        "Mischluft",
        "Sarah Wild",
        "Melbo & Falke",
        "Horst Haller",
        "Sinamin",
        "Carlo Bonanza",
        "Victor Ruiz",
        "Susi Paula",
        "Sabura",
        "Nina Ozono",
        "Madria",
        "Stacy 9_9",
        "Marlon Margiela",
        "Dub FX",
        "Flox",
        "Benjie",
        "Illbilly Hitec feat. Longfingah",
        "Luisa Laakmann",
        "Singing Gold",
        "Aio",
        "Tober&Tober",
    ]

    def __init__(self, app) -> None:
        super().__init__(app)
        self._time = 0.0
        self._duration = 0.0
        self._cues = []
        self._sections = []
        self._score = 0
        self._mood = 58.0
        self._combo = 0
        self._last_label = ""
        self._label_timer = 0.0
        self._flash = {key: 0.0 for key in self.CONTROL_ORDER}
        self._beat = 0
        self._last_beat = -1
        self._crowd_seed = []
        self._crowd_phase = 0.0
        self._crowd_level = 0.22
        self._crowd_level_target = 0.22
        self._dj_name = "Konfusia"
        self._beat_interval = self.BEAT_INTERVAL
        self._music_path = None

    def on_game_start(self) -> None:
        self._time = 0.0
        self._score = 0
        self._mood = 58.0
        self._combo = 0
        self._last_label = "LOS GEHTS"
        self._label_timer = 0.8
        self._flash = {key: 0.0 for key in self.CONTROL_ORDER}
        self._beat = 0
        self._last_beat = -1
        self._crowd_phase = 0.0
        self._crowd_level = 0.22
        self._crowd_level_target = 0.22
        self._dj_name = random.choice(self.DJ_ACTS)
        self._crowd_seed = self._build_crowd_seed()
        self._cues, self._sections, self._duration = self._build_show()
        if self._music_path:
            self.app.sound.play_music(self._music_path)

    def on_exit(self) -> None:
        self.app.sound.stop_music()

    def trigger_game_over(self, score: int) -> None:
        self.app.sound.stop_music()
        super().trigger_game_over(score)

    def handle_game_input(self, pressed):
        for control in self.CONTROL_ORDER:
            if control in pressed:
                self._flash[control] = 0.22
                self._trigger(control)
        if "start" in pressed:
            self._flash["middle"] = 0.22
            self._trigger("middle")

    def update_game(self, dt: float) -> None:
        self._time += dt
        self._crowd_phase += dt * (1.5 + self._mood / 45.0)
        self._update_crowd_level(dt)
        self._label_timer = max(0.0, self._label_timer - dt)
        for key in self._flash:
            self._flash[key] = max(0.0, self._flash[key] - dt)

        self._update_beat()
        self._mood = max(0.0, self._mood - dt * 0.42)

        for cue in self._cues:
            if cue["done"]:
                continue
            if cue.get("type") == "hold":
                self._update_hold_cue(cue)
                continue
            if self._time - cue["time"] > self.GOOD_WINDOW:
                cue["done"] = True
                self._register_miss("OOPS")

        if self._mood <= 0 or self._time >= self._duration:
            self.trigger_game_over(self._score)

    def render_game(self, surface) -> None:
        self._draw_level(surface)
        self._draw_header(surface)
        self._draw_people(surface)
        self._draw_note_lanes(surface)

    def _draw_level(self, surface) -> None:
        surface.fill((249, 246, 232))
        level = self.app.images.get("level_bg")
        if level:
            rect = level.get_rect(center=(self.app.center_x, self.app.center_y + 6))
            surface.blit(level, rect)
        else:
            pygame.draw.rect(surface, (210, 168, 105), (0, 176, self.app.width, self.app.height - 176))
            pygame.draw.rect(surface, (132, 186, 91), (0, 0, self.app.width, 190))

    def _draw_header(self, surface) -> None:
        top = pygame.Rect(24, 16, self.app.width - 48, 90)
        pygame.draw.rect(surface, (255, 253, 240), top, border_radius=12)
        pygame.draw.rect(surface, (75, 56, 38), top, width=2, border_radius=12)
        draw_text(surface, "DJ SET", self.app.fonts["title"], (75, 56, 38), (self.app.center_x, 36))
        act_name = self._dj_name.upper()
        draw_text(surface, act_name, self.app.fonts["body_bold"], (75, 56, 38), (self.app.center_x, 66))
        draw_text(
            surface,
            f"{self._section_name()} / SCORE {self._score} / STREAK {self._combo}",
            self.app.fonts["body"],
            (92, 79, 56),
            (self.app.center_x, 90),
        )

        meter = pygame.Rect(self.app.center_x - 210, 112, 420, 18)
        pygame.draw.rect(surface, (255, 253, 240), meter, border_radius=10)
        fill = meter.copy()
        fill.width = int(meter.width * (self._mood / 100.0))
        meter_color = (235, 96, 78) if self._mood < 35 else (245, 174, 57)
        if self._mood > 72:
            meter_color = (89, 181, 96)
        pygame.draw.rect(surface, meter_color, fill, border_radius=10)
        pygame.draw.rect(surface, (75, 56, 38), meter, width=2, border_radius=10)
        draw_text(surface, f"STIMMUNG {int(self._mood)}", self.app.fonts["body"], (75, 56, 38), meter.center)

        if self._label_timer > 0:
            label_rect = pygame.Rect(self.app.center_x - 82, 136, 164, 28)
            color = (89, 181, 96) if self._last_label in ("PERFEKT", "GUT", "YEAH") else (235, 96, 78)
            pygame.draw.rect(surface, (255, 253, 240), label_rect, border_radius=10)
            pygame.draw.rect(surface, color, label_rect, width=2, border_radius=10)
            draw_text(surface, self._last_label, self.app.fonts["body_bold"], color, label_rect.center)

    def _draw_people(self, surface) -> None:
        mood = self._crowd_mood()
        sprites = self.app.images.get("normie", {})
        sprite = sprites.get(mood)
        energy = self._movement_energy(mood)
        visible_people = self._visible_people()

        sorted_people = sorted(visible_people, key=lambda item: item["y"])
        for person in sorted_people:
            enter = self._enter_progress(person)
            base_x = person["start_x"] + (person["x"] - person["start_x"]) * enter
            base_y = person["start_y"] + (person["y"] - person["start_y"]) * enter
            bounce = int(math.sin(self._crowd_phase + person["phase"]) * person["amp"] * energy)
            sway = int(math.cos(self._crowd_phase * 0.8 + person["phase"]) * 5 * energy)
            x = int(base_x + sway * enter)
            y = int(base_y - bounce * enter)
            scale = person["scale"] * (0.88 + 0.12 * enter)
            if sprite:
                w = max(16, int(sprite.get_width() * scale))
                h = max(24, int(sprite.get_height() * scale))
                frame = pygame.transform.scale(sprite, (w, h))
                surface.blit(frame, frame.get_rect(midbottom=(x, y)))
            else:
                color = (89, 181, 96) if mood == "happy" else (88, 104, 124)
                if mood == "bored":
                    color = (130, 130, 122)
                pygame.draw.rect(surface, color, (x - 7, y - 24, 14, 24), border_radius=3)
                pygame.draw.circle(surface, (75, 56, 38), (x, y - 31), 7)

    def _draw_note_lanes(self, surface) -> None:
        top_y = 160
        target_y = self.app.height - 54
        exit_y = self.app.height + 24
        lane_w = 120
        centers = [self.app.center_x - 180, self.app.center_x, self.app.center_x + 180]
        for key, cx in zip(self.CONTROL_ORDER, centers):
            _, color = self.CONTROLS[key]
            lane = pygame.Rect(cx - lane_w // 2, top_y, lane_w, self.app.height - top_y)
            lane_overlay = pygame.Surface(lane.size, pygame.SRCALPHA)
            pygame.draw.rect(lane_overlay, (255, 253, 240, 58), lane_overlay.get_rect(), border_radius=12)
            pygame.draw.rect(lane_overlay, (75, 56, 38, 95), lane_overlay.get_rect(), width=2, border_radius=12)
            surface.blit(lane_overlay, lane.topleft)
            pygame.draw.line(surface, color, (cx, top_y + 12), (cx, self.app.height), 2)

        for key, cx in zip(self.CONTROL_ORDER, centers):
            _, color = self.CONTROLS[key]
            active = self._flash[key] > 0
            rect = pygame.Rect(cx - 60, target_y - 18, 120, 36)
            if active:
                pygame.draw.rect(surface, color, rect, border_radius=10)
            else:
                button_overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(button_overlay, (*color, 135), button_overlay.get_rect(), border_radius=10)
                surface.blit(button_overlay, rect.topleft)
            pygame.draw.rect(surface, (75, 56, 38), rect, width=2, border_radius=10)

        for cue in self._cues:
            if cue["done"]:
                continue
            delta = cue["time"] - self._time
            if delta < -self.GOOD_WINDOW or delta > self.LEAD_TIME:
                continue
            if delta >= 0:
                y = target_y - int((delta / self.LEAD_TIME) * (target_y - top_y))
            else:
                y = target_y + int((-delta / self.GOOD_WINDOW) * (exit_y - target_y))
            for control in self._cue_controls(cue):
                if control in cue.get("hit_controls", []) and not cue.get("active"):
                    continue
                _, color = self.CONTROLS[control]
                cx = centers[self.CONTROL_ORDER.index(control)]
                if cue.get("type") == "hold":
                    end_delta = cue["time"] + float(cue.get("duration", 0.0)) - self._time
                    if end_delta >= 0:
                        end_y = target_y - int((end_delta / self.LEAD_TIME) * (target_y - top_y))
                    else:
                        end_y = target_y + int((-end_delta / self.GOOD_WINDOW) * (exit_y - target_y))
                    top = min(y, end_y)
                    height = max(34, abs(end_y - y))
                    hold_rect = pygame.Rect(cx - 30, top, 60, height)
                    hold_surface = pygame.Surface(hold_rect.size, pygame.SRCALPHA)
                    pygame.draw.rect(hold_surface, (*color, 148), hold_surface.get_rect(), border_radius=8)
                    surface.blit(hold_surface, hold_rect.topleft)
                    pygame.draw.rect(surface, (75, 56, 38), hold_rect, width=2, border_radius=8)
                    rect = pygame.Rect(cx - 42, y - 17, 84, 34)
                else:
                    rect = pygame.Rect(cx - 42, y - 17, 84, 34)
                pygame.draw.rect(surface, color, rect, border_radius=8)
                pygame.draw.rect(surface, (75, 56, 38), rect, width=2, border_radius=8)

    def _trigger(self, control: str) -> None:
        candidates = [
            cue for cue in self._cues
            if control in self._cue_controls(cue)
            and control not in cue.get("hit_controls", [])
            and not cue["done"]
            and not cue.get("active")
        ]
        if not candidates:
            self._register_miss("FALSCH")
            return
        cue = min(candidates, key=lambda item: abs(item["time"] - self._time))
        delta = abs(cue["time"] - self._time)
        if cue.get("type") == "hold":
            if delta <= self.GOOD_WINDOW:
                self._start_hold_cue(cue, control)
            else:
                self._register_miss("DANEBEN")
            return
        if delta <= self.PERFECT_WINDOW:
            self._mark_cue_hit(cue, control)
            self._register_hit(24, 7.0, "PERFEKT")
        elif delta <= self.GOOD_WINDOW:
            self._mark_cue_hit(cue, control)
            self._register_hit(14, 4.0, "GUT")
        else:
            self._register_miss("DANEBEN")

    def _cue_controls(self, cue) -> list[str]:
        controls = cue.get("controls")
        if isinstance(controls, list):
            return [control for control in controls if control in self.CONTROL_ORDER]
        return [cue["control"]]

    def _mark_cue_hit(self, cue, control: str) -> None:
        hit_controls = cue.setdefault("hit_controls", [])
        if control not in hit_controls:
            hit_controls.append(control)
        if all(item in hit_controls for item in self._cue_controls(cue)):
            cue["done"] = True

    def _update_hold_cue(self, cue) -> None:
        if cue.get("active"):
            control = cue.get("held_control")
            end_time = cue["time"] + float(cue.get("duration", 0.0))
            grace_until = float(cue.get("release_grace_until", 0.0) or 0.0)
            if control and self._time > grace_until and not self._is_control_down(control):
                cue["done"] = True
                self._register_miss("LOSGELASSEN")
                return
            if self._time >= end_time:
                cue["done"] = True
                self._register_hit(34, 9.0, "GEHALTEN")
            return

        if abs(self._time - cue["time"]) <= self.GOOD_WINDOW:
            for control in self._cue_controls(cue):
                if self._is_control_down(control):
                    self._start_hold_cue(cue, control)
                    return

        if self._time - cue["time"] > self.GOOD_WINDOW:
            cue["done"] = True
            self._register_miss("OOPS")

    def _start_hold_cue(self, cue, control: str) -> None:
        cue["active"] = True
        cue["held_control"] = control
        cue["release_grace_until"] = self._time + self.HOLD_RELEASE_GRACE
        self._last_label = "HALTEN"
        self._label_timer = 0.35

    def _is_control_down(self, control: str) -> bool:
        if self.app.buttons.is_down(control):
            return True
        return control == "middle" and self.app.buttons.is_down("start")

    def _register_hit(self, points: int, mood_gain: float, label: str) -> None:
        self._combo += 1
        self._score += points + min(60, self._combo * 2)
        self._mood = min(100.0, self._mood + mood_gain)
        crowd_gain = 0.035 + min(0.065, self._combo * 0.006)
        self._crowd_level_target = min(1.0, self._crowd_level_target + crowd_gain)
        self._last_label = "YEAH" if self._combo and self._combo % 8 == 0 else label
        self._label_timer = 0.38

    def _register_miss(self, label: str) -> None:
        self._combo = 0
        self._mood = max(0.0, self._mood - 6.5)
        self._crowd_level_target = max(0.18, self._crowd_level_target - 0.04)
        self._last_label = label
        self._label_timer = 0.45

    def _crowd_mood(self) -> str:
        if self._mood < 35:
            return "bored"
        if self._combo >= 4 or self._mood > 74:
            return "happy"
        return "normal"

    def _movement_energy(self, mood: str) -> float:
        if mood == "bored":
            return 0.18
        if mood == "happy":
            return 1.15
        return 0.55

    def _visible_people(self):
        if not self._crowd_seed:
            return []
        threshold = self._crowd_level
        visible = [person for person in self._crowd_seed if person["join"] <= threshold]
        minimum = min(6, len(self._crowd_seed))
        if len(visible) < minimum:
            return self._crowd_seed[:minimum]
        return visible

    def _enter_progress(self, person) -> float:
        span = 0.14
        progress = (self._crowd_level - person["join"]) / span
        return max(0.0, min(1.0, progress))

    def _update_crowd_level(self, dt: float) -> None:
        if self._crowd_level == self._crowd_level_target:
            return
        direction = 1.0 if self._crowd_level_target > self._crowd_level else -1.0
        speed = 0.22 if direction > 0 else 0.18
        self._crowd_level += direction * speed * dt
        if (direction > 0 and self._crowd_level > self._crowd_level_target) or (
            direction < 0 and self._crowd_level < self._crowd_level_target
        ):
            self._crowd_level = self._crowd_level_target

    def _next_cue(self):
        upcoming = [cue for cue in self._cues if not cue["done"] and cue["time"] >= self._time - self.GOOD_WINDOW]
        if not upcoming:
            return None
        return min(upcoming, key=lambda item: item["time"])

    def _section_name(self) -> str:
        for section in self._sections:
            start, end, name = section[:3]
            if start <= self._time < end:
                return name
        return self._sections[-1][2] if self._sections else "FLOOR"

    def _update_beat(self) -> None:
        beat = int(self._time / self._beat_interval)
        if beat == self._last_beat:
            return
        self._last_beat = beat
        self._beat = beat % 4

    def _build_show(self):
        analyzed = self._load_analyzed_show()
        if analyzed:
            return analyzed

        self._music_path = None
        self._beat_interval = self.BEAT_INTERVAL
        patterns = [
            ("ANKOMMEN", 5, ["left", "right", "middle"]),
            ("TANZEN", 6, ["left", "middle", "right", "left"]),
            ("DROP", 8, ["middle", "left", "right", "middle", "right"]),
            ("SONNE", 7, ["left", "right", "middle", "left", "middle", "right"]),
        ]
        cues = []
        sections = []
        time_pos = 1.0
        for name, bars, pattern in patterns:
            section_start = time_pos
            for bar in range(bars):
                for idx, control in enumerate(pattern):
                    beat_offset = (idx + 1) * (4.0 / (len(pattern) + 1))
                    cues.append({
                        "time": round(time_pos + beat_offset * self._beat_interval, 3),
                        "control": control,
                        "controls": [control],
                        "type": "tap",
                        "duration": 0.0,
                        "done": False,
                    })
                if name in ("DROP", "SONNE") and bar % 2 == 1:
                    cues.append({
                        "time": round(time_pos + 3.72 * self._beat_interval, 3),
                        "control": "middle",
                        "controls": ["middle"],
                        "type": "tap",
                        "duration": 0.0,
                        "done": False,
                    })
                time_pos += self._beat_interval * 4
            sections.append((section_start, time_pos, name))
            time_pos += 0.35
        cues.sort(key=lambda item: item["time"])
        return cues, sections, time_pos + 0.8

    def _load_analyzed_show(self):
        path = os.path.join(config.DATA_DIR, "show_cues.json")
        payload = load_json(path, None)
        if not payload or not isinstance(payload, dict):
            return None

        cues = []
        for item in payload.get("cues", []):
            try:
                time_pos = float(item["time"])
                raw_controls = item.get("controls", [item.get("control")])
            except (KeyError, TypeError, ValueError):
                continue
            if not isinstance(raw_controls, list):
                raw_controls = [raw_controls]
            controls = [str(control) for control in raw_controls if str(control) in self.CONTROL_ORDER]
            if not controls:
                continue
            cues.append({
                "time": round(time_pos, 3),
                "control": controls[0],
                "controls": controls,
                "type": str(item.get("type", "tap")),
                "duration": float(item.get("duration", 0.0) or 0.0),
                "done": False,
            })
        cues = self._remove_hold_lane_conflicts(cues)
        if not cues:
            return None

        bpm = float(payload.get("bpm", 0) or 0)
        self._beat_interval = 60.0 / bpm if bpm > 0 else self.BEAT_INTERVAL

        sections = []
        for item in payload.get("sections", []):
            try:
                start, end, name = item[:3]
                sections.append((float(start), float(end), str(name)))
            except (TypeError, ValueError):
                continue

        duration = float(payload.get("duration", cues[-1]["time"] + 1.0))
        if not sections:
            sections = [(0.0, duration, "SET")]

        source = str(payload.get("source", ""))
        music_path = os.path.abspath(os.path.join(config.BASE_DIR, os.pardir, "audio", source))
        self._music_path = music_path if source and os.path.exists(music_path) else None
        return cues, sections, duration

    def _remove_hold_lane_conflicts(self, cues):
        cleaned = []
        hold_windows = {control: [] for control in self.CONTROL_ORDER}
        margin = 0.05

        for cue in sorted(cues, key=lambda item: item["time"]):
            cue_time = float(cue["time"])
            controls = [control for control in self._cue_controls(cue) if control in self.CONTROL_ORDER]
            if not controls:
                continue

            blocked = {
                control
                for control in controls
                for start, end in hold_windows.get(control, [])
                if start - margin < cue_time < end + margin
            }

            if cue.get("type") == "hold":
                if blocked:
                    continue
                duration = float(cue.get("duration", 0.0) or 0.0)
                for control in controls:
                    hold_windows[control].append((cue_time, cue_time + duration))
                cleaned.append(cue)
                continue

            controls = [control for control in controls if control not in blocked]
            if not controls:
                continue
            cue["controls"] = controls
            cue["control"] = controls[0]
            cleaned.append(cue)

        return cleaned

    def _build_crowd_seed(self):
        rng = random.Random(31)
        clusters = [
            (326, 438, 6, 0.12),
            (546, 424, 6, 0.13),
            (746, 444, 6, 0.14),
            (414, 500, 10, 0.25),
            (642, 504, 10, 0.31),
            (276, 528, 10, 0.40),
            (810, 526, 10, 0.46),
            (502, 552, 14, 0.56),
            (658, 558, 14, 0.66),
            (366, 566, 12, 0.76),
            (760, 566, 12, 0.86),
        ]
        spots = []
        for cx, cy, count, join_start in clusters:
            for idx in range(count):
                angle = (idx / max(1, count)) * math.tau + rng.uniform(-0.25, 0.25)
                radius_x = rng.randrange(18, 78)
                radius_y = rng.randrange(10, 34)
                x = cx + int(math.cos(angle) * radius_x)
                y = cy + int(math.sin(angle) * radius_y)
                y = max(392, min(570, y))
                depth = (y - 392) / (570 - 392)
                scale = 1.28 + depth * 0.72 + rng.uniform(-0.06, 0.08)
                join = min(1.0, join_start + idx * 0.008 + rng.uniform(0.0, 0.045))
                side_left = (len(spots) + idx) % 2 == 0
                start_x = -70 if side_left else self.app.width + 70
                start_y = self.app.height + rng.randrange(8, 72)
                spots.append((x, y, scale, join, start_x, start_y))
        spots.sort(key=lambda item: item[3])
        people = []
        for x, y, scale, join, start_x, start_y in spots:
            target_x = x + rng.randrange(-8, 9)
            target_y = y + rng.randrange(-5, 6)
            if join <= 0.22:
                start_x = target_x
                start_y = target_y
            people.append({
                "x": target_x,
                "y": target_y,
                "start_x": start_x,
                "start_y": start_y,
                "scale": scale,
                "join": join,
                "phase": rng.random() * math.tau,
                "amp": rng.randrange(4, 11),
            })
        return people
