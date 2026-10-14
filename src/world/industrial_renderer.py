"""
Industrial environment renderer for NORMAL difficulty.

This module turns the existing gameplay geometry (platform rects, the
ground rect, pit rects, moving-platform rects) into a tiled industrial
factory look, using the tiles sliced by `industrial_tileset.py`.

IMPORTANT: this module is purely visual. It never creates or changes
any collision rectangle - it only reads the rects it is given and
draws tiles on top of / around them.

Only tiles whose screen position intersects the visible screen are
drawn, and platform/ground bodies are clipped to their own rect so the
tile grid never has to line up perfectly with non-multiple-of-tile
widths or heights.
"""

import pygame

from src.settings import WIDTH, HEIGHT
from src.world.industrial_tileset import get_tileset

# Background structural panels/pipes are large and spaced out along the
# world so the factory feels continuous without being drawn in full.
BG_STRUCTURE_SPACING = 260
BG_STRUCTURE_HEIGHT = 230


def _visible_x_range(camera, margin=64):
    """World-space x range currently visible on screen (with margin)."""
    left = camera.x - margin
    right = camera.x + WIDTH + margin
    return left, right


def _tile_row(screen, camera, rect, row_world_y, row_height, picker):
    """
    Draw one horizontal row of tiles spanning `rect`'s width at world
    y = row_world_y, using `picker(col_index, is_first, is_last)` to
    choose which named tile to draw in each column. Tiles are scaled
    to (col_width, row_height) so rows of any height compose cleanly.
    """
    ts = get_tileset()
    T = ts.tile_size

    num_cols = max(1, round(rect.width / T))
    col_width = rect.width / num_cols

    for col in range(num_cols):
        world_x = rect.x + col * col_width
        screen_x = world_x - camera.x
        screen_y = row_world_y

        if screen_x + col_width < -32 or screen_x > WIDTH + 32:
            continue

        name = picker(col, col == 0, col == num_cols - 1)
        tile = ts.get(name) if name else None
        if tile is None:
            continue

        w = int(round(col_width)) + 1
        h = int(round(row_height))
        if w <= 0 or h <= 0:
            continue
        if tile.get_size() != (w, h):
            tile = pygame.transform.scale(tile, (w, h))

        screen.blit(tile, (int(screen_x), int(screen_y)))


def _body_variant(index, seed):
    """Deterministic (non-flickering) variant picker for body panels."""
    h = (index * 2654435761 + seed * 97) & 0xFFFFFFFF
    bucket = h % 10
    if bucket == 7:
        return "HAZARD_CENTER"
    if bucket == 3:
        return "PANEL_VARIANT_2"
    if bucket == 5:
        return "PANEL_VARIANT_4"
    return "CENTER"


