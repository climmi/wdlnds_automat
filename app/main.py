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
from .states.state_machine import StateMachine


class App:
    def __init__(self, width: int, height: int, fullscreen: bool) -> None:
        pygame.init()
        flags = pygame.SCALED
        if fullscreen:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Woodlands Automat")

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
        self._attach_gpio_inputs()

        self.state_machine = StateMachine({
            "idle": IdleState(self),
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
            self._jump_to_game("show_control")
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
        level_bg = self._load_graphic(os.path.join(root_dir, "graphic", "level", "isometric_pixel_art_scene_of_an_outdoor_indoor_hyb.png"))
        if level_bg:
            level_bg = self._scale_to_cover(level_bg, self.width, self.height)
        normie_dir = os.path.join(root_dir, "graphic", "charakters", "normie 01")
        normie = {
            "normal": self._load_graphic(os.path.join(normie_dir, "normie_anim_normal.png")),
            "bored": self._load_graphic(os.path.join(normie_dir, "normie_anim_bored.png")),
            "happy": self._load_graphic(os.path.join(normie_dir, "normie_anim_happy.png")),
        }
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
            "level_bg": level_bg,
            "normie": normie,
        }

    def _load_graphic(self, path: str):
        if not os.path.exists(path):
            return None
        return pygame.image.load(path).convert_alpha()

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
