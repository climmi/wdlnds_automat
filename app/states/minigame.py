import random
import pygame

from .. import config
from ..ui import draw_text, draw_panel
from .base import BaseState


class MiniGameState(BaseState):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._player_lane = 1
        self._obstacles = []
        self._elapsed = 0.0
        self._score = 0
        self._spawn_timer = 0.0
        self._game_over = False
        self._mode = "play"
        self._name_chars = ["A", "A", "A"]
        self._name_index = 0
        self._alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-!?*+")
        self._track_rect = None
        self._player_sprite = None
        self._obstacle_sprites = []
        self._player_size = 54
        self._pending_score = 0
        self._game_over_timer = 0.0
        self._phase = "play"
        self._fade = 0.0
        self._entry_timer = 0.0

    def on_enter(self) -> None:
        self._player_lane = 1
        self._obstacles = []
        self._elapsed = 0.0
        self._score = 0
        self._spawn_timer = 0.0
        self._game_over = False
        self._mode = "play"
        self._name_chars = ["A", "A", "A"]
        self._name_index = 0
        self._track_rect = pygame.Rect(140, 130, self.app.width - 280, self.app.height - 220)
        self._prepare_sprites()
        self._pending_score = 0
        self._game_over_timer = 0.0
        self._phase = "play"
        self._fade = 0.0
        self._entry_timer = 0.0

    def handle_input(self, pressed):
        if self._game_over:
            if self._mode == "entry":
                self._handle_name_entry(pressed)
            return

        if "left" in pressed:
            self._player_lane = 0
        if "middle" in pressed:
            self._player_lane = 1
        if "right" in pressed:
            self._player_lane = 2

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

        self._elapsed += dt
        self._score = int(self._elapsed * 10)

        speed = config.MINIGAME_START_SPEED + config.MINIGAME_SPEED_RAMP * self._elapsed
        spawn_interval = max(0.35, config.MINIGAME_SPAWN_BASE - config.MINIGAME_SPAWN_RAMP * (self._elapsed / 10.0))

        self._spawn_timer += dt
        if self._spawn_timer >= spawn_interval:
            self._spawn_timer = 0.0
            lanes = list(range(config.LANE_COUNT))
            random.shuffle(lanes)
            count = 2 if random.random() < config.MINIGAME_DOUBLE_SPAWN_CHANCE else 1
            count = min(count, config.LANE_COUNT - 1)
            for lane in lanes[:count]:
                sprite = None
                if self._obstacle_sprites and lane < len(self._obstacle_sprites):
                    sprite = self._obstacle_sprites[lane]
                self._obstacles.append({"lane": lane, "y": -40, "sprite": sprite})

        for obstacle in self._obstacles:
            obstacle["y"] += speed * dt

        self._obstacles = [o for o in self._obstacles if o["y"] < self.app.height + 60]

        track_top = self._track_rect.top if self._track_rect else 0
        player_y = self.app.height - 140
        player_rect = self._player_rect(track_top, player_y)
        for obstacle in self._obstacles:
            obstacle_rect = self._obstacle_rect(obstacle, track_top)
            if player_rect and obstacle_rect and player_rect.colliderect(obstacle_rect):
                self._game_over = True
                self._mode = "entry"
                self._pending_score = self._score
                self._game_over_timer = 0.0
                self._phase = "gameover_wait"
                self.app.sound.play_win()
                break

    def render(self, surface) -> None:
        if self._game_over and self._phase == "entry":
            self.app.draw_background(surface)
            title_font = self.app.fonts["title"]
            body_font = self.app.fonts["body"]
            draw_text(surface, "HIGH SCORE", title_font, config.COLOR_TEXT_DARK,
                      (self.app.center_x, 120))
            self._render_scoreboard(surface, y=self.app.center_y - 120, include_pending=True)
            self._render_name_entry(surface)
            return

        self.app.draw_background(surface)
        title_font = self.app.fonts["title"]
        body_font = self.app.fonts["body"]



        track_rect = self._track_rect or pygame.Rect(140, 130, self.app.width - 280, self.app.height - 220)
        lane_width = track_rect.width / config.LANE_COUNT
        surface.set_clip(track_rect)
        lane_colors = [config.COLOR_LANE_1, config.COLOR_LANE_2, config.COLOR_LANE_3]
        for lane_idx in range(config.LANE_COUNT):
            lane_x = track_rect.left + lane_idx * lane_width
            color = lane_colors[lane_idx % len(lane_colors)]
            lane_rect = pygame.Rect(
                int(lane_x + 22),
                int(track_rect.top + 10),
                int(lane_width - 44),
                int(track_rect.height - 20),
            )
            lane_surface = pygame.Surface((lane_rect.width, lane_rect.height), pygame.SRCALPHA)
            lane_surface.fill(color)
            self._shade_lane(lane_surface, top_strength=70, bottom_strength=130, mid_boost=28)
            surface.blit(lane_surface, lane_rect)

        player_x = track_rect.left + lane_width * self._player_lane + lane_width / 2
        player_y = self.app.height - 140
        self._render_player(surface, player_x, player_y)

        for obstacle in self._obstacles:
            ox = track_rect.left + lane_width * obstacle["lane"] + lane_width / 2
            oy = obstacle["y"] + track_rect.top
            self._render_obstacle(surface, ox, oy, obstacle.get("sprite"))
        surface.set_clip(None)

        draw_text(surface, f"Score: {self._score}", body_font, config.COLOR_TEXT_DARK,
                  (self.app.center_x, 110))

        status = self.app.contest.status()
        if status.active:
            minutes = int(self.app.contest.time_left() // 60)
            draw_text(surface, f"Highscore: {status.top_name} {status.top_score} | {minutes} min", body_font,
                      config.COLOR_TEXT_DARK, (self.app.center_x, self.app.height - 40))

        if self._game_over:
            if self._phase == "gameover_wait":
                overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
                overlay.fill((180, 180, 180, 140))
                surface.blit(overlay, (0, 0))
                draw_text(surface, "GAME OVER", title_font, config.COLOR_WARNING,
                          (self.app.center_x, self.app.center_y))
            elif self._phase == "entry":
                entry_surface = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
                draw_text(entry_surface, "Name eintragen", body_font, config.COLOR_TEXT_DARK,
                          (self.app.center_x, self.app.center_y + 60))
                self._render_scoreboard(entry_surface, y=self.app.center_y - 170, include_pending=True)
                self._render_name_entry(entry_surface)
                entry_surface.set_alpha(int(255 * self._fade))
                surface.blit(entry_surface, (0, 0))

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
        status = self.app.contest.status()
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
        self.app.contest.register_score(self._pending_score, name)
        self._game_over = False
        self._phase = "play"
        self.app.state_machine.change("idle")

    def _prepare_sprites(self) -> None:
        player = self.app.images.get("player")
        if player:
            self._player_sprite = pygame.transform.smoothscale(
                player, (self._player_size, self._player_size)
            )
        else:
            self._player_sprite = None

        stickers = self.app.images.get("stickers", [])
        self._obstacle_sprites = [
            sticker for sticker in stickers if sticker
        ]
        while len(self._obstacle_sprites) < config.LANE_COUNT:
            self._obstacle_sprites.append(None)

    def _pick_obstacle(self):
        return None

    def _render_player(self, surface, x: float, y: float) -> None:
        if self._player_sprite:
            rect = self._player_sprite.get_rect(center=(int(x), int(y)))
            surface.blit(self._player_sprite, rect)
            return
        pygame.draw.circle(surface, config.COLOR_ACCENT_2, (int(x), int(y)), 24)

    def _render_obstacle(self, surface, x: float, y: float, sprite) -> None:
        rect = self._scaled_obstacle_rect(x, y, sprite)
        if sprite and rect:
            scaled = pygame.transform.smoothscale(sprite, (rect.width, rect.height)).convert_alpha()
            self._shade_with_world_light(scaled, rect.top)
            surface.blit(scaled, rect)
            return
        pygame.draw.rect(surface, config.COLOR_WARNING, (x - 20, y - 20, 40, 40), border_radius=6)

    def _player_rect(self, track_top: int, y: float):
        player_x = self._track_rect.left + (self._track_rect.width / config.LANE_COUNT) * self._player_lane + (
            self._track_rect.width / config.LANE_COUNT
        ) / 2
        if self._player_sprite:
            return self._player_sprite.get_rect(center=(int(player_x), int(y)))
        return pygame.Rect(int(player_x - 20), int(y - 20), 40, 40)

    def _obstacle_rect(self, obstacle, track_top: int):
        lane_width = self._track_rect.width / config.LANE_COUNT
        ox = self._track_rect.left + lane_width * obstacle["lane"] + lane_width / 2
        oy = obstacle["y"] + track_top
        sprite = obstacle.get("sprite")
        rect = self._scaled_obstacle_rect(ox, oy, sprite)
        if rect:
            return rect
        return pygame.Rect(int(ox - 20), int(oy - 20), 40, 40)

    def _scaled_obstacle_rect(self, x: float, y: float, sprite):
        if not self._track_rect:
            return None
        lane_width = self._track_rect.width / config.LANE_COUNT
        target_w = int(lane_width - 52)
        if sprite:
            sw, sh = sprite.get_size()
            aspect = sh / max(1, sw)
            base_h = max(1, int(target_w * aspect))
        else:
            base_h = target_w

        mid = self._track_rect.top + self._track_rect.height / 2
        dist = abs(y - mid)
        norm = min(1.0, dist / max(1.0, self._track_rect.height / 2))
        squash = 0.65 + (1.0 - norm) * 0.35
        height = max(8, int(base_h * squash))
        return pygame.Rect(int(x - target_w / 2), int(y - height / 2), target_w, height)

    def _shade_lane(self, surface, top_strength: int = 70, bottom_strength: int = 130, mid_boost: int = 24) -> None:
        width, height = surface.get_size()
        top = pygame.Surface((width, height), pygame.SRCALPHA)
        bottom = pygame.Surface((width, height), pygame.SRCALPHA)
        mid = pygame.Surface((width, height), pygame.SRCALPHA)
        half = max(1, height // 2)
        for y in range(half):
            alpha = int(top_strength * (1 - (y / half)))
            pygame.draw.line(top, (0, 0, 0, alpha), (0, y), (width, y))
        for y in range(half):
            alpha = int(bottom_strength * (1 - (y / half)))
            pygame.draw.line(bottom, (0, 0, 0, alpha), (0, height - 1 - y), (width, height - 1 - y))

        band_h = max(6, height // 6)
        band_top = max(0, height // 2 - band_h // 2)
        for y in range(band_h):
            alpha = int(mid_boost * (1 - abs((y - band_h / 2) / (band_h / 2))))
            pygame.draw.line(mid, (255, 255, 255, alpha), (0, band_top + y), (width, band_top + y))

        surface.blit(top, (0, 0))
        surface.blit(bottom, (0, 0))
        surface.blit(mid, (0, 0))

    def _shade_with_world_light(self, surface, world_top: int) -> None:
        if not self._track_rect:
            return
        width, height = surface.get_size()
        mid_y = self._track_rect.top + self._track_rect.height / 2
        band_h = max(6, self._track_rect.height // 6)
        mult = pygame.Surface((width, height), pygame.SRCALPHA)
        add = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(height):
            world_y = world_top + y
            if world_y <= mid_y:
                dist = max(1.0, mid_y - self._track_rect.top)
                t = (mid_y - world_y) / dist
                dark = int(70 * t)
                light = int(24 * max(0.0, 1 - abs(world_y - mid_y) / (band_h / 2)))
            else:
                dist = max(1.0, self._track_rect.bottom - mid_y)
                t = (world_y - mid_y) / dist
                dark = int(130 * t)
                light = int(24 * max(0.0, 1 - abs(world_y - mid_y) / (band_h / 2)))
            if dark:
                val = max(0, 255 - dark)
                mult.fill((val, val, val, 255), rect=pygame.Rect(0, y, width, 1))
            else:
                mult.fill((255, 255, 255, 255), rect=pygame.Rect(0, y, width, 1))
            if light:
                add.fill((light, light, light, 255), rect=pygame.Rect(0, y, width, 1))
        surface.blit(mult, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(add, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
