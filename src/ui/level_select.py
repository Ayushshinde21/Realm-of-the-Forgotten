import pygame

from src.settings import MAX_LEVELS, WORLD_LEVEL_COUNT, WORLD_NAMES
from src.ui.theme import draw_background, draw_wood_panel, draw_button, draw_star, font, YELLOW

COLS = 5
TILE_W = 118
TILE_H = 48
GAP_X = 18
GAP_Y = 18
WORLD_TOPS = {1: 116, 2: 290}
WORLD_HEADER_Y = {1: 98, 2: 272}


class LevelSelect:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.levels = [
            {"name": f"LEVEL {i}", "unlocked": i == 1, "stars": 0}
            for i in range(1, MAX_LEVELS + 1)
        ]
        self.selected = 0
        self.panel = pygame.Rect(65, 25, 830, 485)

    def unlock_level(self, level_number):
        if 1 <= level_number <= len(self.levels):
            self.levels[level_number - 1]["unlocked"] = True

    def reset(self):
        """Reset campaign progress before loading another user's save."""
        self.levels = [
            {"name": f"LEVEL {i}", "unlocked": i == 1, "stars": 0}
            for i in range(1, MAX_LEVELS + 1)
        ]
        self.selected = 0

    def set_stars(self, stars):
        for number in range(1, MAX_LEVELS + 1):
            self.levels[number - 1]["stars"] = int(stars.get(str(number), stars.get(number, 0)))

    def handle_event(self, event):
        count = len(self.levels)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % count
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % count
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - COLS) % count
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + COLS) % count
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.selected + 1 if self.levels[self.selected]["unlocked"] else None
            elif event.key == pygame.K_ESCAPE:
                return "BACK"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.tile_rects()):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    if self.levels[index]["unlocked"]:
                        return index + 1
        return None

    def tile_rects(self):
        total_width = COLS * TILE_W + (COLS - 1) * GAP_X
        start_x = (self.width - total_width) // 2
        rects = []
        for index in range(MAX_LEVELS):
            world_number = 1 if index < WORLD_LEVEL_COUNT else 2
            local_index = index % WORLD_LEVEL_COUNT
            row, col = divmod(local_index, COLS)
            x = start_x + col * (TILE_W + GAP_X)
            y = WORLD_TOPS[world_number] + row * (TILE_H + GAP_Y)
            rects.append(pygame.Rect(x, y, TILE_W, TILE_H))
        return rects

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "CHOOSE WORLD & LEVEL")

        for world_number in (1, 2):
            label = (
                f"WORLD {world_number}  •  {WORLD_NAMES[world_number].upper()}"
                f"  •  LEVELS {((world_number - 1) * WORLD_LEVEL_COUNT) + 1}-"
                f"{world_number * WORLD_LEVEL_COUNT}"
            )
            heading = font(18, True).render(label, True, YELLOW)
            self.screen.blit(
                heading,
                heading.get_rect(center=(self.width // 2, WORLD_HEADER_Y[world_number])),
            )

        for index, (level, rect) in enumerate(zip(self.levels, self.tile_rects())):
            unlocked = level["unlocked"]
            selected = index == self.selected
            draw_button(
                self.screen,
                rect,
                str(index + 1),
                selected and unlocked,
                enabled=unlocked,
            )
            if not unlocked:
                lock = font(12, True).render("LOCKED", True, (150, 150, 150))
                self.screen.blit(lock, lock.get_rect(center=(rect.centerx, rect.bottom - 9)))
            for star_index in range(3):
                draw_star(
                    self.screen,
                    (rect.centerx - 18 + star_index * 18, rect.bottom + 9),
                    6,
                    unlocked and star_index < level["stars"],
                )

        hint = font(16, True).render(
            "ARROWS / WASD Select     ENTER / SPACE Play     ESC Back",
            True,
            YELLOW,
        )
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, 492)))
