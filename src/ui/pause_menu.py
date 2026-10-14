import pygame
from src.ui.theme import draw_wood_panel, draw_button, font, YELLOW


class PauseMenu:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.options = ["RESUME", "SETTINGS", "MAIN MENU"]
        self.selected = 0
        self.panel = pygame.Rect(190, 65, 580, 410)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w): self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s): self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE): return self.options[self.selected]
            elif event.key == pygame.K_ESCAPE: return "RESUME"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.button_rects()):
                if rect.collidepoint(event.pos): self.selected = i; return self.options[i]
        return None

    def button_rects(self): return [pygame.Rect(315, 175 + i * 80, 330, 56) for i in range(len(self.options))]

    def draw(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        draw_wood_panel(self.screen, self.panel, "PAUSED")
        for i, option in enumerate(self.options): draw_button(self.screen, self.button_rects()[i], option, i == self.selected)
        hint = font(18, True).render("ESC Resume", True, YELLOW)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, 455)))
