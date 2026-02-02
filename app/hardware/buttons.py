import time
from typing import Dict, List

import pygame

from .. import config
from .gpio import GpioButton


KEY_LOOKUP = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "down": pygame.K_DOWN,
    "up": pygame.K_UP,
    "return": pygame.K_RETURN,
    "space": pygame.K_SPACE,
    "a": pygame.K_a,
    "s": pygame.K_s,
    "d": pygame.K_d,
    "c": pygame.K_c,
}


class ButtonManager:
    def __init__(self) -> None:
        self._queue: List[str] = []
        self._last_pressed: Dict[str, float] = {}
        self._gpio_buttons: Dict[str, GpioButton] = {}

        for logical in ("left", "middle", "right", "start"):
            self._last_pressed[logical] = 0.0

    def attach_gpio(self, mapping: Dict[str, int]) -> None:
        for logical, pin in mapping.items():
            self._gpio_buttons[logical] = GpioButton(pin)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        for logical, keys in config.KEYMAP.items():
            if logical == "coin":
                continue
            for key in keys:
                if event.key == KEY_LOOKUP.get(key):
                    self._enqueue(logical)

    def _enqueue(self, logical: str) -> None:
        now = time.time()
        last = self._last_pressed.get(logical, 0.0)
        if (now - last) * 1000.0 < config.BUTTON_DEBOUNCE_MS:
            return
        self._last_pressed[logical] = now
        self._queue.append(logical)

    def update(self) -> None:
        for logical, button in self._gpio_buttons.items():
            if button.is_pressed():
                self._enqueue(logical)

    def consume(self) -> List[str]:
        pressed = list(self._queue)
        self._queue.clear()
        return pressed
