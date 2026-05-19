import pygame

from .. import config
from ..storage import load_json
from ..ui import draw_button_hints, draw_text
from .base import BaseState


class SongSelectState(BaseState):
    OPTIONS = [
        {"label": "WALDWINKEL", "difficulty": "easy", "caption": "EINFACH", "level_image": "Waldwinkel 01.png"},
        {"label": "ZOB", "difficulty": "medium", "caption": "MITTEL", "level_image": "ZOB 01.png"},
        {"label": "MARKTPLATZ", "difficulty": "hard", "caption": "SCHWER", "level_image": "Marktplatz 01.png"},
    ]
    BUTTON_TO_INDEX = {"left": 0, "middle": 1, "right": 2}

    def __init__(self, app) -> None:
        super().__init__(app)
        self._selected = 1
        self._track_selected = 0
        self._phase = "location"
        self._location = self.OPTIONS[1]
        self._armed_index = None
        self._fade_in = 0.0
        self._fade_out = 0.0
        self._leaving = False
        self._catalog = []

    def on_enter(self) -> None:
        self._selected = 1
        self._track_selected = 0
        self._phase = "location"
        self._location = self.OPTIONS[self._selected]
        self._armed_index = None
        self._fade_in = 0.0
        self._fade_out = 0.0
        self._leaving = False
        self._catalog = self._load_catalog()
        self.app.esp32.send("MODE standby")
        self.app.sound.play_scoreboard_loop()

    def on_exit(self) -> None:
        self.app.sound.stop_scoreboard_loop()

    def handle_input(self, pressed):
        if self._leaving:
            return
        if self._phase == "track":
            tracks = self._tracks_for_location(self._location)
            if "start" in pressed:
                self._phase = "location"
                self._armed_index = None
                self.app.esp32.send("LED flash start")
                return
            for control in self.BUTTON_TO_INDEX:
                if control in pressed and tracks:
                    self._choose_track(control, tracks)
                    return
            return

        for control in self.BUTTON_TO_INDEX:
            if control in pressed:
                self._choose_location(control)
                return

    def update(self, dt: float) -> None:
        if self._leaving:
            self._fade_out = min(1.0, self._fade_out + dt * 1.35)
            if self._fade_out >= 1.0:
                self.app.state_machine.change("minigame")
            return
        self._fade_in = min(1.0, self._fade_in + dt * 1.35)

    def render(self, surface) -> None:
        self.app.draw_background(surface)
        if self._phase == "track":
            self._render_track_select(surface)
        else:
            self._render_location_select(surface)

        if self._fade_in < 1.0:
            self._draw_fade(surface, 1.0 - self._fade_in)
        if self._leaving:
            self._draw_fade(surface, self._fade_out)

    def _render_location_select(self, surface) -> None:
        ink = config.COLOR_TEXT_DARK
        soft = (92, 79, 56)

        draw_text(surface, "FLOOR WAEHLEN", self.app.fonts["title"], ink, (self.app.center_x, 130))

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
            if active and self._armed_index == index:
                draw_text(surface, "NOCHMAL DRUECKEN", self.app.fonts["body"], border, (rect.centerx, rect.top + 132))

        draw_button_hints(surface, self.app, left=True, middle=True, right=True, middle_label="MITTE")

    def _render_track_select(self, surface) -> None:
        ink = config.COLOR_TEXT_DARK
        soft = (92, 79, 56)
        accent = (245, 174, 57)
        tracks = self._tracks_for_location(self._location)

        draw_text(surface, self._location["label"], self.app.fonts["title"], ink, (self.app.center_x, 104))
        draw_text(surface, "TRACK WAEHLEN", self.app.fonts["body_bold"], soft, (self.app.center_x, 146))

        card_w = 278
        card_h = 190
        gap = 22
        total_w = card_w * 3 + gap * 2
        start_x = self.app.center_x - total_w // 2
        y = 210

        if not tracks:
            draw_text(surface, "KEINE TRACKS GEFUNDEN", self.app.fonts["body_bold"], ink, (self.app.center_x, 292))
            draw_button_hints(surface, self.app, confirm=True, confirm_label="ZURUECK")
            return

        for index, song in enumerate(tracks):
            x = start_x + index * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            active = index == self._track_selected
            fill = (255, 253, 240) if active else (246, 238, 222)
            border = accent if active else (75, 56, 38)
            pygame.draw.rect(surface, fill, rect, border_radius=10)
            pygame.draw.rect(surface, border, rect, width=4 if active else 2, border_radius=10)
            draw_text(surface, str(song.get("artist", "ARTIST")).upper(), self.app.fonts["body_bold"], ink, (rect.centerx, rect.top + 52))
            title = str(song.get("title", "TRACK")).upper()
            if len(title) > 24:
                title = title[:21] + "..."
            draw_text(surface, title, self.app.fonts["body"], soft, (rect.centerx, rect.top + 92))
            bpm = song.get("bpm")
            detail = f"BPM {bpm}" if bpm else str(song.get("caption", ""))
            draw_text(surface, detail, self.app.fonts["body"], soft, (rect.centerx, rect.top + 132))
            footer = "NOCHMAL DRUECKEN" if active and self._armed_index == index else self._difficulty_label(song)
            draw_text(surface, footer, self.app.fonts["body"], border, (rect.centerx, rect.top + 162))

        draw_button_hints(
            surface,
            self.app,
            confirm=True,
            confirm_label="ZURUECK",
            left=True,
            middle=True,
            right=True,
            middle_label="MITTE",
        )

    def _draw_fade(self, surface, amount: float) -> None:
        overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
        overlay.fill((255, 253, 240, int(max(0.0, min(1.0, amount)) * 255)))
        surface.blit(overlay, (0, 0))

    def _load_catalog(self):
        path = f"{config.DATA_DIR}/song_catalog.json"
        payload = load_json(path, [])
        return payload if isinstance(payload, list) else []

    def _choose_location(self, control: str) -> None:
        index = self.BUTTON_TO_INDEX[control]
        self.app.esp32.send(f"LED flash {control}")
        if self._armed_index == index:
            self._location = self.OPTIONS[index]
            tracks = self._tracks_for_location(self._location)
            self._track_selected = 1 if len(tracks) >= 3 else 0
            self._phase = "track"
            self._armed_index = None
            return
        self._selected = index
        self._armed_index = index

    def _choose_track(self, control: str, tracks) -> None:
        index = min(self.BUTTON_TO_INDEX[control], len(tracks) - 1)
        self.app.esp32.send(f"LED flash {control}")
        if self._armed_index == index:
            self.app.selected_song = tracks[index]
            self.app.current_game = "show_control"
            self.app.consume_credit()
            self._leaving = True
            self._fade_out = 0.0
            return
        self._track_selected = index
        self._armed_index = index

    def _tracks_for_location(self, option):
        location = str(option.get("location") or option.get("label", "")).lower()
        difficulty = str(option.get("difficulty", ""))
        tracks = [
            dict(song)
            for song in self._catalog
            if str(song.get("location", "")).lower() == location or str(song.get("difficulty", "")) == difficulty
        ]
        for song in tracks:
            song.setdefault("label", option["label"])
            song.setdefault("caption", option["caption"])
            song.setdefault("level_image", option.get("level_image"))
        return tracks

    def _difficulty_label(self, song) -> str:
        difficulty = str(song.get("difficulty", "medium"))
        if difficulty == "easy":
            return "EINFACH"
        if difficulty == "hard":
            return "SCHWER"
        return "MITTEL"
