import os
import pygame

from . import config


class FontManager:
    def __init__(self, base_dir: str) -> None:
        self._font_dir = os.path.join(base_dir, "assets", "fonts")

    def _load(self, filename: str, size: int) -> pygame.font.Font:
        path = os.path.join(self._font_dir, filename)
        if os.path.exists(path):
            return pygame.font.Font(path, size)
        return pygame.font.SysFont(["Press Start 2P", "VT323", "Trebuchet MS", "Verdana"], size)

    def build(self) -> dict:
        return {
            "title": self._load(config.FONT_PRIMARY, 40),
            "mega": self._load(config.FONT_PRIMARY, 48),
            "big": self._load(config.FONT_PRIMARY, 42),
            "body": self._load(config.FONT_SECONDARY, 22),
            "body_bold": self._load(config.FONT_SECONDARY, 22),
        }
