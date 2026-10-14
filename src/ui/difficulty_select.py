import pygame
from src.ui.theme import draw_background, draw_wood_panel, draw_button, font, YELLOW


class DifficultySelect:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.options = ["EASY", "NORMAL", "HARD"]
        self.selected = 1
        self.panel = pygame.Rect(210, 70, 540, 420)
        self.back_rect = pygame.Rect(400, 420, 160, 40)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.selected].lower()
            elif event.key == pygame.K_ESCAPE:
                return "BACK"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.button_rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    return self.options[i].lower()
            if self.back_rect.collidepoint(event.pos):
                return "BACK"
        return None

    def button_rects(self):
        return [pygame.Rect(315, 185 + i * 82, 330, 58) for i in range(3)]

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "SELECT DIFFICULTY")
        for i, option in enumerate(self.options):
            draw_button(self.screen, self.button_rects()[i], option, i == self.selected)
        draw_button(self.screen, self.back_rect, "← BACK", small=True)
        hint = font(20, True).render("↑ / ↓ Select     ENTER / SPACE Choose     ESC Back", True, YELLOW)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, 470)))
