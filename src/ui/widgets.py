import pygame
from src.ui.theme import font, WHITE, WOOD_DARK, WOOD_SHADOW, SILVER, ORANGE_LIGHT


class TextField:
    def __init__(self, key, label, rect, password=False):
        self.key = key
        self.label = label
        self.rect = pygame.Rect(rect)
        self.password = password
        self.value = ""

    def draw(self, screen, focused):
        border = ORANGE_LIGHT if focused else SILVER
        pygame.draw.rect(screen, WOOD_SHADOW, self.rect.move(0, 3), border_radius=8)
        pygame.draw.rect(screen, border, self.rect, border_radius=8)
        pygame.draw.rect(screen, WOOD_DARK, self.rect.inflate(-4, -4), border_radius=6)

        display = self.value
        if self.password:
            display = "*" * len(self.value)
        if display:
            text = font(20).render(display, True, WHITE)
        else:
            text = font(20).render(self.label, True, (150, 130, 110))
        screen.blit(text, (self.rect.left + 12, self.rect.centery - text.get_height() // 2))

        if focused:
            cursor_x = self.rect.left + 12 + (font(20).size(display)[0] if display else 0) + 2
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                pygame.draw.line(screen, WHITE, (cursor_x, self.rect.top + 8), (cursor_x, self.rect.bottom - 8), 2)

    def handle_key(self, event):
        """Handle a KEYDOWN event while this field is focused.
        Returns True if the event was consumed as text input."""
        if event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
            return True
        if event.unicode and event.unicode.isprintable():
            if len(self.value) < 40:
                self.value += event.unicode
            return True
        return False
