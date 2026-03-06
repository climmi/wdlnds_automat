import time
from typing import Optional

import pygame

from .. import config
from .gpio import GpioButton
from .buttons import KEY_LOOKUP


class CoinSensor:
    def __init__(self) -> None:
        self._gpio_button: Optional[GpioButton] = None
        self._gpio_last_state = False
        self._last_trigger = 0.0
        self._triggered = False

    def attach_gpio(self, pin: int) -> None:
        self._gpio_button = GpioButton(pin)
        self._gpio_button.set_on_press(self._enqueue)
        self._gpio_last_state = self._gpio_button.is_pressed()

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
        if self._gpio_button is None:
            return
        was_pressed = self._gpio_last_state
        is_pressed = self._gpio_button.is_pressed()
        if is_pressed and not was_pressed:
            self._enqueue()
        self._gpio_last_state = is_pressed

    def consume(self) -> bool:
        if self._triggered:
            self._triggered = False
            return True
        return False

    def gpio_state(self) -> bool:
        if self._gpio_button is None:
            return False
        return self._gpio_button.is_pressed()
