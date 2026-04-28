import pygame


def draw_text(surface, text, font, color, center):
    render = font.render(text, True, color)
    rect = render.get_rect(center=center)
    surface.blit(render, rect)
    return rect


def draw_glow_text(surface, text, font, color, center, glow_color, glow_radius: int = 4):
    base = font.render(text, True, color)
    rect = base.get_rect(center=center)

    glow = pygame.Surface((rect.width + glow_radius * 4, rect.height + glow_radius * 4), pygame.SRCALPHA)
    glow_center = glow.get_rect().center
    for dx, dy in ((-glow_radius, 0), (glow_radius, 0), (0, -glow_radius), (0, glow_radius)):
        shadow = font.render(text, True, glow_color)
        shadow_rect = shadow.get_rect(center=(glow_center[0] + dx, glow_center[1] + dy))
        glow.blit(shadow, shadow_rect)
    surface.blit(glow, glow.get_rect(center=center), special_flags=pygame.BLEND_RGBA_ADD)
    surface.blit(base, rect)
    return rect


def draw_panel(surface, rect, color, border_color=None, border=2, shadow=True):
    if shadow:
        shadow_rect = rect.move(6, 6)
        pygame.draw.rect(surface, (0, 0, 0, 40), shadow_rect, border_radius=12)
    pygame.draw.rect(surface, color, rect, border_radius=12)
    if border_color:
        pygame.draw.rect(surface, border_color, rect, width=border, border_radius=12)


def draw_glow_panel(surface, rect, color, border_color, glow_color, border: int = 2, radius: int = 18):
    glow = pygame.Surface((rect.width + 48, rect.height + 48), pygame.SRCALPHA)
    glow_rect = glow.get_rect(center=rect.center)
    for inflate, alpha in ((32, 24), (18, 36), (8, 56)):
        pygame.draw.rect(
            glow,
            (*glow_color, alpha),
            pygame.Rect(24 - inflate // 2, 24 - inflate // 2, rect.width + inflate, rect.height + inflate),
            border_radius=radius + 8,
        )
    surface.blit(glow, glow_rect, special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, width=border, border_radius=radius)


def draw_orb(surface, center, radius: int, color, alpha: int = 170):
    orb = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    cx = cy = radius * 2
    for idx, mult in enumerate((1.9, 1.4, 1.0)):
        r = max(2, int(radius * mult))
        a = max(18, alpha // (idx + 2))
        pygame.draw.circle(orb, (*color, a), (cx, cy), r)
    pygame.draw.circle(orb, (*color, min(255, alpha + 40)), (cx, cy), max(2, radius // 2))
    surface.blit(orb, orb.get_rect(center=center), special_flags=pygame.BLEND_RGBA_ADD)
