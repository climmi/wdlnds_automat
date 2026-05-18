import argparse
import os
import sys
import time
import pygame

from . import config
from .highscores import HighScoreManager
from .assets import ImageManager
from .fonts import FontManager
from .theme import create_background, draw_logo
from .hardware.buttons import ButtonManager
from .hardware.coin_sensor import CoinSensor
from .hardware.esp32_serial import Esp32SerialController
from .hardware.lamps import LampController
from .hardware.payout import PayoutController
from .hardware.sound import SoundManager
from .states.idle import IdleState
from .states.minigame import MiniGameState
from .states.song_select import SongSelectState
from .states.state_machine import StateMachine


class App:
    def __init__(self, width: int, height: int, fullscreen: bool) -> None:
        pygame.init()
        flags = pygame.SCALED
        if fullscreen:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Woodlands Automat")
        pygame.mouse.set_visible(False)
        pygame.mouse.set_pos((width - 1, height // 2))

        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2

        self.fonts = FontManager(os.path.dirname(__file__)).build()
        self.images = self._load_images()
        self._background = create_background(width, height)

        self.clock = pygame.time.Clock()
        self.running = True
        self.credits = 0
        self._coin_event = False
        self._last_inputs = []
        self._last_input_ts = 0.0
        self._last_coin_ts = 0.0
        self._debug_enabled = config.DEBUG_OVERLAY
        self._decor = {
            "left_angle": 0.0,
            "right_angle": 0.0,
            "left_speed": 18.0,
            "right_speed": -12.0,
            "left_timer": 0.0,
            "right_timer": 0.0,
        }
        self._runtime = 0.0
        self._local_dev_mode = config.LOCAL_DEV_MODE

        self.buttons = ButtonManager()
        self.coin_sensor = CoinSensor()
        self.esp32 = Esp32SerialController()
        self.sound = SoundManager()
        self.lamps = LampController()
        self.payout = PayoutController()
        self.highscores = HighScoreManager(os.path.join(config.DATA_DIR, "highscores.json"))
        self.current_game = "show_control"
        self.selected_song = {
            "label": "ZOB",
            "difficulty": "medium",
            "caption": "VOLLER FLOOR",
            "level_image": "ZOB 01.png",
        }
        self._attach_gpio_inputs()

        self.state_machine = StateMachine({
            "idle": IdleState(self),
            "song_select": SongSelectState(self),
            "minigame": MiniGameState(self),
        }, "idle")

    def add_credit(self, amount: int) -> None:
        self.credits += amount

    def consume_credit(self) -> None:
        if self.credits > 0:
            self.credits -= 1

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self._runtime += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    self._debug_enabled = not self._debug_enabled
                if self._local_dev_mode and event.type == pygame.KEYDOWN:
                    self._handle_local_dev_shortcuts(event)
                self.buttons.handle_event(event)
                self.coin_sensor.handle_event(event)

            self.esp32.update(self.buttons, self.coin_sensor)
            self.buttons.update()
            self.coin_sensor.update()

            if self.coin_sensor.consume():
                self.add_credit(1)
                self._coin_event = True
                self._last_coin_ts = time.time()
                if self.state_machine.current.__class__.__name__ != "IdleState":
                    self.sound.play_coin()

            pressed = self.buttons.consume()
            if pressed:
                self._last_inputs = pressed
                self._last_input_ts = time.time()
            # decor disabled for performance
            self.state_machine.handle_input(pressed)
            self.state_machine.update(dt)
            self.state_machine.render(self.screen)
            # no overlays
            if self._debug_enabled:
                self._draw_debug_overlay()
            pygame.display.flip()

        pygame.quit()

    def consume_coin_event(self) -> bool:
        if self._coin_event:
            self._coin_event = False
            return True
        return False

    def _draw_debug_overlay(self) -> None:
        now = time.time()
        font = pygame.font.SysFont("Consolas", 18)
        lines = [
            f"state: {self.state_machine.current.__class__.__name__}",
            f"credits: {self.credits}",
            f"local dev: {self._local_dev_mode}",
            f"last inputs: {self._last_inputs} ({now - self._last_input_ts:.1f}s ago)",
            f"last coin: {now - self._last_coin_ts:.1f}s ago",
            f"fps: {self.clock.get_fps():.1f}",
            f"gpio btn: {self.buttons.gpio_states()}",
            f"gpio coin: {self.coin_sensor.gpio_state()}",
            f"esp32: {self.esp32.status()}",
        ]
        x, y = 12, 12
        for line in lines:
            render = font.render(line, True, config.COLOR_TEXT_DARK)
            rect = render.get_rect(topleft=(x, y))
            self.screen.blit(render, rect)
            y += 20

    def draw_background(self, surface, logo: bool = True) -> None:
        surface.blit(self._background, (0, 0))
        if not logo:
            return
        if self.images.get("logo"):
            logo = self.images["logo"]
            rect = logo.get_rect(center=(self.center_x, 44))
            surface.blit(logo, rect)
        else:
            draw_logo(surface, (self.center_x, 40), self.fonts["body_bold"])

    def draw_overlays(self, surface) -> None:
        pass

    def _handle_local_dev_shortcuts(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_1:
            self.state_machine.change("song_select")
        elif event.key == pygame.K_0:
            self.credits = 0
            self.state_machine.change("idle")
        elif event.key == pygame.K_9:
            self.credits = 9

    def _jump_to_game(self, game_id: str) -> None:
        self.current_game = "show_control"
        self.credits = max(self.credits, 1)
        self.consume_credit()
        self.state_machine.change("minigame")

    def _render_decor(self, surface) -> None:
        pass

    def _update_decor(self, dt: float) -> None:
        pass

    def _tint(self, surface, color):
        mask = pygame.mask.from_surface(surface)
        tinted = mask.to_surface(setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
        return tinted.convert_alpha()

    def _load_images(self) -> dict:
        manager = ImageManager(os.path.dirname(__file__))
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        logo = manager.load("woodlands_logo_images.png")
        if logo:
            target_w = 220
            w, h = logo.get_size()
            target_h = max(1, int(h * (target_w / max(1, w))))
            logo = pygame.transform.smoothscale(logo, (target_w, target_h))
        level_dir = os.path.join(root_dir, "graphic", "level")
        level_bgs = {}
        for filename in ("Waldwinkel 01.png", "ZOB 01.png", "Marktplatz 01.png"):
            image = self._load_graphic(os.path.join(level_dir, filename))
            if image:
                level_bgs[filename] = self._scale_to_cover(image, self.width, self.height)
        characters_dir = os.path.join(root_dir, "graphic", "charakters")
        people = self._load_character_sets(characters_dir)
        normie = people[0]["sprites"] if people else {}
        return {
            "player": manager.load("woodlands_coin_effect1.png"),
            "stickers": [
                manager.load("wdlnds_sticker1.png"),
                manager.load("wdlnds_sticker2.png"),
                manager.load("wdlnds_sticker3.png"),
            ],
            "hero_bg": None,
            "logo": logo,
            "form_left": manager.load("forms_0.png"),
            "form_right": manager.load("forms_2.png"),
            "cursor": manager.load("forms_11.png"),
            "ball": manager.load("forms_3.png"),
            "level_bg": level_bgs.get("ZOB 01.png"),
            "level_bgs": level_bgs,
            "normie": normie,
            "people": people,
        }

    def _load_graphic(self, path: str):
        if not os.path.exists(path):
            return None
        return pygame.image.load(path).convert_alpha()

    def _load_character_sets(self, characters_dir: str):
        if not os.path.isdir(characters_dir):
            return []
        people = []
        for folder in sorted(os.listdir(characters_dir)):
            folder_path = os.path.join(characters_dir, folder)
            if not os.path.isdir(folder_path):
                continue
            sprites = {}
            for filename in sorted(os.listdir(folder_path)):
                lower = filename.lower()
                if not lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
                    continue
                state = None
                if "bored" in lower:
                    state = "bored"
                elif "happy" in lower:
                    state = "happy"
                elif "normal" in lower:
                    state = "normal"
                if state is None:
                    continue
                image = self._load_graphic(os.path.join(folder_path, filename))
                if image:
                    sprites[state] = self._prepare_character_sprite(image)
            if sprites:
                normal = sprites.get("normal") or next(iter(sprites.values()))
                sprites.setdefault("normal", normal)
                sprites.setdefault("bored", normal)
                sprites.setdefault("happy", normal)
                people.append({"id": folder, "sprites": sprites})
        return people

    def _prepare_character_sprite(self, image):
        cleaned = self._remove_white_matte(image)
        return self._normalize_character_sprite(cleaned, target_height=82, canvas_size=(58, 90))

    def _remove_white_matte(self, image):
        surface = image.copy().convert_alpha()
        width, height = surface.get_size()
        remove = set()
        queue = []

        for x in range(width):
            queue.append((x, 0))
            queue.append((x, height - 1))
        for y in range(height):
            queue.append((0, y))
            queue.append((width - 1, y))

        seen = set()
        while queue:
            x, y = queue.pop()
            if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
                continue
            seen.add((x, y))
            color = surface.get_at((x, y))
            if color.a == 0:
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    queue.append((nx, ny))
                continue
            if self._is_white_matte(color, threshold=235):
                remove.add((x, y))
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    queue.append((nx, ny))

        for x, y in remove:
            surface.set_at((x, y), (255, 255, 255, 0))

        # Remove bright anti-aliased fringe pixels left next to transparent matte.
        for _ in range(2):
            fringe = []
            for y in range(height):
                for x in range(width):
                    color = surface.get_at((x, y))
                    if color.a == 0 or not self._is_white_matte(color, threshold=244):
                        continue
                    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if 0 <= nx < width and 0 <= ny < height and surface.get_at((nx, ny)).a == 0:
                            fringe.append((x, y))
                            break
            if not fringe:
                break
            for x, y in fringe:
                surface.set_at((x, y), (255, 255, 255, 0))

        return surface

    def _is_white_matte(self, color, threshold: int) -> bool:
        return color.r >= threshold and color.g >= threshold and color.b >= threshold

    def _normalize_character_sprite(self, image, target_height: int, canvas_size: tuple[int, int]):
        bounds = self._alpha_bounds(image)
        if bounds is None:
            return image
        source = image.subsurface(bounds).copy()
        scale = target_height / max(1, source.get_height())
        target_w = max(1, int(source.get_width() * scale))
        target_h = max(1, int(source.get_height() * scale))
        if target_w > canvas_size[0]:
            scale = canvas_size[0] / max(1, source.get_width())
            target_w = canvas_size[0]
            target_h = max(1, int(source.get_height() * scale))
        scaled = pygame.transform.smoothscale(source, (target_w, target_h))
        canvas = pygame.Surface(canvas_size, pygame.SRCALPHA)
        x = (canvas_size[0] - target_w) // 2
        y = canvas_size[1] - target_h
        canvas.blit(scaled, (x, y))
        return canvas.convert_alpha()

    def _alpha_bounds(self, image, threshold: int = 12):
        width, height = image.get_size()
        min_x, min_y = width, height
        max_x, max_y = -1, -1
        for y in range(height):
            for x in range(width):
                if image.get_at((x, y)).a > threshold:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        if max_x < min_x or max_y < min_y:
            return None
        return pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

    def _scale_to_cover(self, image, width: int, height: int):
        src_w, src_h = image.get_size()
        scale = max(width / src_w, height / src_h)
        target_w = max(1, int(src_w * scale))
        target_h = max(1, int(src_h * scale))
        scaled = pygame.transform.scale(image, (target_w, target_h))
        left = max(0, (target_w - width) // 2)
        top = max(0, (target_h - height) // 2)
        return scaled.subsurface(pygame.Rect(left, top, width, height)).copy()

    def _attach_gpio_inputs(self) -> None:
        # Raspberry Pi pin mapping (BCM):
        # left=GPIO17, middle=GPIO27, right=GPIO22, start=GPIO23, coin=GPIO24
        try:
            self.buttons.attach_gpio({
                "left": 17,
                "middle": 27,
                "right": 22,
                "start": 23,
            })
            self.coin_sensor.attach_gpio(24)
        except Exception:
            # Keep keyboard controls usable on non-Pi systems, but log the reason.
            print("GPIO init disabled; keyboard fallback active.", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Woodlands Automat UI")
    parser.add_argument("--width", type=int, default=config.SCREEN_WIDTH)
    parser.add_argument("--height", type=int, default=config.SCREEN_HEIGHT)
    parser.add_argument("--fullscreen", action="store_true", default=config.FULLSCREEN)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = App(args.width, args.height, args.fullscreen)
    app.run()


if __name__ == "__main__":
    main()
