import math
import array

import pygame


class SoundManager:
    def __init__(self) -> None:
        self._enabled = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._enabled = True
        except pygame.error:
            self._enabled = False
        self._cache = {}

    def _tone(self, freq: float, duration: float, volume: float = 0.5) -> pygame.mixer.Sound:
        key = (freq, duration, volume)
        if key in self._cache:
            return self._cache[key]
        sample_rate = 22050
        length = int(sample_rate * duration)
        amp = int(32767 * volume)
        buf = array.array("h")
        for idx in range(length):
            value = int(amp * math.sin(2.0 * math.pi * freq * (idx / sample_rate)))
            buf.append(value)
        sound = pygame.mixer.Sound(buffer=buf)
        self._cache[key] = sound
        return sound

    def play_beep(self) -> None:
        return

    def play_win(self) -> None:
        return

    def play_menu(self) -> None:
        return
