import random
import pygame

from .. import config
from ..ui import draw_text
from .score_base import ScoreGameState


class MiniGameState(ScoreGameState):
    game_id = "runner"
    game_name = "Runner"

    def __init__(self, app) -> None:
        super().__init__(app)
        self._player_lane = 1
        self._obstacles = []
        self._elapsed = 0.0
        self._score = 0
        self._spawn_timer = 0.0
        self._track_rect = None
        self._player_sprite = None
        self._obstacle_sprites = []
        self._player_size = 54

    def on_game_start(self) -> None:
        self._player_lane = 1
        self._obstacles = []
        self._elapsed = 0.0
        self._score = 0
        self._spawn_timer = 0.0
        self._track_rect = pygame.Rect(140, 130, self.app.width - 280, self.app.height - 220)
        self._prepare_sprites()

    def handle_game_input(self, pressed):
        if "left" in pressed:
            self._player_lane = 0
        if "middle" in pressed:
            self._player_lane = 1
        if "right" in pressed:
            self._player_lane = 2

    def update_game(self, dt: float) -> None:
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
                self.trigger_game_over(self._score)
                break

    def render_game(self, surface) -> None:
        self.app.draw_background(surface)
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
