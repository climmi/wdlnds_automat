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
    HOLD_RELEASE_WINDOW = 0.46
    HOLD_AUTO_COMPLETE_DELAY = 0.36
    SONG_INTRO_NO_CUES = 2.0
    MAX_VISIBLE_PEOPLE = 72
    MOOD_DECAY = 0.56
    COMBO_THRESHOLDS = (3, 8, 15, 25)
    DIFFICULTY_RULES = {
        "easy": {"start_mood": 58.0, "mood_decay": 0.42, "miss_penalty": 5.0, "crowd_loss": 0.03},
        "medium": {"start_mood": 52.0, "mood_decay": 0.68, "miss_penalty": 8.0, "crowd_loss": 0.055},
        "hard": {"start_mood": 46.0, "mood_decay": 0.86, "miss_penalty": 11.0, "crowd_loss": 0.075},
    }
    LEVEL_SCORE_IDS = {
        "easy": "show_control_waldwinkel",
        "medium": "show_control_zob",
        "hard": "show_control_marktplatz",
    }
    LEVEL_IMAGES = {
        "easy": "Waldwinkel 01.png",
        "medium": "ZOB 01.png",
        "hard": "Marktplatz 01.png",
    }
    DJ_ACTS = [
        "Konfluxia",
        "Mako",
        "Cocoluma",
        "Elbarto",
        "Pabu",
        "Felderkern",
        "ELX Sounds",
        "Dotto",
        "DJ KRSX",
        "Nebelluft",
        "Sira Wald",
        "Melbo & Finke",
        "Hurst Haller",
        "Sinamoon",
        "Carlo Bonaro",
        "Vektor Ruiz",
        "Susi Pola",
        "Saburo",
        "Nina Osono",
        "Madrio",
        "Stacy 8_8",
        "Marlon Marea",
        "Dub Fuzz",
        "Flux",
        "Bendji",
        "Hillbilly HiFi feat. Longfinger",
        "Luisa Lakuna",
        "Singing Stone",
        "Ayo",
        "Tober & Tabor",
    ]

    def __init__(self, app) -> None:
        super().__init__(app)
        self._time = 0.0
        self._duration = 0.0
        self._cues = []
        self._sections = []
        self._score = 0
        self._mood = 52.0
        self._combo = 0
        self._last_label = ""
        self._label_timer = 0.0
        self._flash = {key: 0.0 for key in self.CONTROL_ORDER}
        self._button_feedback = {key: {"timer": 0.0, "label": "", "color": (255, 253, 240)} for key in self.CONTROL_ORDER}
        self._beat = 0
        self._last_beat = -1
        self._crowd_seed = []
        self._crowd_phase = 0.0
        self._crowd_level = 0.22
        self._crowd_level_target = 0.22
        self._dj_name = "Konfluxia"
        self._beat_interval = self.BEAT_INTERVAL
        self._music_path = None
        self._led_timer = 0.0
        self._song_option = {
            "label": "WALDWINKEL",
            "location": "waldwinkel",
            "difficulty": "easy",
            "level_image": "Waldwinkel 01.png",
        }
        self._crowd_by_depth = []
        self._sprite_cache = {}
        self._last_combo_sound_level = 0

    def on_game_start(self) -> None:
        self._time = 0.0
        self._score = 0
        self._song_option = getattr(self.app, "selected_song", self._song_option)
        self._mood = self._difficulty_rules()["start_mood"]
        self._combo = 0
        self._last_label = "LOS GEHTS"
        self._label_timer = 0.8
        self._flash = {key: 0.0 for key in self.CONTROL_ORDER}
        self._button_feedback = {key: {"timer": 0.0, "label": "", "color": (255, 253, 240)} for key in self.CONTROL_ORDER}
        self._beat = 0
        self._last_beat = -1
        self._crowd_phase = 0.0
        self._crowd_level = 0.22
        self._crowd_level_target = 0.22
        self._dj_name = random.choice(self.DJ_ACTS)
        self._crowd_seed = self._build_crowd_seed()
        self._crowd_by_depth = sorted(self._crowd_seed, key=lambda item: item["y"])
        self._sprite_cache = {}
        self._last_combo_sound_level = 0
        self._cues, self._sections, self._duration = self._build_show()
        self._led_timer = 0.0
        self.app.esp32.send("MODE game")
        if self._music_path:
            self.app.sound.play_music(self._music_path)

    def on_exit(self) -> None:
        self.app.sound.stop_music()
        self.app.esp32.send("MODE standby")

    def trigger_game_over(self, score: int, complete: bool = False) -> None:
        self.app.sound.stop_music()
        self.app.esp32.send("MODE standby")
        super().trigger_game_over(score, complete=complete)

    def scoreboard_id(self) -> str:
        difficulty = str(self._song_option.get("difficulty", "medium"))
        return self.LEVEL_SCORE_IDS.get(difficulty, "show_control_zob")

    def scoreboard_title(self) -> str:
        label = str(self._song_option.get("label", "ZOB")).upper()
        return f"{label} TOP 5"

    def handle_game_input(self, pressed):
        for control in self.CONTROL_ORDER:
            if control in pressed:
                self._flash[control] = 0.22
                self.app.esp32.send(f"LED flash {control}")
                self._trigger(control)
        if "start" in pressed:
            self._flash["middle"] = 0.22
            self.app.esp32.send("LED flash middle")
            self._trigger("middle")

    def update_game(self, dt: float) -> None:
        self._time += dt
        self._crowd_phase += dt * (1.5 + self._mood / 45.0)
        self._update_crowd_level(dt)
        self._label_timer = max(0.0, self._label_timer - dt)
        for key in self._flash:
            self._flash[key] = max(0.0, self._flash[key] - dt)
        for feedback in self._button_feedback.values():
            feedback["timer"] = max(0.0, float(feedback["timer"]) - dt)

        self._update_beat()
        self._mood = max(0.0, self._mood - dt * self._difficulty_rules()["mood_decay"])
        self._update_led_feedback(dt)

        for cue in self._cues:
            if cue["done"]:
                continue
            if cue.get("type") == "hold":
                self._update_hold_cue(cue)
                continue
            if self._time - cue["time"] > self.GOOD_WINDOW:
                cue["done"] = True
                self._register_miss("ZU SPAET", self._cue_controls(cue))

        if self._mood <= 0:
            self.trigger_game_over(self._score, complete=False)
            return

        if self._time >= self._duration:
            self.trigger_game_over(self._score, complete=True)

    def _update_led_feedback(self, dt: float) -> None:
        self._led_timer += dt
        if self._led_timer < 0.09:
            return
        self._led_timer = 0.0

        lane_state = {
            control: {"position": 0, "intensity": 0, "prompt": 255 if self._flash[control] > 0 else 0}
            for control in self.CONTROL_ORDER
        }

        for cue in self._cues:
            if cue["done"]:
                continue
            active_hold = cue.get("type") == "hold" and cue.get("active")
            delta = cue["time"] - self._time
            if not active_hold and (delta < -self.GOOD_WINDOW or delta > self.LEAD_TIME):
                continue

            if active_hold:
                position = 100
                intensity = 210
                prompt = 255
            else:
                position = max(0, min(100, int((1.0 - delta / self.LEAD_TIME) * 100)))
                closeness = max(0.0, 1.0 - abs(delta) / self.LEAD_TIME)
                intensity = int(50 + closeness * 155)
                prompt = 255 if abs(delta) <= self.GOOD_WINDOW * 1.15 else 0

            for control in self._cue_controls(cue):
                state = lane_state[control]
                if intensity > state["intensity"]:
                    state["position"] = position
                    state["intensity"] = intensity
                state["prompt"] = max(state["prompt"], prompt)

        left = lane_state["left"]
        middle = lane_state["middle"]
        right = lane_state["right"]
        self.app.esp32.send(
            "GAME "
            f"{left['position']} {left['intensity']} {left['prompt']} "
            f"{middle['position']} {middle['intensity']} {middle['prompt']} "
            f"{right['position']} {right['intensity']} {right['prompt']} "
            f"{int(self._mood)}"
        )

    def render_game(self, surface) -> None:
        self._draw_level(surface)
        self._draw_header(surface)
        self._draw_people(surface)
        self._draw_note_lanes(surface)

    def _draw_level(self, surface) -> None:
        surface.fill((249, 246, 232))
        difficulty = str(self._song_option.get("difficulty", "medium"))
        filename = str(self._song_option.get("level_image") or self.LEVEL_IMAGES.get(difficulty, "ZOB 01.png"))
        level = self.app.images.get("level_bgs", {}).get(filename) or self.app.images.get("level_bg")
        if level:
            rect = level.get_rect(center=(self.app.center_x, self.app.center_y + 6))
            surface.blit(level, rect)
        else:
            pygame.draw.rect(surface, (210, 168, 105), (0, 176, self.app.width, self.app.height - 176))
            pygame.draw.rect(surface, (132, 186, 91), (0, 0, self.app.width, 190))

    def _draw_header(self, surface) -> None:
        top = pygame.Rect(24, 16, self.app.width - 48, 76)
        pygame.draw.rect(surface, (255, 253, 240), top, border_radius=12)
        pygame.draw.rect(surface, (75, 56, 38), top, width=2, border_radius=12)

        meter = pygame.Rect(52, 34, 430, 18)
        pygame.draw.rect(surface, (238, 230, 211), meter, border_radius=10)
        fill = meter.copy()
        fill.width = int(meter.width * (self._mood / 100.0))
        meter_color = (235, 96, 78) if self._mood < 35 else (245, 174, 57)
        if self._mood > 72:
            meter_color = (89, 181, 96)
        pygame.draw.rect(surface, meter_color, fill, border_radius=10)
        pygame.draw.rect(surface, (75, 56, 38), meter, width=2, border_radius=10)
        draw_text(surface, f"STIMMUNG {int(self._mood)}", self.app.fonts["body"], (75, 56, 38), meter.center)

        progress = 0.0 if self._duration <= 0 else max(0.0, min(1.0, self._time / self._duration))
        progress_rect = pygame.Rect(52, 64, 430, 10)
        pygame.draw.rect(surface, (238, 230, 211), progress_rect, border_radius=6)
        progress_fill = progress_rect.copy()
        progress_fill.width = int(progress_rect.width * progress)
        pygame.draw.rect(surface, (75, 154, 225), progress_fill, border_radius=6)
        pygame.draw.rect(surface, (75, 56, 38), progress_rect, width=1, border_radius=6)
        draw_text(surface, "TRACK", self.app.fonts["body"], (92, 79, 56), (progress_rect.right + 44, progress_rect.centery))

        draw_text(
            surface,
            f"STREAK {self._combo}",
            self.app.fonts["body_bold"],
            (75, 56, 38),
            (self.app.width - 162, 42),
        )
        draw_text(
            surface,
            f"SCORE {self._score}",
            self.app.fonts["body"],
            (92, 79, 56),
            (self.app.width - 162, 70),
        )

        if self._label_timer > 0:
            label_rect = pygame.Rect(self.app.center_x - 112, 104, 224, 32)
            color = (89, 181, 96) if self._last_label in ("PERFEKT", "GUT", "YEAH") else (235, 96, 78)
            pygame.draw.rect(surface, (255, 253, 240), label_rect, border_radius=10)
            pygame.draw.rect(surface, color, label_rect, width=2, border_radius=10)
            draw_text(surface, self._last_label, self.app.fonts["body_bold"], color, label_rect.center)

    def _draw_people(self, surface) -> None:
        visible_people = self._visible_people()

        for person in visible_people[:self.MAX_VISIBLE_PEOPLE]:
            mood = self._person_mood(person)
            sprites = person.get("sprites") or self.app.images.get("normie", {})
            sprite = sprites.get(mood) or sprites.get("normal")
            energy = self._movement_energy(mood)
            enter = self._enter_progress(person)
            base_x = person["start_x"] + (person["x"] - person["start_x"]) * enter
            base_y = person["start_y"] + (person["y"] - person["start_y"]) * enter
            bounce = int(math.sin(self._crowd_phase + person["phase"]) * person["amp"] * energy)
            sway = int(math.cos(self._crowd_phase * 0.8 + person["phase"]) * 5 * energy)
            x = int(base_x + sway * enter)
            y = int(base_y - bounce * enter)
            scale = person["scale"]
            if sprite:
                frame = self._crowd_sprite(person.get("character", "person"), mood, sprite, scale)
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
            feedback = self._button_feedback.get(key, {})
            if feedback.get("timer", 0.0) > 0:
                pygame.draw.rect(surface, feedback["color"], rect, border_radius=10)
                draw_text(surface, str(feedback["label"]), self.app.fonts["body_bold"], (75, 56, 38), rect.center)
            elif active:
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
            is_active_hold = cue.get("type") == "hold" and cue.get("active")
            hold_end_time = cue["time"] + float(cue.get("duration", 0.0))
            if is_active_hold:
                if self._time > hold_end_time + self.HOLD_AUTO_COMPLETE_DELAY:
                    continue
            elif delta < -self.GOOD_WINDOW or delta > self.LEAD_TIME:
                continue
            if is_active_hold:
                y = target_y
            elif delta >= 0:
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
                    if cue.get("active"):
                        release_rect = pygame.Rect(cx - 48, target_y - 25, 96, 50)
                        release_surface = pygame.Surface(release_rect.size, pygame.SRCALPHA)
                        pygame.draw.rect(release_surface, (*color, 70), release_surface.get_rect(), border_radius=10)
                        surface.blit(release_surface, release_rect.topleft)
                        pygame.draw.rect(surface, color, release_rect, width=3, border_radius=10)
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
            self._register_miss("FALSCH", [control])
            return
        cue = min(candidates, key=lambda item: abs(item["time"] - self._time))
        signed_delta = self._time - cue["time"]
        delta = abs(signed_delta)
        if cue.get("type") == "hold":
            if delta <= self.GOOD_WINDOW:
                self._start_hold_cue(cue, control)
            else:
                self._register_miss(self._timing_label(signed_delta), [control])
            return
        if delta <= self.PERFECT_WINDOW:
            self._mark_cue_hit(cue, control)
            self._register_hit(24, 7.0, "PERFEKT", control)
        elif delta <= self.GOOD_WINDOW:
            self._mark_cue_hit(cue, control)
            self._register_hit(14, 4.0, "GUT", control)
        else:
            self._register_miss(self._timing_label(signed_delta), [control])

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
            release_start = end_time - self.HOLD_RELEASE_WINDOW
            if control and self._time > grace_until and not self._is_control_down(control):
                cue["done"] = True
                if self._time >= release_start:
                    self._register_hit(34, 9.0, "GEHALTEN", control)
                else:
                    self._register_miss("LOSGELASSEN", [control])
                return
            if self._time >= end_time + self.HOLD_AUTO_COMPLETE_DELAY:
                cue["done"] = True
                self._register_hit(34, 9.0, "GEHALTEN", control)
            return

        if abs(self._time - cue["time"]) <= self.GOOD_WINDOW:
            for control in self._cue_controls(cue):
                if self._is_control_down(control):
                    self._start_hold_cue(cue, control)
                    return

        if self._time - cue["time"] > self.GOOD_WINDOW:
            cue["done"] = True
            self._register_miss("ZU SPAET", self._cue_controls(cue))

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

    def _register_hit(self, points: int, mood_gain: float, label: str, control: str | None = None) -> None:
        self._combo += 1
        self._score += points + min(60, self._combo * 2)
        scaled_mood_gain = self._scaled_mood_gain(mood_gain, label)
        self._mood = min(100.0, self._mood + scaled_mood_gain)
        crowd_gain = (0.012 + min(0.065, self._combo * 0.004)) if self._combo >= 3 else 0.004
        self._crowd_level_target = min(1.0, self._crowd_level_target + crowd_gain)
        self._last_label = "YEAH" if self._combo and self._combo % 8 == 0 else label
        self._label_timer = 0.38
        combo_level = self._combo_level()
        if combo_level > self._last_combo_sound_level:
            self.app.sound.play_combo(combo_level)
            self._last_combo_sound_level = combo_level
        if control:
            color = (89, 181, 96) if label in ("PERFEKT", "GEHALTEN") else (245, 174, 57)
            self._set_button_feedback(control, label, color)

    def _register_miss(self, label: str, controls=None) -> None:
        if self._combo > 0:
            self.app.sound.play_streak_break()
        self._combo = 0
        self._last_combo_sound_level = 0
        rules = self._difficulty_rules()
        self._mood = max(0.0, self._mood - rules["miss_penalty"])
        self._crowd_level_target = max(0.18, self._crowd_level_target - rules["crowd_loss"])
        self._last_label = label
        self._label_timer = 0.45
        for control in controls or []:
            color = (245, 174, 57) if label == "ZU FRUEH" else (235, 96, 78)
            self._set_button_feedback(control, label, color)

    def _timing_label(self, signed_delta: float) -> str:
        if signed_delta < -self.GOOD_WINDOW:
            return "ZU FRUEH"
        if signed_delta > self.GOOD_WINDOW:
            return "ZU SPAET"
        return "DANEBEN"

    def _set_button_feedback(self, control: str, label: str, color) -> None:
        if control not in self._button_feedback:
            return
        self._button_feedback[control] = {
            "timer": 0.42,
            "label": label,
            "color": color,
        }

    def _scaled_mood_gain(self, mood_gain: float, label: str) -> float:
        combo_level = self._combo_level()
        if combo_level <= 0:
            return 0.0
        streak_scale = (0.24, 0.46, 0.74, 1.08)[combo_level - 1]
        if label == "GUT":
            streak_scale *= 0.64
        elif label == "GEHALTEN":
            streak_scale *= 0.92
        high_mood_drag = 1.0
        if self._mood > 72:
            high_mood_drag -= min(0.52, (self._mood - 72.0) / 54.0)
        return mood_gain * streak_scale * high_mood_drag

    def _combo_level(self) -> int:
        level = 0
        for threshold in self.COMBO_THRESHOLDS:
            if self._combo >= threshold:
                level += 1
        return level

    def _difficulty_rules(self):
        difficulty = str(self._song_option.get("difficulty", "medium"))
        return self.DIFFICULTY_RULES.get(difficulty, self.DIFFICULTY_RULES["medium"])

    def _crowd_mood(self) -> str:
        if self._mood < 35:
            return "bored"
        if self._combo >= 4 or self._mood > 74:
            return "happy"
        return "normal"

    def _person_mood(self, person) -> str:
        if self._mood < person.get("normal_at", 38):
            return "bored"
        if self._mood >= person.get("happy_at", 74) and self._combo >= person.get("happy_combo", 4):
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
        source = self._crowd_by_depth or self._crowd_seed
        visible = [person for person in source if person["join"] <= threshold]
        minimum = min(6, len(self._crowd_seed))
        if len(visible) < minimum:
            return sorted(self._crowd_seed[:minimum], key=lambda item: item["y"])
        return visible

    def _crowd_sprite(self, character: str, mood: str, sprite, scale: float):
        bucket = max(12, int(scale * 20))
        flipped = self._flip_crowd_sprites()
        key = (character, mood, bucket, flipped)
        cached = self._sprite_cache.get(key)
        if cached is not None:
            return cached
        normalized_scale = bucket / 20.0
        w = max(16, int(sprite.get_width() * normalized_scale))
        h = max(24, int(sprite.get_height() * normalized_scale))
        frame = pygame.transform.scale(sprite, (w, h))
        if flipped:
            frame = pygame.transform.flip(frame, True, False)
        self._sprite_cache[key] = frame
        return frame

    def _flip_crowd_sprites(self) -> bool:
        return str(self._song_option.get("difficulty", "medium")) in ("easy", "medium")

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
        if self._time < self.SONG_INTRO_NO_CUES:
            return "BEREIT"
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
        cues = self._prepare_cues_for_song(cues, sections)
        return cues, sections, time_pos + 0.8

    def _load_analyzed_show(self):
        cue_file = str(self._song_option.get("cues", "show_cues.json"))
        path = os.path.join(config.DATA_DIR, cue_file)
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
        sections = []
        for item in payload.get("sections", []):
            try:
                start, end, name = item[:3]
                difficulty = str(item[3]) if len(item) > 3 else "medium"
                sections.append((float(start), float(end), str(name), difficulty))
            except (TypeError, ValueError):
                continue

        cues = self._remove_hold_lane_conflicts(cues)
        cues = self._prepare_cues_for_song(cues, sections)
        if not cues:
            return None

        bpm = float(payload.get("bpm", 0) or 0)
        self._beat_interval = 60.0 / bpm if bpm > 0 else self.BEAT_INTERVAL

        duration = float(payload.get("duration", cues[-1]["time"] + 1.0))
        if not sections:
            sections = [(0.0, duration, "SET")]

        source = str(payload.get("source") or self._song_option.get("audio", ""))
        music_path = os.path.abspath(os.path.join(config.BASE_DIR, os.pardir, "audio", source))
        self._music_path = music_path if source and os.path.exists(music_path) else None
        return cues, sections, duration

    def _prepare_cues_for_song(self, cues, sections):
        first_visible_cue = self.SONG_INTRO_NO_CUES + self.LEAD_TIME
        prepared = [cue for cue in cues if cue["time"] >= first_visible_cue]
        difficulty = str(self._song_option.get("difficulty", "medium"))
        filtered = []
        for index, cue in enumerate(prepared):
            section_difficulty = self._difficulty_for_time(cue["time"], sections)
            controls = self._cue_controls(cue)
            if difficulty == "easy":
                if cue.get("type") == "hold" or len(controls) > 1:
                    continue
                if section_difficulty == "hard" and index % 3 != 0:
                    continue
                if section_difficulty == "medium" and index % 2 != 0:
                    continue
            elif difficulty == "medium":
                if section_difficulty == "hard" and index % 7 == 1:
                    continue
            filtered.append(cue)
        filtered = self._space_cues_by_difficulty(filtered, sections, difficulty)
        return self._add_cue_variation(filtered, sections, difficulty)

    def _space_cues_by_difficulty(self, cues, sections, difficulty: str):
        min_gaps = {
            "easy": {"intro": 1.0, "easy": 0.82, "medium": 0.92, "hard": 1.05},
            "medium": {"intro": 0.70, "easy": 0.56, "medium": 0.44, "hard": 0.44},
            "hard": {"intro": 0.56, "easy": 0.44, "medium": 0.34, "hard": 0.34},
        }
        gaps = min_gaps.get(difficulty, min_gaps["medium"])
        spaced = []
        last_time = -999.0
        last_controls = None
        for cue in sorted(cues, key=lambda item: item["time"]):
            section_difficulty = self._difficulty_for_time(cue["time"], sections)
            gap = gaps.get(section_difficulty, gaps.get("medium", 0.54))
            controls = self._cue_controls(cue)
            if cue.get("type") == "hold":
                gap += 0.10 if difficulty == "hard" else 0.16
            if len(controls) > 1 and difficulty != "hard":
                gap += 0.12
            if cue["time"] - last_time < gap:
                continue
            if difficulty == "easy" and last_controls == controls:
                cue = dict(cue)
                replacement = self.CONTROL_ORDER[(self.CONTROL_ORDER.index(controls[0]) + 1) % len(self.CONTROL_ORDER)]
                cue["controls"] = [replacement]
                cue["control"] = replacement
                controls = [replacement]
            spaced.append(cue)
            last_time = cue["time"]
            last_controls = controls
        return spaced

    def _add_cue_variation(self, cues, sections, difficulty: str):
        if not cues:
            return []
        seed_source = str(self._song_option.get("cues", "")) + difficulty
        rng = random.Random(seed_source)
        phrase_patterns = [
            ["left", "middle", "right", "middle"],
            ["left", "right", "middle", "right"],
            ["middle", "left", "middle", "right"],
            ["right", "middle", "left", "middle"],
            ["left", "middle", "left", "right", "middle"],
            ["middle", "right", "left", "right", "middle"],
        ]
        if difficulty == "medium":
            phrase_patterns.extend([
                ["left", "middle", "right", "left", "middle", "right"],
                ["middle", "right", "middle", "left", "right", "middle"],
            ])
        elif difficulty == "hard":
            phrase_patterns.extend([
                ["left", "middle", "right", "middle", "left", "right", "middle", "right"],
                ["right", "middle", "left", "middle", "right", "left", "middle", "left"],
                ["middle", "left", "right", "middle", "left", "middle", "right", "left", "middle"],
            ])
        varied = []
        last_single = None
        run_length = 0
        tap_index = 0

        for cue in sorted(cues, key=lambda item: item["time"]):
            cue = dict(cue)
            cue["hit_controls"] = []
            controls = self._cue_controls(cue)
            if cue.get("type") == "hold" or len(controls) != 1:
                varied.append(cue)
                last_single = None
                run_length = 0
                continue

            phrase_index = int(float(cue["time"]) / max(0.1, self._beat_interval * 8.0))
            pattern = phrase_patterns[phrase_index % len(phrase_patterns)]
            desired = pattern[tap_index % len(pattern)]
            section_difficulty = self._difficulty_for_time(cue["time"], sections)
            original = controls[0]

            if original == last_single:
                run_length += 1
            else:
                run_length = 1
            should_vary = run_length >= 2 or rng.random() < self._variation_chance(difficulty, section_difficulty)
            if should_vary:
                controls = [desired]
                if controls[0] == last_single and len(pattern) > 1:
                    controls = [pattern[(tap_index + 1) % len(pattern)]]
            else:
                controls = [original]

            if difficulty in ("medium", "hard") and section_difficulty in ("medium", "hard"):
                dual_every = 9 if difficulty == "medium" else 5
                dual_offsets = (4,) if difficulty == "medium" else (2, 4)
                if tap_index % dual_every in dual_offsets:
                    partner = self.CONTROL_ORDER[(self.CONTROL_ORDER.index(controls[0]) + 1) % len(self.CONTROL_ORDER)]
                    controls = [controls[0], partner]

            cue["controls"] = controls
            cue["control"] = controls[0]
            varied.append(cue)
            if len(controls) == 1:
                last_single = controls[0]
                run_length = run_length + 1 if controls[0] == original else 1
            else:
                last_single = None
                run_length = 0
            tap_index += 1

        return self._limit_repeated_controls(varied)

    def _variation_chance(self, difficulty: str, section_difficulty: str) -> float:
        base = {"easy": 0.32, "medium": 0.58, "hard": 0.72}.get(difficulty, 0.48)
        if section_difficulty == "hard":
            base += 0.12
        elif section_difficulty == "easy":
            base -= 0.10
        return max(0.18, min(0.75, base))

    def _limit_repeated_controls(self, cues):
        result = []
        last = None
        run = 0
        cycle = ["left", "middle", "right", "middle", "left", "right"]
        cycle_index = 0
        for cue in cues:
            controls = self._cue_controls(cue)
            key = "+".join(controls)
            if len(controls) == 1 and key == last:
                run += 1
            else:
                run = 1

            if len(controls) == 1 and run > 3:
                replacement = cycle[cycle_index % len(cycle)]
                cycle_index += 1
                if replacement == controls[0]:
                    replacement = cycle[cycle_index % len(cycle)]
                    cycle_index += 1
                cue = dict(cue)
                cue["controls"] = [replacement]
                cue["control"] = replacement
                key = replacement
                run = 1

            result.append(cue)
            last = key if len(self._cue_controls(cue)) == 1 else None
        return result

    def _difficulty_for_time(self, time_pos: float, sections) -> str:
        for section in sections:
            if len(section) < 4:
                continue
            start, end, _, difficulty = section[:4]
            if float(start) <= time_pos < float(end):
                return str(difficulty)
        return "medium"

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
        character_sets = self.app.images.get("people") or [{"id": "normie", "sprites": self.app.images.get("normie", {})}]
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
                scale = 0.98 + depth * 0.46 + rng.uniform(-0.04, 0.05)
                join = min(1.0, join_start + idx * 0.008 + rng.uniform(0.0, 0.045))
                side_left = (len(spots) + idx) % 2 == 0
                start_x = -70 if side_left else self.app.width + 70
                start_y = self.app.height + rng.randrange(8, 72)
                spots.append((x, y, scale, join, start_x, start_y))
        spots.sort(key=lambda item: item[3])
        people = []
        for index, (x, y, scale, join, start_x, start_y) in enumerate(spots):
            target_x = x + rng.randrange(-8, 9)
            target_y = y + rng.randrange(-5, 6)
            if join <= 0.22:
                start_x = target_x
                start_y = target_y
            character = character_sets[index % len(character_sets)]
            happy_at = rng.choice((60, 66, 72, 78, 84, 90))
            if rng.random() < 0.16:
                happy_at = rng.randrange(86, 96)
            people.append({
                "x": target_x,
                "y": target_y,
                "start_x": start_x,
                "start_y": start_y,
                "scale": scale,
                "join": join,
                "character": character.get("id", "person"),
                "sprites": character.get("sprites", {}),
                "normal_at": rng.randrange(30, 45),
                "happy_at": happy_at,
                "happy_combo": rng.choice((3, 4, 5, 6)),
                "phase": rng.random() * math.tau,
                "amp": rng.randrange(4, 11),
            })
        return people
