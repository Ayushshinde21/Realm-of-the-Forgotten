import pygame
from src.settings import MAX_LEVELS
from src.ui.theme import draw_background, draw_wood_panel, draw_button, draw_star, font, WHITE, YELLOW

COLS = 5
TILE_W = 130
TILE_H = 90
GAP_X = 20
GAP_Y = 45
GRID_TOP = 150


class LevelSelect:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.levels = [{"name": f"LEVEL {i}", "unlocked": i == 1, "stars": 0} for i in range(1, MAX_LEVELS + 1)]
        self.selected = 0
        self.panel = pygame.Rect(65, 30, 830, 480)

    def unlock_level(self, level_number):
        if 1 <= level_number <= len(self.levels): self.levels[level_number - 1]["unlocked"] = True

    def reset(self):
        """Clears progress back to defaults - call this before loading a
        different user's progress so a previous user's unlocks don't leak."""
        self.levels = [{"name": f"LEVEL {i}", "unlocked": i == 1, "stars": 0} for i in range(1, MAX_LEVELS + 1)]
        self.selected = 0

    def set_stars(self, stars):
        for i in range(1, MAX_LEVELS + 1):
            self.levels[i - 1]["stars"] = int(stars.get(str(i), stars.get(i, 0)))

    def handle_event(self, event):
        n = len(self.levels)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % n
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % n
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - COLS) % n
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + COLS) % n
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.selected + 1 if self.levels[self.selected]["unlocked"] else None
            elif event.key == pygame.K_ESCAPE: return "BACK"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.tile_rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    if self.levels[i]["unlocked"]: return i + 1
        return None

    def tile_rects(self):
        n = len(self.levels)
        cols = min(COLS, n)
        total_width = cols * TILE_W + (cols - 1) * GAP_X
        start_x = (self.width - total_width) // 2
        rects = []
        for i in range(n):
            row, col = divmod(i, COLS)
            x = start_x + col * (TILE_W + GAP_X)
            y = GRID_TOP + row * (TILE_H + GAP_Y)
            rects.append(pygame.Rect(x, y, TILE_W, TILE_H))
        return rects

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "LEVELS")
        for i, (level, rect) in enumerate(zip(self.levels, self.tile_rects())):
            unlocked = level["unlocked"]
            selected = i == self.selected
            draw_button(self.screen, rect, str(i + 1), selected and unlocked, enabled=unlocked)
            if not unlocked:
                lock = font(14, True).render("LOCKED", True, (150, 150, 150))
                self.screen.blit(lock, lock.get_rect(center=(rect.centerx, rect.bottom - 14)))
            for s in range(3):
                draw_star(self.screen, (rect.centerx - 26 + s * 26, rect.bottom + 14), 9, unlocked and s < level["stars"])
        hint = font(17, True).render("ARROWS / WASD Select     ENTER / SPACE Play     ESC Back", True, YELLOW)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, 500)))
