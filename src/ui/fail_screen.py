import pygame
from src.ui.theme import draw_background, draw_wood_panel, draw_button, draw_star, font, WHITE, YELLOW


class FailScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.panel = pygame.Rect(180, 60, 600, 420)
        self.btn_back = pygame.Rect(220, 400, 190, 50)
        self.btn_retry = pygame.Rect(550, 400, 190, 50)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE): return "RETRY"
            if event.key == pygame.K_ESCAPE: return "MENU"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.collidepoint(event.pos): return "MENU"
            if self.btn_retry.collidepoint(event.pos): return "RETRY"
        return None

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "FAILED")
        for x in (355, 480, 605):
            draw_star(self.screen, (x, 235), 34, False)
        msg = font(34, True).render("SORRY :( LEVEL FAILED", True, WHITE)
        self.screen.blit(msg, msg.get_rect(center=(self.width // 2, 305)))
        draw_button(self.screen, self.btn_back, "← BACK")
        draw_button(self.screen, self.btn_retry, "↺ RETRY")
