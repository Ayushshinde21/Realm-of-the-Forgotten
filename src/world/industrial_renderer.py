"""Industrial Zone renderer used exclusively by Normal difficulty.

All drawing is visual-only: collision and movement rectangles are read but
never modified. The renderer tiles the supplied native 32px industrial art,
uses the pack's layered backgrounds for parallax, and deterministically places
non-colliding scenery from the included object and animation assets.
"""
from __future__ import annotations

import random

import pygame

from src.settings import WIDTH, HEIGHT
from src.world.industrial_tileset import get_tileset

TILE = 32
BACKGROUND_SCALE = 2
BG_STRUCTURE_SPACING = 880
BG_STRUCTURE_HEIGHT = 240
DRAW_MARGIN = 180

# Native 32px tile IDs from the supplied 81-tile pack. Each entry is an
# actual file, not a guessed sprite-sheet row/column.
_PLATFORM_TOP_IDS = (77, 78, 79)
_PLATFORM_BODY_IDS = (4, 5, 6, 8, 11, 12, 13, 14, 15, 16, 17, 22, 23, 24, 25, 26, 55, 56, 57, 64, 65, 66, 73)
_BACKGROUND_PANEL_IDS = (3, 7, 11, 14, 16, 21, 22, 25, 26, 55, 62, 64, 65, 71, 73)
_HAZARD_TOP_IDS = (80, 81, 9)
_PIT_BODY_IDS = (21, 46, 62, 70, 71)
_GROUND_OBJECTS = (
    "Barrel1", "Barrel2", "Barrel3", "Barrel4",
    "Box1", "Box2", "Box3", "Box5", "Box6", "Box8",
    "Locker1", "Locker2", "Locker3", "Locker4",
    "Bench", "Fire-extinguisher1", "Fire-extinguisher2",
    "Ladder1", "Ladder2", "Fence1", "Fence2", "Board1", "Board2",
)
_SMALL_PLATFORM_OBJECTS = ("Box1", "Box2", "Box5", "Barrel1", "Fire-extinguisher1")

# Result cache avoids regenerating the same decoration placement every frame.
_DECORATION_LAYOUTS = {}


def _visible_world_range(camera, screen_width=WIDTH, margin=DRAW_MARGIN):
    return int(camera.x) - margin, int(camera.x) + screen_width + margin


def _screen_rect(camera, world_rect):
    return camera.apply(world_rect)


def _surface(screen, tile, x, y):
    if tile is not None:
        screen.blit(tile, (int(x), int(y)))