def draw_industrial_platform(screen, camera, rect, seed=0, thick=True):
    """Draw a full industrial platform (top edge + repeating body)."""
    ts = get_tileset()
    if not ts.loaded:
        pygame.draw.rect(screen, (69, 48, 28), camera.apply(rect))
        return

    T = ts.tile_size
    screen_rect = camera.apply(rect)

    old_clip = screen.get_clip()
    screen.set_clip(screen_rect)

    # ---- TOP ROW (corners + top edge) ----
    def top_picker(col, is_first, is_last):
        if is_first:
            return "CORNER_TOP_LEFT"
        if is_last:
            return "CORNER_TOP_RIGHT"
        return "TOP"

    top_height = min(T, rect.height)
    _tile_row(screen, camera, rect, screen_rect.y, top_height, top_picker)

    # ---- BODY ROWS (repeating panels down to the bottom) ----
    remaining = rect.height - top_height
    row_y = screen_rect.y + top_height
    row_index = 0

    while remaining > 0:
        row_h = min(T, remaining)
        is_bottom_row = remaining <= T

        def body_picker(col, is_first, is_last, _row=row_index, _bottom=is_bottom_row):
            if is_first:
                return "CORNER_BOTTOM_LEFT" if _bottom else "LEFT"
            if is_last:
                return "CORNER_BOTTOM_RIGHT" if _bottom else "RIGHT"
            if _bottom:
                return "BOTTOM"
            return _body_variant(col + _row * 13, seed)

        _tile_row(screen, camera, rect, row_y, row_h, body_picker)
        row_y += row_h
        remaining -= row_h
        row_index += 1

    screen.set_clip(old_clip)

    # ---- Occasional hazard stripe accent just above the platform ----
    if thick and rect.width >= T * 2 and (seed % 3 == 0):
        stripe_h = max(4, T // 6)
        band = ts.get("HAZARD_SINGLE")
        if band is not None and screen_rect.width > 0:
            band = pygame.transform.scale(band, (screen_rect.width, stripe_h))
            screen.blit(band, (screen_rect.x, screen_rect.y - stripe_h + 2))


def draw_industrial_ground(screen, camera, rect, seed=0):
    """Draw the large ground strip as a continuous factory floor."""
    ts = get_tileset()
    if not ts.loaded:
        pygame.draw.rect(screen, (69, 48, 28), camera.apply(rect))
        return

    draw_industrial_platform(screen, camera, rect, seed=seed, thick=True)

    # A thin hazard warning strip runs along the very top of the floor.
    T = ts.tile_size
    screen_rect = camera.apply(rect)
    strip_rect = pygame.Rect(screen_rect.x, screen_rect.y, screen_rect.width, 10)

    def hazard_picker(col, is_first, is_last):
        return "HAZARD_SINGLE"

    old_clip = screen.get_clip()
    screen.set_clip(strip_rect)
    _tile_row(screen, camera, rect, screen_rect.y, 10, hazard_picker)
    screen.set_clip(old_clip)


def draw_industrial_moving_platform(screen, camera, rect, seed=0):
    """Thin industrial platform variant used for moving platforms."""
    ts = get_tileset()
    screen_rect = camera.apply(rect)

    if not ts.loaded:
        pygame.draw.rect(screen, (90, 90, 100), screen_rect)
        return

    old_clip = screen.get_clip()
    screen.set_clip(screen_rect)

    def picker(col, is_first, is_last):
        if is_first:
            return "CORNER_TOP_LEFT"
        if is_last:
            return "CORNER_TOP_RIGHT"
        return "TOP" if (col + seed) % 5 != 2 else "HAZARD_TOP"

    _tile_row(screen, camera, rect, screen_rect.y, screen_rect.height, picker)
    screen.set_clip(old_clip)


def draw_industrial_pit(screen, camera, pit_rect, floor_top_y):
    """Draw a pit as an exposed industrial shaft rather than a black box."""
    ts = get_tileset()
    screen_rect = camera.apply(pit_rect)

    if not ts.loaded:
        pygame.draw.rect(screen, (20, 20, 20), screen_rect)
        return

    # Dark shaft interior.
    old_clip = screen.get_clip()
    screen.set_clip(screen_rect)

    T = ts.tile_size
    void_tile = ts.get("DARK_VOID")
    grate_tile = ts.get("GRATE")
    row_y = screen_rect.y
    row_index = 0
    remaining = screen_rect.height
    while remaining > 0:
        row_h = min(T, remaining)
        tile = grate_tile if row_index % 3 == 1 else void_tile
        if tile is not None:
            num_cols = max(1, round(screen_rect.width / T))
            col_w = screen_rect.width / num_cols
            for col in range(num_cols):
                sx = screen_rect.x + col * col_w
                w = int(round(col_w)) + 1
                h = int(round(row_h))
                scaled = pygame.transform.scale(tile, (w, h))
                screen.blit(scaled, (int(sx), int(row_y)))
        row_y += row_h
        remaining -= row_h
        row_index += 1

    screen.set_clip(old_clip)

    # Hazard-striped warning lip around the opening.
    hazard = ts.get("HAZARD_SINGLE")
    if hazard is not None:
        lip_h = 8
        lip = pygame.transform.scale(hazard, (screen_rect.width, lip_h))
        screen.blit(lip, (screen_rect.x, screen_rect.y - 2))

    # Vertical pipes flanking the pit opening for detail.
    pipe_top = ts.get("PIPE_TOP")
    pipe_mid = ts.get("PIPE_MID")
    if pipe_top is not None and pipe_mid is not None and screen_rect.height > T:
        pipe_w = T // 2
        for edge_x in (screen_rect.left - pipe_w // 2, screen_rect.right - pipe_w // 2):
            if -pipe_w < edge_x < WIDTH:
                top = pygame.transform.scale(pipe_top, (pipe_w, T))
                screen.blit(top, (edge_x, screen_rect.y - T // 2))


def draw_industrial_background(screen, camera, world_width, ground_top_y):
    """
    Large background factory structures behind the gameplay platforms:
    vertical supports, panel walls and pipes spaced along the world.
    Purely decorative, scrolls with the camera at a slightly reduced
    (midground) rate on both axes for a bit of parallax depth.
    """
    ts = get_tileset()
    if not ts.loaded:
        return

    T = ts.tile_size
    parallax = 0.85
    visible_left, visible_right = _visible_x_range(camera, margin=BG_STRUCTURE_SPACING)

    first_index = int(visible_left // BG_STRUCTURE_SPACING)
    last_index = int(visible_right // BG_STRUCTURE_SPACING) + 1

    top_y = ground_top_y - BG_STRUCTURE_HEIGHT

    # A lightweight camera-like object so _draw_background_structure can
    # keep using camera.apply()-style math while actually applying the
    # reduced (parallax) scroll rate on both axes.
    class _ParallaxCamera:
        x = camera.x * parallax
        y = camera.y * parallax

        @staticmethod
        def apply(rect):
            return pygame.Rect(
                int(rect.x - camera.x * parallax),
                int(rect.y - camera.y * parallax),
                rect.width,
                rect.height,
            )

    for i in range(first_index, last_index + 1):
        world_x = i * BG_STRUCTURE_SPACING
        screen_x = world_x - camera.x * parallax

        if screen_x < -BG_STRUCTURE_SPACING or screen_x > WIDTH + BG_STRUCTURE_SPACING:
            continue

        bucket = (i * 2654435761) & 0xFFFFFFFF
        variant = bucket % 4

        struct_rect = pygame.Rect(int(world_x), int(top_y), T * 3, BG_STRUCTURE_HEIGHT)
        _draw_background_structure(screen, _ParallaxCamera, struct_rect, variant, i)


def _draw_background_structure(screen, camera, rect, variant, index):
    ts = get_tileset()
    T = ts.tile_size
    screen_rect = camera.apply(rect)

    if screen_rect.right < 0 or screen_rect.left > WIDTH:
        return

    old_clip = screen.get_clip()
    screen.set_clip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    if variant == 0:
        # Wide cross-braced panel wall.
        def picker(col, is_first, is_last):
            return "CROSS_BRACE_1" if col % 2 == 0 else "CROSS_BRACE_2"
        rows = max(1, rect.height // T)
        row_h = rect.height / rows
        for r in range(rows):
            _tile_row(screen, camera, rect, screen_rect.y + r * row_h, row_h, picker)

    elif variant == 1:
        # Vertical pipe cluster.
        pipe_top = ts.get("PIPE_TOP")
        pipe_mid = ts.get("PIPE_MID")
        if pipe_top and pipe_mid:
            pipe_w = T
            x = screen_rect.x + rect.width // 4
            top = pygame.transform.scale(pipe_top, (pipe_w, T))
            screen.blit(top, (x, screen_rect.y))
            y = screen_rect.y + T
            while y < screen_rect.bottom:
                seg = pygame.transform.scale(pipe_mid, (pipe_w, min(T, screen_rect.bottom - y)))
                screen.blit(seg, (x, y))
                y += T

    elif variant == 2:
        # Bolted plain wall panel with a warning gate accent.
        def picker(col, is_first, is_last):
            return "BOLT_PANEL" if col % 2 == 0 else "PANEL_PLAIN"
        rows = max(1, rect.height // T)
        row_h = rect.height / rows
        for r in range(rows):
            _tile_row(screen, camera, rect, screen_rect.y + r * row_h, row_h, picker)
        gate = ts.get("WARNING_GATE")
        if gate is not None:
            gate = pygame.transform.scale(gate, (T, T))
            screen.blit(gate, (screen_rect.x + rect.width // 3, screen_rect.bottom - T))

    else:
        # Support beam / vent structure.
        def picker(col, is_first, is_last):
            return "VENT_PANEL" if col % 3 == 0 else "PANEL_DARK"
        rows = max(1, rect.height // T)
        row_h = rect.height / rows
        for r in range(rows):
            _tile_row(screen, camera, rect, screen_rect.y + r * row_h, row_h, picker)

    screen.set_clip(old_clip)
