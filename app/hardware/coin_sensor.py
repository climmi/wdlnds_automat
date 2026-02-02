import time
from typing import Optional

import pygame

from .. import config
from .gpio import GpioButton
from .buttons import KEY_LOOKUP


class CoinSensor:
    def __init__(self) -> None:
        self._gpio_button: Optional[GpioButton] = None
        self._last_trigger = 0.0
        self._triggered = False

    def attach_gpio(self, pin: int) -> None:
        self._gpio_button = GpioButton(pin)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        for key in config.KEYMAP["coin"]:
            if event.key == KEY_LOOKUP.get(key):
                self._enqueue()

    def _enqueue(self) -> None:
        now = time.time()
        if (now - self._last_trigger) * 1000.0 < config.COIN_DEBOUNCE_MS:
            return
        self._last_trigger = now
        self._triggered = True

    def update(self) -> None:
        if self._gpio_button and self._gpio_button.is_pressed():
            self._enqueue()

    def consume(self) -> bool:
        if self._triggered:
            self._triggered = False
            return True
        return False
