"""Adventure tiles used only by Easy difficulty."""

import pygame

from src.paths import ASSETS_DIR

_TILE_DIR = ASSETS_DIR / "tilesets" / "adventure_easy" / "1 Tiles"
_GROUND_TILE_IDS = (1, 2, 3, 4)
_SOIL_TILE_ID = 26
_PLATFORM_TILE_IDS = (7, 8, 9, 18)
_TERRAIN = None


def _load_image(path):
    image = pygame.image.load(str(path))
    try:
        return image.convert_alpha()
    except pygame.error:
        return image


def _get_terrain():
    global _TERRAIN
    if _TERRAIN is None:
        tile_ids = set(_GROUND_TILE_IDS + (_SOIL_TILE_ID,) + _PLATFORM_TILE_IDS)
        _TERRAIN = {}
        for tile_id in tile_ids:
            path = _TILE_DIR / f"Tile_{tile_id:03d}.png"
            if path.is_file():
                _TERRAIN[tile_id] = _load_image(path)
    return _TERRAIN


def _visible_world_range(rect, camera, tile_width, screen_width):
    camera_x = int(camera.x)
    left = max(rect.left, camera_x - tile_width)
    right = min(rect.right, camera_x + screen_width + tile_width)
    first_x = (left // tile_width) * tile_width
    return range(first_x, right, tile_width)


def draw_easy_ground(screen, camera, world_rect):
    terrain = _get_terrain()
    ground_tiles = [terrain[tile_id] for tile_id in _GROUND_TILE_IDS if tile_id in terrain]
    soil_tile = terrain.get(_SOIL_TILE_ID)
    screen_rect = camera.apply(world_rect)
    previous_clip = screen.get_clip()
    screen.set_clip(previous_clip.clip(screen_rect))

    pygame.draw.rect(screen, (44, 30, 25), screen_rect)

    if soil_tile is not None:
        tile_width = max(1, soil_tile.get_width() - 2)
        tile_height = max(1, soil_tile.get_height() - 2)
        tile_positions = _visible_world_range(world_rect, camera, tile_width, screen.get_width())
        start_y = world_rect.top + 46
        end_y = world_rect.bottom
        for world_y in range(start_y, end_y, tile_height):
            for world_x in tile_positions:
                screen.blit(
                    soil_tile,
                    (world_x - int(camera.x) - 1, world_y - int(camera.y) - 1),
                )

    if ground_tiles:
        tile_width = max(1, ground_tiles[0].get_width() - 2)
        tile_positions = _visible_world_range(world_rect, camera, tile_width, screen.get_width())
        for world_x in tile_positions:
            tile_index = (world_x // tile_width) % len(ground_tiles)
            tile = ground_tiles[tile_index]
            screen.blit(
                tile,
                (world_x - int(camera.x) - 1, world_rect.top - int(camera.y) - 1),
            )

    screen.set_clip(previous_clip)


def draw_easy_platform(screen, camera, world_rect, variant=0, moving=False):
    terrain = _get_terrain()
    platform_tiles = [terrain[tile_id] for tile_id in _PLATFORM_TILE_IDS if tile_id in terrain]
    screen_rect = camera.apply(world_rect)
    previous_clip = screen.get_clip()
    strip_height = max((tile.get_height() for tile in platform_tiles), default=34)
    sprite_clip = pygame.Rect(
        screen_rect.left,
        screen_rect.top - 2,
        screen_rect.width,
        max(strip_height, screen_rect.height) + 2,
    )
    screen.set_clip(previous_clip.clip(sprite_clip))

    body_color = (62, 43, 29) if not moving else (75, 53, 33)
    pygame.draw.rect(screen, body_color, screen_rect)
    if moving:
        pygame.draw.line(
            screen,
            (112, 83, 43),
            (screen_rect.left, screen_rect.top + 2),
            (screen_rect.right, screen_rect.top + 2),
            2,
        )

    if platform_tiles:
        tile_width = max(1, platform_tiles[0].get_width() - 2)
        x = screen_rect.left
        index = variant % len(platform_tiles)
        while x < screen_rect.right:
            tile = platform_tiles[index]
            screen.blit(tile, (x - 1, screen_rect.top - 1))
            x += tile_width
            index = (index + 1) % len(platform_tiles)

    screen.set_clip(previous_clip)
