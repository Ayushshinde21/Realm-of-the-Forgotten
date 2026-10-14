import math
import pygame
from src.settings import MAX_LEVELS
from src.ui.theme import draw_background, draw_wood_panel, draw_button, draw_star, font, WHITE, YELLOW, ORANGE_LIGHT

GREEN = (110, 220, 120)
RED = (210, 95, 95)


class WinScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.panel = pygame.Rect(120, 20, 720, 500)
        self.elapsed = 0
        self.stars = 1
        self.level_number = 1
        self.score = 0
        self.breakdown = None
        self.btn_menu = pygame.Rect(205, 440, 190, 50)
        self.btn_next = pygame.Rect(565, 440, 190, 50)

    def set_result(self, level_number, score, stars, breakdown=None):
        self.level_number = level_number
        self.score = score
        self.stars = max(1, min(3, stars))
        self.breakdown = breakdown
        self.elapsed = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return "NEXT" if self.level_number < MAX_LEVELS else "MENU"
            if event.key == pygame.K_ESCAPE:
                return "MENU"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_menu.collidepoint(event.pos): return "MENU"
            if self.btn_next.collidepoint(event.pos): return "NEXT" if self.level_number < MAX_LEVELS else "MENU"
        return None

    def update(self):
        self.elapsed += 1

    def _breakdown_items(self):
        """Returns the (label, met) list explaining exactly which quest
        earned (or missed) each star. There are always exactly 3 quests:
        "Completed the level" (always met) plus the 2 quests randomly
        chosen for this level - each worth exactly 1 star."""
        b = self.breakdown or {}
        quest_items = b.get("quest_items")
        if quest_items:
            return quest_items
        # Fallback if no breakdown was provided.
        return [("Completed the level", True)]

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "YOU WIN!")
        msg = font(28, True).render("CONGRATULATIONS! LEVEL COMPLETE", True, WHITE)
        self.screen.blit(msg, msg.get_rect(center=(self.width // 2, 135)))

        # Stars
        for i in range(3):
            delay = i * 12
            progress = max(0, min(1, (self.elapsed - delay) / 16))
            scale = 0.35 + 0.65 * progress
            radius = int((34 if i == 1 else 25) * scale)
            if radius > 2:
                x = self.width // 2 + (i - 1) * 85
                y = 185 if i == 1 else 192
                draw_star(self.screen, (x, y), radius, i < self.stars)

        # Breakdown: which specific objectives earned (or missed) a star
        if self.breakdown:
            start_y = 232
            line_h = 25
            for i, (label, met) in enumerate(self._breakdown_items()):
                y = start_y + i * line_h
                color = GREEN if met else RED
                mark = "✓" if met else "✗"
                line = font(19, True).render(f"{mark}  {label}", True, color)
                self.screen.blit(line, line.get_rect(midleft=(self.width // 2 - 175, y)))

        score = font(28, True).render(f"SCORE: {self.score}   +50 ⚡ XP", True, YELLOW)
        self.screen.blit(score, score.get_rect(center=(self.width // 2, 395)))

        draw_button(self.screen, self.btn_menu, "☰ MENU")
        draw_button(self.screen, self.btn_next, "→ NEXT" if self.level_number < MAX_LEVELS else "→ MENU")
