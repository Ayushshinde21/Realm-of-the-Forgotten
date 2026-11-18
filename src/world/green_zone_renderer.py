"""Green Zone world renderer used exclusively by World 2.

All render functions are visual-only: they use the level's existing world
rectangles without modifying collisions, movement, or gameplay state.
"""
from __future__ import annotations

import random

import pygame

from src.settings import WIDTH, HEIGHT
from src.world.green_zone_tileset import get_tileset

TILE = 32
DRAW_MARGIN = 160

# The supplied tiles are individually numbered 1-96. These roles are based on
# the actual supplied PNGs: grassy cap tiles, wall/soil bodies, rock platforms,
# and diagonal grass edges. All tile use remains within the supplied pack.
_GROUND_TOP_IDS = (1, 2, 3, 5, 6, 7, 8, 18)
_PLATFORM_TOP_IDS = (49, 50, 51, 52, 1, 2, 3)
_SOIL_BODY_IDS = (13, 14, 15, 16, 17, 24, 25, 26, 27, 28, 29, 37, 38, 39, 40, 41, 53, 60, 61, 63, 64, 65, 66, 67, 68, 69, 70)
_STONE_BODY_IDS = (21, 22, 23, 30, 37, 38, 39, 40, 41, 44, 45, 46, 47, 48, 62, 63, 64, 65, 66, 71, 72)
_GRASS_EDGE_IDS = (42, 43)
_TREE_NAMES = ("Tree1", "Tree2", "Tree3", "Tree4")
_STONE_NAMES = ("Stone1", "Stone2", "Stone3", "Stone4", "Stone5", "Stone6")
_GROUND_DECORATION_CACHE = {}


def _screen_rect(camera, world_rect):
    return camera.apply(world_rect)


def _visible_world_x(camera, rect, screen_width):
    return max(rect.left, int(camera.x) - TILE), min(rect.right, int(camera.x) + screen_width + TILE)


