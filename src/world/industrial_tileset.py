"""Cached loader for the supplied Industrial Zone asset pack.

The pack contains individual 32px tiles and separated background, object,
and animation categories; it is not a single tile sheet. All paths are rooted
at the project assets directory so launching from another working directory
still finds the art.
"""
from __future__ import annotations

from pathlib import Path

import pygame

from src.paths import ASSETS_DIR

TILE_SIZE = 32
INDUSTRIAL_ROOT = ASSETS_DIR / "tilesets" / "industrial_zone"
TILES_DIR = INDUSTRIAL_ROOT / "tiles"
BACKGROUNDS_DIR = INDUSTRIAL_ROOT / "backgrounds"
OBJECTS_DIR = INDUSTRIAL_ROOT / "objects"
ANIMATED_OBJECTS_DIR = INDUSTRIAL_ROOT / "animated_objects"

# Every supplied animation strip is horizontal. Frame dimensions are explicit
# because several sheets are not square (Entry and Hammer are 32x64 frames).
_ANIMATION_LAYOUT = {
    "Card": (24, 24),
    "Chest": (32, 32),
    "Entry": (32, 64),
    "Hammer": (32, 64),
    "Money": (24, 24),
    "Platform": (32, 32),
    "Screen1": (32, 32),
    "Screen2": (32, 42),
    "Transporter": (32, 32),
    "Transporter1": (32, 32),
    "Transporter2": (32, 32),
    "Transporter3": (32, 32),
}

# Semantic aliases retained for compatibility with code/tests that used the
# old interface. They point to actual individual assets in this pack.
_TILE_ALIASES = {
    "CORNER_TOP_LEFT": 73,
    "TOP": 77,
    "CORNER_TOP_RIGHT": 79,
    "LEFT": 55,
    "CENTER": 5,
    "RIGHT": 56,
    "CORNER_BOTTOM_LEFT": 64,
    "BOTTOM": 65,
    "CORNER_BOTTOM_RIGHT": 66,
    "PANEL_VARIANT_1": 4,
    "PANEL_VARIANT_2": 6,
    "PANEL_VARIANT_3": 12,
    "PANEL_VARIANT_4": 16,
    "PANEL_PLAIN": 14,
    "PANEL_DARK": 21,
    "CROSS_BRACE_1": 62,
    "CROSS_BRACE_2": 71,
    "BOLT_PANEL": 7,
    "BUTTON_PANEL": 74,
    "VENT_PANEL": 18,
    "HAZARD_TOP_LEFT": 31,
    "HAZARD_TOP": 80,
    "HAZARD_TOP_RIGHT": 81,
    "HAZARD_CENTER": 40,
    "HAZARD_CENTER_2": 34,
    "HAZARD_BOTTOM_LEFT": 49,
    "HAZARD_BOTTOM": 58,
    "HAZARD_BOTTOM_RIGHT": 60,
    "HAZARD_SINGLE": 9,
    "HAZARD_CROSS": 36,
    "PIPE_TOP": 61,
    "PIPE_MID": 70,
    "PIPE_MID_2": 63,
    "PIPE_BOTTOM": 72,
    "SUPPORT_BEAM": 70,
    "SUPPORT_BEAM_2": 61,
    "SUPPORT_BLOCK": 73,
    "SUPPORT_BLOCK_2": 64,
    "SUPPORT_SMALL": 18,
    "CROSS_X_BIG": 71,
    "CROSS_X_SMALL": 62,
    "WARNING_GATE": 31,
    "VENT_GRILLE": 18,
    "GRATE": 62,
    "DARK_VOID": 46,
    "LADDER": 61,
    "LADDER_2": 70,
    "ACCENT_PURPLE": 1,
    "ACCENT_PURPLE_2": 10,
    "CIRCLE_BUTTON": 37,
    "TRIANGLE_WEDGE": 38,
    "HALF_HAZARD": 80,
    "HALF_HAZARD_2": 81,
}


