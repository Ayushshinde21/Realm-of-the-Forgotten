import pygame
from src.ui.theme import draw_background, draw_wood_panel, draw_button, draw_star, font, WHITE, YELLOW, GOLD
from src.systems.achievements import ACHIEVEMENTS


class Achievements:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.panel = pygame.Rect(105, 35, 750, 470)
        self.selected = 0
        self.state = {a["id"]: False for a in ACHIEVEMENTS}

    def set_state(self, state):
        self.state.update(state or {})

    def reset(self):
        """Clears achievement state back to defaults - call this before
        loading a different user's achievements."""
        self.state = {a["id"]: False for a in ACHIEVEMENTS}
        self.selected = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w): self.selected = (self.selected - 1) % len(ACHIEVEMENTS)
            elif event.key in (pygame.K_DOWN, pygame.K_s): self.selected = (self.selected + 1) % len(ACHIEVEMENTS)
            elif event.key == pygame.K_ESCAPE: return "BACK"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(110, 455, 170, 40).collidepoint(event.pos): return "BACK"
        return None

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "ACHIEVEMENTS")
        y = 125
        for i, a in enumerate(ACHIEVEMENTS):
            unlocked = self.state.get(a["id"], False)
            row = pygame.Rect(145, y, 670, 58)
            pygame.draw.rect(self.screen, (65, 43, 25) if i != self.selected else (92, 56, 28), row, border_radius=10)
            draw_star(self.screen, (175, y + 29), 18, unlocked, color=a.get("icon_color"))
            name = font(24, True).render(a["name"], True, WHITE)
            desc = font(17).render(a["description"], True, YELLOW)
            self.screen.blit(name, (205, y + 7))
            self.screen.blit(desc, (205, y + 33))
            if unlocked:
                draw_button(self.screen, pygame.Rect(705, y + 9, 85, 40), "✓ GOT", small=True, color_override=GOLD)
            else:
                draw_button(self.screen, pygame.Rect(705, y + 9, 85, 40), "GET", enabled=False, small=True)
            y += 65
        draw_button(self.screen, pygame.Rect(110, 455, 170, 40), "← BACK", small=True)
