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
        self._gpio_last_state: Dict[str, bool] = {}
        self._keyboard_held: Dict[str, bool] = {}
        self._gpio_held: Dict[str, bool] = {}
        self._external_held: Dict[str, bool] = {}

        for logical in ("left", "middle", "right", "start"):
            self._last_pressed[logical] = 0.0
            self._keyboard_held[logical] = False
            self._gpio_held[logical] = False
            self._external_held[logical] = False

    def attach_gpio(self, mapping: Dict[str, int]) -> None:
        for logical, pin in mapping.items():
            button = GpioButton(pin)
            button.set_on_press(lambda l=logical: self._handle_gpio_press(l))
            button.set_on_release(lambda l=logical: self._handle_gpio_release(l))
            self._gpio_buttons[logical] = button
            self._gpio_last_state[logical] = button.is_pressed()
            self._gpio_held[logical] = self._gpio_last_state[logical]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type not in (pygame.KEYDOWN, pygame.KEYUP):
            return
        for logical, keys in config.KEYMAP.items():
            if logical == "coin":
                continue
            for key in keys:
                if event.key == KEY_LOOKUP.get(key):
                    if event.type == pygame.KEYDOWN:
                        self._keyboard_held[logical] = True
                        self._enqueue(logical)
                    else:
                        self._keyboard_held[logical] = False

    def _enqueue(self, logical: str) -> None:
        now = time.time()
        last = self._last_pressed.get(logical, 0.0)
        if (now - last) * 1000.0 < config.BUTTON_DEBOUNCE_MS:
            return
        self._last_pressed[logical] = now
        self._queue.append(logical)

    def _handle_gpio_press(self, logical: str) -> None:
        self._gpio_held[logical] = True
        self._enqueue(logical)

    def _handle_gpio_release(self, logical: str) -> None:
        self._gpio_held[logical] = False

    def set_external_state(self, logical: str, is_down: bool) -> None:
        if logical not in self._keyboard_held:
            return
        was_down = self._external_held.get(logical, False)
        self._external_held[logical] = bool(is_down)
        if is_down and not was_down:
            self._enqueue(logical)

    def update(self) -> None:
        # Fallback polling for environments where gpiozero callbacks do not fire reliably.
        for logical, button in self._gpio_buttons.items():
            was_pressed = self._gpio_last_state.get(logical, False)
            is_pressed = button.is_pressed()
            self._gpio_held[logical] = is_pressed
            if is_pressed and not was_pressed:
                self._enqueue(logical)
            self._gpio_last_state[logical] = is_pressed

    def consume(self) -> List[str]:
        pressed = list(self._queue)
        self._queue.clear()
        return pressed

    def gpio_states(self) -> Dict[str, bool]:
        return {name: button.is_pressed() for name, button in self._gpio_buttons.items()}

    def is_down(self, logical: str) -> bool:
        return bool(
            self._keyboard_held.get(logical, False)
            or self._gpio_held.get(logical, False)
            or self._external_held.get(logical, False)
        )
