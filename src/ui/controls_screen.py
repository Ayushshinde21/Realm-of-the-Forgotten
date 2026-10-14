"""Controls / help screen with key rebinding."""
from __future__ import annotations

import pygame

from src import keybinds
from src.ui.theme import (
    draw_background, draw_wood_panel, draw_button, font,
    WHITE, YELLOW, WOOD_DARK, ORANGE,
)

ROW_COUNT = len(keybinds.ACTIONS) + 2  # actions + RESET + BACK

FIXED_HELP = [
    "Attack: Left or Right mouse button",
    "Move: Arrow keys always work too",
    "Pause: ESC        Fullscreen: F11",
    "Checkpoints save your progress automatically",
]


class ControlsScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.panel = pygame.Rect(130, 15, 700, 510)
        self.selected = 0
        self.waiting_for_key = False
        self.message = ""

    def row_rect(self, index):
        return pygame.Rect(200, 95 + index * 52, 560, 44)

    def _activate(self, index):
        if index < len(keybinds.ACTIONS):
            self.waiting_for_key = True
            self.message = "Press the new key (ESC to cancel)"
            return None
        if index == len(keybinds.ACTIONS):
            keybinds.reset_defaults()
            self.message = "Controls reset to defaults"
            return None
        return "BACK"

    def handle_event(self, event):
        if self.waiting_for_key:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.message = ""
                elif keybinds.rebind(keybinds.ACTIONS[self.selected], event.key):
                    self.message = "Key changed"
                else:
                    self.message = "That key can't be used"
                self.waiting_for_key = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.waiting_for_key = False
                self.message = ""
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % ROW_COUNT
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % ROW_COUNT
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._activate(self.selected)
            elif event.key == pygame.K_ESCAPE:
                return "BACK"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(ROW_COUNT):
                if self.row_rect(i).collidepoint(event.pos):
                    self.selected = i
                    return self._activate(i)
        return None

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "CONTROLS")
        for i, action in enumerate(keybinds.ACTIONS):
            rect = self.row_rect(i)
            pygame.draw.rect(self.screen, ORANGE if i == self.selected else WOOD_DARK, rect, border_radius=10)
            label = font(28, True).render(keybinds.ACTION_LABELS[action], True, WHITE)
            self.screen.blit(label, (rect.left + 16, rect.centery - label.get_height() // 2))
            waiting = self.waiting_for_key and i == self.selected
            key_text = "..." if waiting else keybinds.key_name(action)
            key = font(28, True).render(key_text, True, YELLOW)
            self.screen.blit(key, (rect.right - key.get_width() - 16, rect.centery - key.get_height() // 2))
        n = len(keybinds.ACTIONS)
        draw_button(self.screen, self.row_rect(n), "RESET TO DEFAULTS", self.selected == n, small=True)
        draw_button(self.screen, self.row_rect(n + 1), "BACK", self.selected == n + 1, small=True)

        y = self.row_rect(n + 1).bottom + 22
        for line in FIXED_HELP:
            text = font(22, True).render(line, True, WHITE)
            self.screen.blit(text, text.get_rect(center=(self.width // 2, y)))
            y += 24
        if self.message:
            msg = font(22, True).render(self.message, True, YELLOW)
            self.screen.blit(msg, msg.get_rect(center=(self.width // 2, self.panel.top + 62)))
