"""Scrolling credits shown after beating the final level."""
from __future__ import annotations

import pygame

from src.settings import TITLE, VERSION
from src.ui.theme import draw_background, font, WHITE, YELLOW

LINES = [
    ("THE END", 64, YELLOW),
    ("", 30, WHITE),
    ("You rescued Snackland!", 36, WHITE),
    ("", 40, WHITE),
    (TITLE, 30, YELLOW),
    ("", 40, WHITE),
    ("Game design and programming", 26, YELLOW),
    ("Your Name Here", 34, WHITE),
    ("", 30, WHITE),
    ("Made with Python and pygame", 26, WHITE),
    ("", 30, WHITE),
    ("Thank you for playing!", 38, YELLOW),
    ("", 30, WHITE),
    (f"Version {VERSION}", 20, WHITE),
]
# NOTE: replace "Your Name Here" (and add more lines) with your own credits.

SPEED = 1.1  # pixels per frame


class CreditsScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.offset = 0.0

    def reset(self):
        self.offset = 0.0

    def _total_height(self):
        return sum(size + 14 for _, size, _ in LINES)

    def update(self):
        self.offset += SPEED

    def finished(self):
        return self.offset > self.height + self._total_height()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE
        ):
            return "DONE"
        if event.type == pygame.MOUSEBUTTONDOWN:
            return "DONE"
        return None

    def draw(self):
        draw_background(self.screen)
        y = self.height - self.offset
        for text, size, color in LINES:
            if text:
                surf = font(size, True).render(text, True, color)
                self.screen.blit(surf, surf.get_rect(center=(self.width // 2, int(y))))
            y += size + 14
        hint = font(18, True).render("Press ESC / ENTER to skip", True, YELLOW)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 16)))
