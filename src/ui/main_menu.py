import pygame
from src.ui.theme import draw_background, draw_wood_panel, draw_button, font, YELLOW
from src.systems import session
from src.settings import VERSION


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.options = ["PLAY", "ACHIEVEMENTS", "SETTINGS", "LOGOUT", "QUIT"]
        self.selected = 0
        self.panel = pygame.Rect(190, 45, 580, 450)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w): self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s): self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE): return self.options[self.selected]
            elif event.key == pygame.K_ESCAPE: return "QUIT"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.button_rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    return self.options[i]
        return None

    def button_rects(self):
        return [pygame.Rect(315, 165 + i * 58, 330, 48) for i in range(len(self.options))]

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "VEGGIE QUEST")
        display_name = session.get_display_name() or "Player"
        subtitle = font(20, True).render(f"WELCOME, {display_name.upper()}!", True, YELLOW)
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, 145)))
        for i, option in enumerate(self.options):
            draw_button(self.screen, self.button_rects()[i], option, i == self.selected)
        hint = font(18, True).render("↑ / ↓ Select     ENTER / SPACE Choose", True, YELLOW)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, 470)))
        ver = font(16, True).render(f"v{VERSION}", True, YELLOW)
        self.screen.blit(ver, ver.get_rect(bottomright=(self.panel.right - 25, self.panel.bottom - 8)))
