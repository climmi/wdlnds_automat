import math
import random
import pygame

from . import config


def create_background(width: int, height: int) -> pygame.Surface:
    surface = pygame.Surface((width, height))

    top = config.COLOR_BG_TOP
    bottom = config.COLOR_BG_BOTTOM
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

    blob = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.circle(blob, config.COLOR_BLOB_GREEN, (int(width * 0.15), int(height * 0.2)), int(height * 0.35))
    pygame.draw.circle(blob, config.COLOR_BLOB_ORANGE, (int(width * 0.8), int(height * 0.15)), int(height * 0.28))
    pygame.draw.circle(blob, config.COLOR_BLOB_BLUE, (int(width * 0.7), int(height * 0.75)), int(height * 0.4))
    surface.blit(blob, (0, 0))

    rng = random.Random(7)
    for _ in range(140):
        x = rng.randrange(0, width)
        y = rng.randrange(0, height)
        radius = rng.randrange(1, 3)
        color = rng.choice([config.COLOR_DOT_1, config.COLOR_DOT_2, config.COLOR_DOT_3])
        pygame.draw.circle(surface, color, (x, y), radius)

    pixel = pygame.Surface((width, height), pygame.SRCALPHA)
    grid = 24
    for y in range(0, height, grid):
        for x in range(0, width, grid):
            if rng.random() < 0.08:
                pygame.draw.rect(pixel, (*config.COLOR_PIXEL_1, 120), (x + 2, y + 2, 6, 6))
    for x in range(0, width, 18):
        if rng.random() < 0.2:
            pygame.draw.rect(pixel, (*config.COLOR_PIXEL_2, 140), (x, 8, 4, 4))
            pygame.draw.rect(pixel, (*config.COLOR_PIXEL_2, 140), (x, height - 12, 4, 4))
    surface.blit(pixel, (0, 0))

    return surface


def draw_frame(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, config.COLOR_FRAME_EDGE, rect, width=4, border_radius=18)
    inner = rect.inflate(-10, -10)
    pygame.draw.rect(surface, config.COLOR_FRAME, inner, width=2, border_radius=16)


def draw_stickers(surface: pygame.Surface, width: int, height: int) -> None:
    sticker_size = 62
    positions = [
        (int(width * 0.12), int(height * 0.12)),
        (int(width * 0.84), int(height * 0.18)),
        (int(width * 0.2), int(height * 0.78)),
    ]
    colors = [config.COLOR_STICKER_1, config.COLOR_STICKER_2, config.COLOR_STICKER_3]
    for (x, y), color in zip(positions, colors):
        rect = pygame.Rect(x, y, sticker_size, sticker_size)
        pygame.draw.rect(surface, color, rect, border_radius=12)
        pygame.draw.rect(surface, (255, 255, 255), rect, width=2, border_radius=12)


def draw_logo(surface: pygame.Surface, center: tuple, font: pygame.font.Font) -> None:
    text = "WDLNDS"
    render = font.render(text, True, config.COLOR_LOGO)
    rect = render.get_rect(center=center)
    shadow = font.render(text, True, (255, 255, 255))
    shadow_rect = shadow.get_rect(center=(center[0] + 2, center[1] + 2))
    surface.blit(shadow, shadow_rect)
    surface.blit(render, rect)


def create_scanlines(width: int, height: int) -> pygame.Surface:
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(0, height, 4):
        pygame.draw.line(overlay, config.COLOR_CRT, (0, y), (width, y))
    return overlay