def draw_green_zone_ground(screen, camera, world_rect, seed=0):
    """Draw a green grass cap over a deep, tiled forest-soil ground body."""
    tileset = get_tileset()
    screen_rect = _screen_rect(camera, world_rect)
    pygame.draw.rect(screen, (38, 25, 43), screen_rect)
    if not tileset.loaded:
        pygame.draw.rect(screen, (87, 174, 70), (screen_rect.x, screen_rect.y, screen_rect.width, 9))
        pygame.draw.rect(screen, (49, 52, 74), (screen_rect.x, screen_rect.y + 9, screen_rect.width, max(0, screen_rect.height - 9)))
        return

    visible_left, visible_right = _visible_world_x(camera, world_rect, screen.get_width())
    first_x = (visible_left // TILE) * TILE
    clip_before = screen.get_clip()
    screen.set_clip(clip_before.clip(screen_rect))
    # Body rows start underneath the 32px turf tiles so their grassy caps never repeat vertically.
    for world_y in range(world_rect.top + TILE, world_rect.bottom, TILE):
        y = int(world_y - camera.y)
        row_index = world_y // TILE + seed * 5
        for world_x in range(first_x, visible_right, TILE):
            tile_id = _SOIL_BODY_IDS[(world_x // TILE * 3 + row_index) % len(_SOIL_BODY_IDS)]
            tile = tileset.tile(tile_id)
            if tile is not None:
                screen.blit(tile, (int(world_x - camera.x), y))
    y = int(world_rect.top - camera.y)
    for world_x in range(first_x, visible_right, TILE):
        tile_id = _GROUND_TOP_IDS[(world_x // TILE + seed * 5) % len(_GROUND_TOP_IDS)]
        tile = tileset.tile(tile_id)
        if tile is not None:
            screen.blit(tile, (int(world_x - camera.x), y))
    screen.set_clip(clip_before)


def draw_green_zone_platform(screen, camera, world_rect, seed=0, moving=False):
    """Draw a grass-topped floating ledge without changing its collision rect."""
    tileset = get_tileset()
    screen_rect = _screen_rect(camera, world_rect)
    body_color = (38, 32, 48) if not moving else (43, 49, 65)
    pygame.draw.rect(screen, body_color, screen_rect)
    if not tileset.loaded:
        pygame.draw.line(screen, (95, 186, 74), screen_rect.topleft, screen_rect.topright, 6)
        return

    visible_left, visible_right = _visible_world_x(camera, world_rect, screen.get_width())
    if moving:
        # Anchor every tile to the platform itself. World-grid alignment makes
        # the artwork appear stationary while a horizontal platform moves.
        first_x = world_rect.left + ((visible_left - world_rect.left) // TILE) * TILE
    else:
        first_x = (visible_left // TILE) * TILE
    clip_before = screen.get_clip()
    # The tile cap is allowed a couple of visual pixels outside the collider to keep the edge organic.
    sprite_clip = pygame.Rect(screen_rect.left, screen_rect.top - 2, screen_rect.width, max(34, screen_rect.height + 2))
    screen.set_clip(clip_before.clip(sprite_clip))
    for world_y in range(world_rect.top + TILE, world_rect.bottom, TILE):
        y = int(world_y - camera.y)
        for world_x in range(first_x, visible_right, TILE):
            if moving:
                tile_column = (world_x - world_rect.left) // TILE
                tile_row = (world_y - world_rect.top) // TILE
                tile_id = _STONE_BODY_IDS[(tile_column + seed * 3 + tile_row) % len(_STONE_BODY_IDS)]
            else:
                tile_id = _SOIL_BODY_IDS[(world_x // TILE + seed + world_y // TILE) % len(_SOIL_BODY_IDS)]
            tile = tileset.tile(tile_id)
            if tile is not None:
                screen.blit(tile, (int(world_x - camera.x), y))
    for world_x in range(first_x, visible_right, TILE):
        if moving:
            tile_column = (world_x - world_rect.left) // TILE
            tile_id = _PLATFORM_TOP_IDS[(tile_column + seed) % len(_PLATFORM_TOP_IDS)]
            if tile_column % 3 == 0:
                tile_id = 18
        else:
            tile_id = _PLATFORM_TOP_IDS[(world_x // TILE + seed) % len(_PLATFORM_TOP_IDS)]
        tile = tileset.tile(tile_id)
        if tile is not None:
            screen.blit(tile, (int(world_x - camera.x), int(world_rect.top - camera.y)))
    if moving:
        pygame.draw.line(screen, (69, 117, 86), screen_rect.bottomleft, screen_rect.bottomright, 2)
    screen.set_clip(clip_before)


def draw_green_zone_moving_platform(screen, camera, world_rect, seed=0):
    draw_green_zone_platform(screen, camera, world_rect, seed=seed, moving=True)


def draw_green_zone_pit(screen, camera, pit_rect, floor_top_y):
    """Render existing pit rectangles as dark rocky chasms with grassy lips."""
    tileset = get_tileset()
    screen_rect = _screen_rect(camera, pit_rect)
    if not screen_rect.colliderect(screen.get_rect()):
        return
    pygame.draw.rect(screen, (23, 23, 39), screen_rect)
    clip_before = screen.get_clip()
    screen.set_clip(clip_before.clip(screen_rect))
    visible_left, visible_right = _visible_world_x(camera, pit_rect, screen.get_width())
    first_x = (visible_left // TILE) * TILE
    for world_y in range(pit_rect.top + 4, pit_rect.bottom, TILE):
        y = int(world_y - camera.y)
        for world_x in range(first_x, visible_right, TILE):
            tile_id = _STONE_BODY_IDS[(world_x // TILE + world_y // TILE) % len(_STONE_BODY_IDS)]
            tile = tileset.tile(tile_id)
            if tile is not None:
                screen.blit(tile, (int(world_x - camera.x), y))
    screen.set_clip(clip_before)
    # Grass at both lips marks the dangerous opening without bridging the gap.
    left_x = int(pit_rect.left - camera.x)
    right_x = int(pit_rect.right - camera.x)
    lip_y = int(pit_rect.top - camera.y)
    for x, tile_id in ((left_x - TILE // 2, _GRASS_EDGE_IDS[0]), (right_x - TILE // 2, _GRASS_EDGE_IDS[1])):
        tile = tileset.tile(tile_id)
        if tile is not None:
            screen.blit(tile, (x, lip_y))
    pygame.draw.line(screen, (75, 139, 59), (left_x, lip_y + 2), (left_x + 12, lip_y + 2), 3)
    pygame.draw.line(screen, (75, 139, 59), (right_x - 12, lip_y + 2), (right_x, lip_y + 2), 3)


def _decoration_layout(world_width, ground_rect, platforms, pits, seed, level_number, finish_x):
    platform_data = tuple((p.rect.x, p.rect.y, p.rect.width, p.rect.height) for p in platforms if hasattr(p, "rect"))
    pit_data = tuple((p.left, p.right) for p in pits)
    key = (world_width, ground_rect.top, platform_data, pit_data, seed, level_number, finish_x)
    if key in _GROUND_DECORATION_CACHE:
        return _GROUND_DECORATION_CACHE[key]

    rng = random.Random((int(seed) ^ (int(level_number) * 0x45D9F3B)) & 0xFFFFFFFF)
    pit_bands = [(left - 90, right + 90) for left, right in pit_data]
    ground_items = []
    x = rng.randint(480, 700)
    while x < world_width - 180:
        step = rng.randint(390, 720)
        if x < 360 or (finish_x - 280 <= x <= finish_x + 100):
            x += step
            continue
        if any(left <= x <= right for left, right in pit_bands):
            x += step
            continue
        roll = rng.random()
        if roll < 0.70:
            ground_items.append((rng.choice(_TREE_NAMES), x))
        elif roll < 0.90:
            ground_items.append((rng.choice(_STONE_NAMES), x))
        else:
            ground_items.append(("FountainAnimation", x))
        x += step

    platform_items = []
    for index, (px, py, pw, ph) in enumerate(platform_data):
        if pw < 220 or rng.random() > 0.18:
            continue
        if any(left < px + pw and right > px for left, right in pit_bands):
            continue
        asset = rng.choice(_STONE_NAMES[:4])
        platform_items.append((asset, px + rng.randint(25, max(26, pw - 35)), py))

    result = (tuple(ground_items), tuple(platform_items))
    _GROUND_DECORATION_CACHE[key] = result
    if len(_GROUND_DECORATION_CACHE) > 64:
        _GROUND_DECORATION_CACHE.pop(next(iter(_GROUND_DECORATION_CACHE)))
    return result


def draw_green_zone_decorations(screen, camera, world_width, ground_rect, platforms, pits, seed=0, level_number=1, finish_x=None):
    """Draw deterministic trees, stones and animated fountains as scenery only."""
    tileset = get_tileset()
    if not tileset.loaded:
        return
    if finish_x is None:
        finish_x = world_width - 200
    ground_items, platform_items = _decoration_layout(world_width, ground_rect, platforms, pits, seed, level_number, finish_x)
    visible_left = int(camera.x) - DRAW_MARGIN
    visible_right = int(camera.x) + screen.get_width() + DRAW_MARGIN
    ground_top = int(ground_rect.top)
    tick_ms = pygame.time.get_ticks()

    for name, world_x in ground_items:
        if world_x < visible_left - 200 or world_x > visible_right:
            continue
        if name == "FountainAnimation":
            image = tileset.animation_frame("Fountain", tick_ms=tick_ms, frame_ms=140)
            if image is None:
                image = tileset.object("Fountain1")
        else:
            image = tileset.object(name)
        if image is None:
            continue
        screen.blit(image, (int(world_x - camera.x), int(ground_top - camera.y - image.get_height())))

    for name, world_x, platform_top in platform_items:
        image = tileset.object(name)
        if image is None:
            continue
        screen.blit(image, (int(world_x - camera.x), int(platform_top - camera.y - image.get_height() + 2)))


def _draw_background_layer(screen, layer, camera, horizontal_rate, vertical_rate, phase):
    if layer is None:
        return
    width = layer.get_width()
    offset = -int(camera.x * horizontal_rate + phase) % width
    y = -int(camera.y * vertical_rate)
    x = offset - width
    while x < WIDTH:
        screen.blit(layer, (x, y))
        x += width


def draw_green_zone_background(screen, camera, world_width, ground_top_y, seed=0, level_number=1):
    """Compose supplied numbered forest layers with stable, level-seeded parallax.

    The first five World 2 levels use daylight, while its levels 6-10 transition to the
    matching night art. This gives the same cohesive Green Zone theme variety
    without changing any level geometry or mechanics.
    """
    tileset = get_tileset()
    time_of_day = "day" if int(level_number) <= 5 else "night"
    screen.fill((45, 47, 72) if time_of_day == "night" else (161, 183, 190))
    if not tileset.loaded:
        pygame.draw.rect(screen, (62, 104, 63), (0, HEIGHT - 100, WIDTH, 100))
        return

    base = tileset.scaled_background("1", time_of_day, WIDTH, HEIGHT)
    if base is not None:
        screen.blit(base, (0, 0))

    # Layer 1 supplies the sky, while 2-5 add increasingly near scenery.
    # Full-canvas surfaces preserve the original aspect ratio and transparency.
    layers = (
        ("2", 0.035, 0.006),
        ("3", 0.085, 0.012),
        ("4", 0.17, 0.020),
        ("5", 0.29, 0.030),
    )
    for index, (name, rate_x, rate_y) in enumerate(layers):
        layer = tileset.scaled_background(name, time_of_day, WIDTH, HEIGHT)
        phase = (int(seed) * 29 + int(level_number) * 71 + index * 193) % WIDTH
        _draw_background_layer(screen, layer, camera, rate_x, rate_y, phase)
