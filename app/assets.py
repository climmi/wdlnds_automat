import os
from typing import Optional

import pygame


class ImageManager:
    def __init__(self, base_dir: str) -> None:
        self._image_dir = os.path.join(base_dir, "assets", "images")

    def load(self, filename: str, size: Optional[tuple] = None) -> Optional[pygame.Surface]:
        path = os.path.join(self._image_dir, filename)
        if not os.path.exists(path):
            return None
        image = pygame.image.load(path).convert_alpha()
        if size:
            image = pygame.transform.smoothscale(image, size)
        return image