def _draw_top_row(screen, camera, rect, tile_ids, seed=0, hazard=False):
    tileset = get_tileset()
    if not tile_ids:
        return
    left, right = _visible_world_range(camera)
    first_x = max(rect.left, (left // TILE) * TILE)
    last_x = min(rect.right, right)
    if first_x > last_x:
        return
    clip_rect = pygame.Rect(rect.x - int(camera.x), rect.y - int(camera.y), rect.width, min(rect.height, TILE))
    old_clip = screen.get_clip()
    screen.set_clip(old_clip.clip(clip_rect))
    for world_x in range(first_x, last_x, TILE):
        column = (world_x // TILE + seed) % len(tile_ids)
        tile_id = tile_ids[column]
        if hazard and ((world_x // TILE + seed) % 5 in (1, 2)):
            tile_id = _HAZARD_TOP_IDS[(world_x // TILE + seed) % len(_HAZARD_TOP_IDS)]
        _surface(screen, tileset.tile(tile_id), world_x - camera.x, rect.y - camera.y)
    screen.set_clip(old_clip)


def draw_industrial_platform(screen, camera, rect, seed=0, thick=True):
    """Draw a metal walkway around the unchanged collision rectangle."""
    tileset = get_tileset()
    screen_rect = _screen_rect(camera, rect)
    if not tileset.loaded:
        pygame.draw.rect(screen, (42, 46, 59), screen_rect)
        pygame.draw.line(screen, (139, 167, 177), screen_rect.topleft, screen_rect.topright, 3)
        return

    visible = screen_rect.clip(screen.get_rect())
    if visible.width <= 0 or visible.height <= 0:
        return
    old_clip = screen.get_clip()
    screen.set_clip(old_clip.clip(screen_rect))

    # Tiles 77-79 are native metal ledges with a transparent lower half. Their
    # top edge lands exactly on the collision rectangle's top, with no scaling.
    top_height = min(16, rect.height)
    _draw_top_row(screen, camera, pygame.Rect(rect.x, rect.y, rect.width, top_height), _PLATFORM_TOP_IDS, seed)

    # Fill the walkable slab below the top surface with real riveted panel tiles.
    start_y = rect.y + top_height
    bottom = rect.bottom
    row_index = 0
    while start_y < bottom:
        row_h = min(TILE, bottom - start_y)
        row_rect = pygame.Rect(rect.x, start_y, rect.width, row_h)
        row_screen = _screen_rect(camera, row_rect)
        previous_row_clip = screen.get_clip()
        screen.set_clip(previous_row_clip.clip(row_screen))
        left, right = _visible_world_range(camera)
        first_x = max(rect.left, (left // TILE) * TILE)
        last_x = min(rect.right, right)
        for world_x in range(first_x, last_x, TILE):
            column = (world_x // TILE + seed * 3 + row_index * 7) % len(_PLATFORM_BODY_IDS)
            tile_id = _PLATFORM_BODY_IDS[column]
            tile = tileset.tile(tile_id)
            if tile is not None:
                screen.blit(tile, (int(world_x - camera.x), int(start_y - camera.y)))
        screen.set_clip(previous_row_clip)
        start_y += row_h
        row_index += 1

    screen.set_clip(old_clip)

    # Occasional riveted edge trim is cosmetic only; it is never a hazard.
    if thick and rect.width >= TILE * 5:
        trim = tileset.tile(18 if seed % 2 == 0 else 27)
        if trim is not None:
            trim_rect = pygame.Rect(screen_rect.x, screen_rect.y + 2, screen_rect.width, min(6, screen_rect.height))
            old_clip = screen.get_clip()
            screen.set_clip(old_clip.clip(trim_rect))
            x = screen_rect.left
            while x < screen_rect.right:
                screen.blit(trim, (x, screen_rect.y))
                x += TILE
            screen.set_clip(old_clip)


def draw_industrial_ground(screen, camera, rect, seed=0):
    """Tile the full ground with a continuous steel surface and panel body."""
    tileset = get_tileset()
    if not tileset.loaded:
        pygame.draw.rect(screen, (42, 46, 59), _screen_rect(camera, rect))
        return
    draw_industrial_platform(screen, camera, rect, seed=seed, thick=False)

    # Low-contrast periodic seams help read the broad floor without making all
    # ground look hazardous. Actual warning markings are reserved for pit lips.
    screen_rect = _screen_rect(camera, rect)
    old_clip = screen.get_clip()
    screen.set_clip(old_clip.clip(screen_rect))
    seam_color = (37, 44, 62)
    start_world_x = (rect.left // 256) * 256
    for world_x in range(start_world_x, rect.right, 256):
        x = int(world_x - camera.x)
        pygame.draw.line(screen, seam_color, (x, screen_rect.y + 16), (x, screen_rect.bottom), 1)
    screen.set_clip(old_clip)


def draw_industrial_moving_platform(screen, camera, rect, seed=0):
    """Distinct conveyor-style visual for existing moving-platform geometry."""
    tileset = get_tileset()
    screen_rect = _screen_rect(camera, rect)
    if not tileset.loaded:
        pygame.draw.rect(screen, (55, 63, 81), screen_rect)
        pygame.draw.line(screen, (222, 82, 45), screen_rect.topleft, screen_rect.topright, 3)
        return

    visible = screen_rect.clip(screen.get_rect())
    if visible.width <= 0 or visible.height <= 0:
        return
    old_clip = screen.get_clip()
    screen.set_clip(old_clip.clip(screen_rect))
    x = screen_rect.left
    segment = seed % 3
    while x < screen_rect.right:
        tile_id = _HAZARD_TOP_IDS[segment % len(_HAZARD_TOP_IDS)]
        tile = tileset.tile(tile_id)
        if tile is None:
            tile = tileset.tile(_PLATFORM_TOP_IDS[segment % len(_PLATFORM_TOP_IDS)])
        if tile is not None:
            screen.blit(tile, (x, screen_rect.top))
        x += TILE
        segment += 1
    pygame.draw.line(screen, (30, 35, 52), screen_rect.bottomleft, screen_rect.bottomright, 2)
    screen.set_clip(old_clip)


def draw_industrial_pit(screen, camera, pit_rect, floor_top_y):
    """Render an existing pit as a deep industrial shaft without changing it."""
    tileset = get_tileset()
    screen_rect = _screen_rect(camera, pit_rect)
    if not screen_rect.colliderect(screen.get_rect()):
        return
    old_clip = screen.get_clip()
    screen.set_clip(old_clip.clip(screen_rect))
    pygame.draw.rect(screen, (20, 22, 34), screen_rect)

    visible_left, visible_right = _visible_world_range(camera, margin=0)
    first_x = max(pit_rect.left, (visible_left // TILE) * TILE)
    last_x = min(pit_rect.right, visible_right)
    top = max(0, screen_rect.top)
    bottom = min(HEIGHT, screen_rect.bottom)
    for row_index, sy in enumerate(range(top, bottom, TILE)):
        world_y = sy + int(camera.y)
        for world_x in range(first_x, last_x, TILE):
            tile_id = _PIT_BODY_IDS[(world_x // TILE + world_y // TILE) % len(_PIT_BODY_IDS)]
            tile = tileset.tile(tile_id)
            if tile is not None:
                screen.blit(tile, (int(world_x - camera.x), sy))
    screen.set_clip(old_clip)

    # Red-orange warning lip is visual-only, and follows the actual pit edges.
    lip_y = int(pit_rect.top - camera.y)
    lip_left = int(pit_rect.left - camera.x)
    lip_right = int(pit_rect.right - camera.x)
    if -TILE < lip_y < HEIGHT and lip_right > 0 and lip_left < WIDTH:
        x = lip_left
        tile_index = 0
        while x < lip_right:
            tile = tileset.tile(_HAZARD_TOP_IDS[tile_index % len(_HAZARD_TOP_IDS)])
            if tile is not None:
                screen.blit(tile, (x, lip_y))
            x += TILE
            tile_index += 1
        for edge_x in (lip_left, lip_right - TILE):
            if -TILE < edge_x < WIDTH:
                pipe = tileset.tile(61)
                if pipe is not None:
                    screen.blit(pipe, (edge_x, lip_y + TILE // 2))


def _draw_repeating_background_layer(screen, surface, camera, horizontal_rate, vertical_rate, phase):
    if surface is None:
        return
    image_width = surface.get_width()
    if image_width <= 0:
        return
    offset = -int(camera.x * horizontal_rate + phase) % image_width
    screen_y = -int(camera.y * vertical_rate)
    x = offset - image_width
    while x < WIDTH:
        screen.blit(surface, (x, screen_y))
        x += image_width


def _draw_background_structure(screen, tileset, screen_x, ground_screen_y, variant, seed, tick_ms):
    """A static industrial wall bay plus animated display/conveyor dressing."""
    panel_x = int(screen_x)
    top_y = int(ground_screen_y - BG_STRUCTURE_HEIGHT)
    if panel_x > WIDTH or panel_x + 96 < 0:
        return

    # Alternating cross-braced wall bays and steel beams use actual 32px tiles.
    panel_ids = (62, 71, 14, 16, 22, 25)
    for col in range(2):
        for row in range(6):
            if variant % 3 == 0:
                tile_id = panel_ids[(variant + col * 2 + row * 3) % len(panel_ids)]
            else:
                tile_id = panel_ids[(seed + variant + col + row * 2) % len(panel_ids)]
            tile = tileset.tile(tile_id)
            if tile is not None:
                screen.blit(tile, (panel_x + col * TILE, top_y + row * TILE))
    beam = tileset.tile(70)
    if beam is not None:
        screen.blit(beam, (panel_x - 8, top_y - 8))
        screen.blit(beam, (panel_x + 56, top_y - 8))

    # Sprite sheets are pre-sliced by the loader. Screens and conveyor modules
    # animate at a stable 150ms per frame; none participates in collision.
    if variant % 2 == 0:
        screen_frame = tileset.animation_frame("Screen1", tick_ms=tick_ms, frame_ms=180)
        if screen_frame is not None:
            screen.blit(screen_frame, (panel_x + 16, top_y + 30))
    elif variant % 3 == 1:
        screen_frame = tileset.animation_frame("Screen2", tick_ms=tick_ms, frame_ms=180)
        if screen_frame is not None:
            screen.blit(screen_frame, (panel_x + 15, top_y + 28))

    if variant % 3 == 2:
        conveyor = tileset.animation_frame("Transporter1", tick_ms=tick_ms, frame_ms=130)
        if conveyor is not None:
            screen.blit(conveyor, (panel_x - 16, top_y + 130))


def draw_industrial_background(screen, camera, world_width, ground_top_y, seed=0, level_number=1):
    """Composite the supplied industrial backgrounds with deterministic parallax."""
    tileset = get_tileset()
    screen.fill((112, 111, 127))
    if not tileset.loaded:
        # Safe industrial fallback if a user removes the optional asset pack.
        for y in range(0, HEIGHT, 48):
            pygame.draw.rect(screen, (76, 83, 101), (0, y, WIDTH, 1))
        pygame.draw.rect(screen, (52, 56, 72), (0, HEIGHT - 160, WIDTH, 160))
        return

    # The pack supplies independent sky, smoke, skyline, factory and refinery
    # silhouettes. Drawn in increasing foreground order, each scaled 2x with
    # nearest-neighbour scaling and repeated only at the panorama's full width.
    layers = (
        ("1", 0.025, 0.015),
        ("2", 0.045, 0.020),
        ("3", 0.115, 0.027),
        ("4", 0.205, 0.034),
        ("5", 0.315, 0.040),
    )
    for index, (name, horizontal_rate, vertical_rate) in enumerate(layers):
        phase = ((seed * 37 + level_number * 113 + index * 71) % 1152)
        layer = tileset.background_layer(name, BACKGROUND_SCALE)
        _draw_repeating_background_layer(
            screen, layer, camera, horizontal_rate, vertical_rate, phase
        )

    # Taller factory wall bays add close industrial detail to otherwise open
    # skyline areas. They are a visual layer only and sit behind all terrain.
    tick_ms = pygame.time.get_ticks()
    spacing = BG_STRUCTURE_SPACING
    phase_world = (int(seed) * 67 + int(level_number) * 191) % spacing
    parallax_camera_x = camera.x * 0.82
    visible_left = int(parallax_camera_x) - spacing
    visible_right = int(parallax_camera_x) + WIDTH + spacing
    first_index = max(-1, (visible_left - phase_world) // spacing)
    last_index = (visible_right - phase_world) // spacing + 1
    ground_screen_y = int(ground_top_y - camera.y)
    for index in range(first_index, last_index + 1):
        world_x = index * spacing + phase_world
        screen_x = world_x - parallax_camera_x
        variant = (index + seed + level_number * 2) % 6
        _draw_background_structure(
            screen, tileset, screen_x, ground_screen_y, variant, seed, tick_ms
        )


def _layout_key(world_width, ground_top, platform_rects, pit_ranges, seed, level_number, finish_x):
    return (
        int(world_width), int(ground_top), tuple(platform_rects), tuple(pit_ranges),
        int(seed), int(level_number), int(finish_x),
    )


def _build_decoration_layout(world_width, ground_rect, platforms, pits, seed, level_number, finish_x):
    platform_rects = tuple(
        (int(p.rect.x), int(p.rect.y), int(p.rect.width), int(p.rect.height))
        for p in platforms if hasattr(p, "rect")
    )
    pit_ranges = tuple((int(p.left), int(p.right)) for p in pits)
    key = _layout_key(world_width, ground_rect.top, platform_rects, pit_ranges, seed, level_number, finish_x)
    if key in _DECORATION_LAYOUTS:
        return _DECORATION_LAYOUTS[key]

    rng = random.Random((int(seed) ^ (int(level_number) * 0x9E3779B9)) & 0xFFFFFFFF)
    pit_intervals = [(left - 50, right + 50) for left, right in pit_ranges]
    ground_items = []
    x = rng.randint(300, 450)
    while x < world_width - 150:
        step = rng.randint(230, 380)
        if x > max(0, finish_x - 260) and x < finish_x + 100:
            x += step
            continue
        if any(left <= x <= right for left, right in pit_intervals):
            x += step
            continue
        if rng.random() < 0.84:
            name = rng.choice(_GROUND_OBJECTS)
            ground_items.append((name, x))
            if name.startswith("Barrel") and rng.random() < 0.38:
                ground_items.append((rng.choice(("Barrel1", "Barrel2", "Box1")), x + rng.randint(17, 25)))
            elif name.startswith("Box") and rng.random() < 0.22:
                ground_items.append((rng.choice(("Box2", "Box5", "Barrel1")), x + rng.randint(25, 34)))
        x += step

    # A restrained set of props on wide static platforms adds depth to elevated
    # traversal. They're purely decorative and have no rect/collision object.
    platform_items = []
    for index, (px, py, pw, ph) in enumerate(platform_rects):
        if pw < 190 or rng.random() > 0.24:
            continue
        if any(left < px + pw and right > px for left, right in pit_intervals):
            continue
        asset = rng.choice(_SMALL_PLATFORM_OBJECTS)
        draw_x = px + rng.randint(28, max(29, pw - 52))
        platform_items.append((asset, draw_x, py + 1))

    result = (tuple(ground_items), tuple(platform_items))
    _DECORATION_LAYOUTS[key] = result
    if len(_DECORATION_LAYOUTS) > 32:
        _DECORATION_LAYOUTS.pop(next(iter(_DECORATION_LAYOUTS)))
    return result


def draw_industrial_decorations(
    screen, camera, world_width, ground_rect, platforms, pits,
    seed=0, level_number=1, finish_x=None,
):
    """Draw deterministic non-colliding industrial props in the foreground."""
    tileset = get_tileset()
    if not tileset.loaded:
        return
    if finish_x is None:
        finish_x = world_width - 200

    ground_items, platform_items = _build_decoration_layout(
        world_width, ground_rect, platforms, pits, seed, level_number, finish_x
    )
    visible_left, visible_right = _visible_world_range(camera, margin=220)
    ground_y = int(ground_rect.top - camera.y)

    for name, world_x in ground_items:
        if world_x + 40 < visible_left or world_x > visible_right:
            continue
        image = tileset.object(name)
        if image is None:
            continue
        screen_x = int(world_x - camera.x)
        screen_y = ground_y - image.get_height()
        screen.blit(image, (screen_x, screen_y))

    for name, world_x, platform_top in platform_items:
        if world_x + 40 < visible_left or world_x > visible_right:
            continue
        image = tileset.object(name)
        if image is None:
            continue
        screen.blit(image, (int(world_x - camera.x), int(platform_top - camera.y - image.get_height())))
