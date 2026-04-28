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
        if not self._enabled:
            return
        self._tone(880, 0.045, 0.28).play()

    def play_win(self) -> None:
        if not self._enabled:
            return
        self._tone(660, 0.08, 0.22).play()
        self._tone(990, 0.12, 0.18).play(maxtime=120, fade_ms=10)

    def play_menu(self) -> None:
        if not self._enabled:
            return
        self._tone(540, 0.05, 0.2).play()

    def play_tick(self, downbeat: bool = False) -> None:
        if not self._enabled:
            return
        if downbeat:
            self._tone(740, 0.05, 0.24).play()
        else:
            self._tone(520, 0.03, 0.16).play()

    def play_music(self, path: str) -> None:
        if not self._enabled:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except pygame.error:
            return

    def stop_music(self) -> None:
        if not self._enabled:
            return
        pygame.mixer.music.stop()
