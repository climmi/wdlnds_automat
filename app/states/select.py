import pygame

from .. import config
from ..ui import draw_glow_panel, draw_glow_text, draw_text
from .base import BaseState


class GameSelectState(BaseState):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._options = [
            ("beatline", "BEATLINE"),
            ("light_ops", "LIGHT OPS"),
            ("crowd_control", "CROWD CTRL"),
        ]
        self._index = 0

    def on_enter(self) -> None:
        if self.app.credits <= 0:
            self.app.state_machine.change("idle")
            return
        # keep last selected if possible
        for idx, (gid, _) in enumerate(self._options):
            if gid == self.app.current_game:
                self._index = idx
                break

    def handle_input(self, pressed):
        if "left" in pressed:
            self._index = (self._index - 1) % len(self._options)
        if "right" in pressed:
            self._index = (self._index + 1) % len(self._options)
        if "middle" in pressed or "start" in pressed:
            self._start_game()

    def update(self, dt: float) -> None:
        if self.app.credits <= 0:
            self.app.state_machine.change("idle")

    def render(self, surface) -> None:
        self.app.draw_background(surface)
        title_font = self.app.fonts["title"]
        body_font = self.app.fonts["body"]

        draw_glow_text(surface, "WOODLANDS NIGHT SELECT", title_font, config.COLOR_TEXT,
                       (self.app.center_x, 96), config.COLOR_ACCENT_CYAN, glow_radius=5)
        draw_text(surface, "CHOOSE THE NEXT FLOOR MOMENT", body_font, config.COLOR_TEXT_SOFT,
                  (self.app.center_x, 136))

        stage_rect = pygame.Rect(54, 170, self.app.width - 108, self.app.height - 120)
        draw_glow_panel(surface, stage_rect, (12, 15, 22), config.COLOR_BG_GRID, config.COLOR_BG_GRID, border=1)
        self._draw_stage_header(surface, stage_rect)

        card_w = 254
        gap = 24
        start_x = self.app.center_x - (card_w * 3 + gap * 2) // 2
        card_y = 238
        palettes = [
            (config.COLOR_ACCENT_CYAN, "DJ SET / CUE / DROP"),
            (config.COLOR_ACCENT_GOLD, "SHOW CUES / LIGHTS"),
            (config.COLOR_ACCENT_HOT, "CROWDWORK / HYPE"),
        ]
        icons = ["|||", "<+>", "OOO"]
        for idx, ((_, name), (accent, subline)) in enumerate(zip(self._options, palettes)):
            rect = pygame.Rect(start_x + idx * (card_w + gap), card_y, card_w, 156)
            selected = idx == self._index
            bg = (15, 19, 28) if selected else (17, 21, 29)
            if selected:
                draw_glow_panel(surface, rect, bg, accent, accent)
            else:
                draw_glow_panel(surface, rect, bg, config.COLOR_BG_GRID, accent, border=1)
            self._draw_card_art(surface, rect, accent, selected, idx)
            draw_text(surface, icons[idx], self.app.fonts["mega"], accent, (rect.centerx, rect.top + 30))
            draw_text(surface, name, body_font, config.COLOR_TEXT, (rect.centerx, rect.top + 82))
            draw_text(surface, subline, body_font, config.COLOR_TEXT_SOFT, (rect.centerx, rect.top + 116))
            draw_text(surface, f"PRESS {idx + 1}", self.app.fonts["body"], accent, (rect.centerx, rect.bottom - 18))

        game_id, _ = self._options[self._index]
        status = self.app.highscores.get_status(game_id)
        footer_rect = pygame.Rect(stage_rect.left + 28, stage_rect.bottom - 72, stage_rect.width - 56, 44)
        draw_glow_panel(surface, footer_rect, (10, 13, 18), config.COLOR_BG_GRID, config.COLOR_BG_GRID, border=1)
        draw_text(surface, f"HIGHSCORE  {status.top_name}  {status.top_score}", body_font,
                  config.COLOR_TEXT, (footer_rect.centerx, footer_rect.centery))

    def _draw_stage_header(self, surface, rect: pygame.Rect) -> None:
        top_band = pygame.Rect(rect.left + 28, rect.top + 24, rect.width - 56, 32)
        pygame.draw.rect(surface, (20, 24, 33), top_band, border_radius=10)
        for idx, color in enumerate((config.COLOR_ACCENT_CYAN, config.COLOR_ACCENT_GOLD, config.COLOR_ACCENT_HOT)):
            x = top_band.left + 22 + idx * 26
            pygame.draw.circle(surface, color, (x, top_band.centery), 6)
        draw_text(surface, "MAIN FLOOR / DJ BOOTH / CROWD PIT", self.app.fonts["body"], config.COLOR_TEXT_SOFT,
                  (top_band.centerx + 40, top_band.centery))

    def _draw_card_art(self, surface, rect: pygame.Rect, accent, selected: bool, idx: int) -> None:
        art = pygame.Surface((rect.width - 28, 44), pygame.SRCALPHA)
        if idx == 0:
            for lane in range(3):
                x = 20 + lane * 70
                pygame.draw.rect(art, (*accent, 70 if selected else 38), (x, 4, 42, 34), border_radius=8)
                pygame.draw.line(art, (255, 255, 255, 120), (x + 6, 11), (x + 36, 11), 2)
        elif idx == 1:
            pygame.draw.rect(art, (*accent, 80 if selected else 42), (18, 8, 58, 20), border_radius=6)
            pygame.draw.polygon(art, (*config.COLOR_ACCENT_CYAN, 80 if selected else 42), [(122, 6), (164, 36), (82, 36)])
            pygame.draw.polygon(art, (*config.COLOR_ACCENT_HOT, 80 if selected else 42), [(192, 6), (234, 36), (152, 36)])
        else:
            for row in range(2):
                for col in range(8):
                    px = 18 + col * 26
                    py = 6 + row * 18
                    pygame.draw.rect(art, (*accent, 84 if (row + col) % 2 == 0 else 36), (px, py, 16, 12), border_radius=3)
        surface.blit(art, (rect.left + 14, rect.top + 18))

    def _start_game(self) -> None:
        game_id, _ = self._options[self._index]
        self.app.current_game = game_id
        self.app.consume_credit()
        if game_id == "beatline":
            self.app.state_machine.change("minigame")
        elif game_id == "light_ops":
            self.app.state_machine.change("timing")
        else:
            self.app.state_machine.change("hold")
