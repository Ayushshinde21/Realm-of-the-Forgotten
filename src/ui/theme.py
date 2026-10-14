import math
import pygame

WOOD_DARK = (55, 35, 20)
WOOD = (101, 67, 33)
WOOD_LIGHT = (145, 96, 48)
WOOD_HIGHLIGHT = (178, 122, 62)
WOOD_SHADOW = (68, 42, 22)
SILVER = (175, 180, 185)
SILVER_DARK = (85, 90, 95)
ORANGE = (224, 116, 35)
ORANGE_LIGHT = (255, 165, 65)
WHITE = (255, 255, 255)
YELLOW = (255, 220, 80)
GREY = (110, 110, 110)
DARK_GREY = (55, 55, 55)
GOLD = (245, 190, 45)


_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        f = pygame.font.Font(None, size)
        f.set_bold(bold)
        _font_cache[key] = f
    return _font_cache[key]


def draw_wood_panel(screen, rect, title):
    rect = pygame.Rect(rect)
    pygame.draw.rect(screen, (20, 16, 12), rect.inflate(10, 10), border_radius=18)
    pygame.draw.rect(screen, WOOD_DARK, rect, border_radius=16)
    pygame.draw.rect(screen, WOOD, rect.inflate(-10, -10), border_radius=12)

    inner = rect.inflate(-18, -18)
    for y in range(inner.top + 10, inner.bottom, 13):
        pygame.draw.line(screen, WOOD_SHADOW, (inner.left, y), (inner.right, y + 2), 1)
    for y in range(inner.top + 16, inner.bottom, 29):
        pygame.draw.line(screen, WOOD_LIGHT, (inner.left + 12, y), (inner.right - 20, y - 1), 1)

    for x, y in ((rect.left + 18, rect.top + 18), (rect.right - 18, rect.top + 18),
                 (rect.left + 18, rect.bottom - 18), (rect.right - 18, rect.bottom - 18)):
        pygame.draw.circle(screen, SILVER_DARK, (x, y), 7)
        pygame.draw.circle(screen, SILVER, (x - 2, y - 2), 4)
        pygame.draw.circle(screen, (70, 70, 70), (x + 1, y + 1), 1)

    # Rope / chain at top
    cx = rect.centerx
    for dx in (-28, 28):
        x = cx + dx
        pygame.draw.line(screen, (45, 30, 20), (x, rect.top - 24), (x, rect.top + 10), 5)
        pygame.draw.circle(screen, WOOD_LIGHT, (x, rect.top - 10), 7)
        pygame.draw.circle(screen, WOOD_DARK, (x, rect.top - 10), 4)

    banner = pygame.Rect(rect.left + 34, rect.top + 22, rect.width - 68, 58)
    pygame.draw.rect(screen, (115, 53, 20), banner.move(0, 4), border_radius=10)
    pygame.draw.rect(screen, ORANGE, banner, border_radius=10)
    pygame.draw.rect(screen, ORANGE_LIGHT, banner.inflate(-6, -6), 2, border_radius=7)
    title_s = font(34, True).render(title, True, WHITE)
    screen.blit(title_s, title_s.get_rect(center=banner.center))
    return banner.bottom + 22


def draw_button(screen, rect, label, selected=False, enabled=True, small=False, color_override=None):
    rect = pygame.Rect(rect)
    if not enabled:
        fill = (70, 70, 68)
        border = (105, 105, 105)
        text_color = (145, 145, 145)
    elif color_override is not None:
        fill = color_override
        border = SILVER
        text_color = WHITE
    elif selected:
        fill = ORANGE
        border = SILVER
        text_color = WHITE
    else:
        fill = WOOD_LIGHT
        border = SILVER
        text_color = WHITE

    pygame.draw.rect(screen, (35, 25, 18), rect.move(0, 5), border_radius=12)
    pygame.draw.rect(screen, border, rect, border_radius=12)
    pygame.draw.rect(screen, fill, rect.inflate(-6, -6), border_radius=9)
    if enabled:
        pygame.draw.line(screen, WOOD_HIGHLIGHT, (rect.left + 14, rect.top + 8), (rect.right - 14, rect.top + 8), 2)
    f = font(24 if small else 30, True)
    text = f.render(label, True, text_color)
    screen.blit(text, text.get_rect(center=rect.center))
    return rect


def draw_star(screen, center, radius, filled=True, color=None):
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.43
        points.append((center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r))
    fill_color = (color or GOLD) if filled else (60, 52, 43)
    pygame.draw.polygon(screen, fill_color, points)
    pygame.draw.polygon(screen, (120, 90, 45) if filled else (90, 80, 70), points, 2)


_bg_cache = {}


def draw_background(screen):
    size = screen.get_size()
    if size not in _bg_cache:
        surf = pygame.Surface(size)
        surf.fill((36, 26, 18))
        for y in range(0, size[1], 18):
            pygame.draw.line(surf, (48 + (y // 18) % 3 * 4, 32, 20), (0, y), (size[0], y + 3), 2)
        _bg_cache[size] = surf
    screen.blit(_bg_cache[size], (0, 0))
