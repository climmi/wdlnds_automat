import math
import array
import os
import random
import time

import pygame

from .. import config


class SoundManager:
    def __init__(self) -> None:
        self._enabled = False
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=4096)
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=4096)
            self._enabled = True
        except pygame.error:
            self._enabled = False
        self._cache = {}
        self._effects_dir = os.path.abspath(os.path.join(config.BASE_DIR, os.pardir, "audio", "soundeffects"))
        self._standby_channel = None
        self._scoreboard_channel = None
        self._standby_rotation_next = 0.0
        self._standby_rotation_active = False
        if self._enabled:
            pygame.mixer.set_num_channels(8)
            self._standby_channel = pygame.mixer.Channel(0)
            self._scoreboard_channel = pygame.mixer.Channel(1)

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

    def _effect(self, filename: str):
        if not self._enabled:
            return None
        key = ("file", filename)
        if key in self._cache:
            return self._cache[key]
        path = os.path.join(self._effects_dir, filename)
        if not os.path.exists(path):
            return None
        try:
            sound = pygame.mixer.Sound(path)
        except pygame.error:
            return None
        self._cache[key] = sound
        return sound

    def _play_effect(self, filename: str, volume: float = 0.85) -> None:
        sound = self._effect(filename)
        if sound is None:
            return
        sound.set_volume(volume)
        channel_index = 2 + (sum(ord(char) for char in filename) % 6)
        pygame.mixer.Channel(channel_index).play(sound)

    def play_beep(self) -> None:
        if not self._enabled:
            return
        self._tone(880, 0.045, 0.18).play()

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
        self.stop_standby_loop()
        self.stop_scoreboard_loop()
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.82)
            pygame.mixer.music.play()
        except pygame.error:
            return

    def stop_music(self) -> None:
        if not self._enabled:
            return
        pygame.mixer.music.stop()

    def play_standby_loop(self) -> None:
        if not self._enabled or self._standby_channel is None:
            return
        if self._standby_channel.get_busy():
            return
        sound = self._effect("standby_sound_loop.mp3")
        if sound is None:
            return
        sound.set_volume(0.42)
        self._standby_channel.play(sound, loops=-1)

    def stop_standby_loop(self) -> None:
        if self._enabled and self._standby_channel is not None:
            self._standby_channel.stop()

    def play_scoreboard_loop(self) -> None:
        if not self._enabled or self._scoreboard_channel is None:
            return
        self.stop_standby_loop()
        self._standby_rotation_active = False
        if self._scoreboard_channel.get_busy():
            return
        sound = self._effect("scoreboard_sound.mp3")
        if sound is None:
            return
        sound.set_volume(0.55)
        self._scoreboard_channel.play(sound, loops=-1)

    def stop_scoreboard_loop(self) -> None:
        if self._enabled and self._scoreboard_channel is not None:
            self._scoreboard_channel.stop()
        self._standby_rotation_active = False

    def start_standby_ambient(self) -> None:
        if not self._enabled:
            return
        self.stop_scoreboard_loop()
        self.play_standby_loop()
        self._schedule_standby_scoreboard()

    def update_standby_ambient(self) -> None:
        if not self._enabled or self._scoreboard_channel is None:
            return
        now = time.time()
        if self._standby_rotation_active:
            if not self._scoreboard_channel.get_busy():
                self._standby_rotation_active = False
                self.play_standby_loop()
                self._schedule_standby_scoreboard(now)
            return

        self.play_standby_loop()
        if self._standby_rotation_next and now >= self._standby_rotation_next:
            sound = self._effect("scoreboard_sound.mp3")
            if sound is None:
                self._schedule_standby_scoreboard(now)
                return
            self.stop_standby_loop()
            sound.set_volume(0.50)
            self._scoreboard_channel.play(sound, loops=0)
            self._standby_rotation_active = True

    def stop_standby_ambient(self) -> None:
        self.stop_standby_loop()
        self.stop_scoreboard_loop()

    def _schedule_standby_scoreboard(self, now: float | None = None) -> None:
        now = time.time() if now is None else now
        self._standby_rotation_next = now + random.uniform(15 * 60, 60 * 60)

    def play_coin(self) -> None:
        self._play_effect("coin_einwurf.mp3", 0.9)

    def play_combo(self, level: int) -> None:
        if level < 1 or level > 4:
            return
        self._play_effect(f"combo_{level}.mp3", 0.9)

    def play_streak_break(self) -> None:
        self._play_effect("streak_break.mp3", 0.9)

    def play_game_over_early(self) -> None:
        self._play_effect("game_over_early.mp3", 0.95)