def _load_surface(path: Path):
    """Load an image once, preserving alpha and supporting dummy/test displays."""
    try:
        image = pygame.image.load(str(path))
    except (pygame.error, OSError, FileNotFoundError):
        return None
    try:
        return image.convert_alpha()
    except pygame.error:
        return image.copy()


class IndustrialTileset:
    """Singleton-style asset cache for the complete industrial environment."""

    _instance = None

    def __init__(self):
        self.tile_size = TILE_SIZE
        self.tiles: dict[int, pygame.Surface] = {}
        self.objects: dict[str, pygame.Surface] = {}
        self.backgrounds: dict[str, pygame.Surface] = {}
        self.animated_sheets: dict[str, pygame.Surface] = {}
        self.animations: dict[str, tuple[pygame.Surface, ...]] = {}
        self._scaled_backgrounds: dict[tuple[str, int], pygame.Surface] = {}
        self._named = {}
        self.loaded = False
        self._load()

    def _load(self):
        for path in sorted(TILES_DIR.glob("IndustrialTile_*.png")):
            try:
                tile_id = int(path.stem.rsplit("_", 1)[1])
            except (ValueError, IndexError):
                continue
            image = _load_surface(path)
            if image is not None:
                self.tiles[tile_id] = image

        for directory, destination in (
            (BACKGROUNDS_DIR, self.backgrounds),
            (OBJECTS_DIR, self.objects),
        ):
            for path in sorted(directory.glob("*.png")):
                image = _load_surface(path)
                if image is not None:
                    destination[path.stem] = image

        for path in sorted(ANIMATED_OBJECTS_DIR.glob("*.png")):
            name = path.stem
            sheet = _load_surface(path)
            if sheet is None:
                continue
            self.animated_sheets[name] = sheet
            frame_size = _ANIMATION_LAYOUT.get(name)
            if frame_size is None:
                continue
            frame_width, frame_height = frame_size
            frame_count = sheet.get_width() // frame_width
            if frame_count < 1 or frame_height > sheet.get_height():
                continue
            frames = []
            for index in range(frame_count):
                frame_rect = pygame.Rect(index * frame_width, 0, frame_width, frame_height)
                if frame_rect.right > sheet.get_width():
                    break
                frames.append(sheet.subsurface(frame_rect).copy())
            if frames:
                self.animations[name] = tuple(frames)

        self.loaded = bool(self.tiles)
        self._named = {name: self.tiles.get(tile_id) for name, tile_id in _TILE_ALIASES.items()}

    def tile(self, tile_id: int):
        return self.tiles.get(int(tile_id))

    def get(self, name: str):
        """Get a semantic alias or an actual tile name such as TILE_77."""
        if name in self._named:
            return self._named[name]
        if name.startswith("TILE_"):
            try:
                return self.tile(int(name.split("_", 1)[1]))
            except ValueError:
                return None
        return None

    def get_variant(self, names, index):
        valid = [self.get(name) for name in names]
        valid = [image for image in valid if image is not None]
        return valid[index % len(valid)] if valid else None

    def object(self, name: str):
        return self.objects.get(name)

    def background(self, name: str):
        return self.backgrounds.get(name)

    def background_layer(self, name: str, scale: int = 2):
        """Return an integer-scaled cached layer (nearest-neighbour pixel art)."""
        key = (name, int(scale))
        if key not in self._scaled_backgrounds:
            source = self.backgrounds.get(name)
            if source is None:
                return None
            target_size = (source.get_width() * scale, source.get_height() * scale)
            self._scaled_backgrounds[key] = pygame.transform.scale(source, target_size)
        return self._scaled_backgrounds[key]

    def animation_frame(self, name: str, tick_ms: int | None = None, frame_ms: int = 150):
        frames = self.animations.get(name)
        if not frames:
            return None
        if tick_ms is None:
            tick_ms = pygame.time.get_ticks()
        index = (int(tick_ms) // max(1, int(frame_ms))) % len(frames)
        return frames[index]


_tileset_instance = None


def get_tileset():
    """Return a process-wide asset cache; loading occurs only once."""
    global _tileset_instance
    if _tileset_instance is None:
        _tileset_instance = IndustrialTileset()
    return _tileset_instance
