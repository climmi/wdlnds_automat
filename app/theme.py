import pygame

from . import config


def draw_dynamic_background(surface: pygame.Surface, t: float) -> None:
    surface.fill((249, 246, 232))


def draw_energy_blob(surface: pygame.Surface, center: tuple, radius: int, color) -> None:
    return None


def create_background(width: int, height: int) -> pygame.Surface:
    surface = pygame.Surface((width, height))
    surface.fill((249, 246, 232))
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
    surface.blit(render, rect)


def create_scanlines(width: int, height: int) -> pygame.Surface:
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    return overlay
