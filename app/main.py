import argparse
import os
import time
import pygame
import random

from . import config
from .contest import ContestManager
from .assets import ImageManager
from .fonts import FontManager
from .theme import draw_frame, draw_logo, draw_stickers
from .hardware.buttons import ButtonManager
from .hardware.coin_sensor import CoinSensor
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

        self.buttons = ButtonManager()
        self.coin_sensor = CoinSensor()
        self.sound = SoundManager()
        self.lamps = LampController()
        self.payout = PayoutController()
        self.contest = ContestManager(os.path.join(config.DATA_DIR, "contest.json"))

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

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    self._debug_enabled = not self._debug_enabled
                self.buttons.handle_event(event)
                self.coin_sensor.handle_event(event)

            self.buttons.update()
            self.coin_sensor.update()

            if self.coin_sensor.consume():
                self.add_credit(1)
                self.contest.ensure_active()
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
            f"last inputs: {self._last_inputs} ({now - self._last_input_ts:.1f}s ago)",
            f"last coin: {now - self._last_coin_ts:.1f}s ago",
            f"fps: {self.clock.get_fps():.1f}",
        ]
        x, y = 12, 12
        for line in lines:
            render = font.render(line, True, config.COLOR_TEXT_DARK)
            rect = render.get_rect(topleft=(x, y))
            self.screen.blit(render, rect)
            y += 20

    def draw_background(self, surface) -> None:
        surface.fill(config.COLOR_BG_TOP)
        self._render_decor(surface)
        if self.images.get("hero_bg"):
            surface.blit(self.images["hero_bg"], (0, 0))
        if self.images.get("logo"):
            logo = self.images["logo"]
            rect = logo.get_rect(center=(self.center_x, 44))
            surface.blit(logo, rect)
        else:
            draw_logo(surface, (self.center_x, 40), self.fonts["body_bold"])
        # no frame

    def draw_overlays(self, surface) -> None:
        pass

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
        hero_bg = manager.load("670c13ad0dc40be65dff6e52_about-hero-bg.png", (self.width, self.height))
        logo = manager.load("woodlands_logo_images.png")
        if logo:
            target_w = 220
            w, h = logo.get_size()
            target_h = max(1, int(h * (target_w / max(1, w))))
            logo = pygame.transform.smoothscale(logo, (target_w, target_h))
        return {
            "player": manager.load("woodlands_coin_effect1.png"),
            "stickers": [
                manager.load("wdlnds_sticker1.png"),
                manager.load("wdlnds_sticker2.png"),
                manager.load("wdlnds_sticker3.png"),
            ],
            "hero_bg": hero_bg,
            "logo": logo,
            "form_left": manager.load("forms_0.png"),
            "form_right": manager.load("forms_2.png"),
        }


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
