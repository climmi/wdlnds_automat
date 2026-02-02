import pygame


def draw_text(surface, text, font, color, center):
    render = font.render(text, True, color)
    rect = render.get_rect(center=center)
    surface.blit(render, rect)


def draw_panel(surface, rect, color, border_color=None, border=2, shadow=True):
    if shadow:
        shadow_rect = rect.move(6, 6)
        pygame.draw.rect(surface, (0, 0, 0, 40), shadow_rect, border_radius=12)
    pygame.draw.rect(surface, color, rect, border_radius=12)
    if border_color:
        pygame.draw.rect(surface, border_color, rect, width=border, border_radius=12)
