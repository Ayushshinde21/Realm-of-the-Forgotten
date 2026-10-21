"""Cached loader for the supplied Green Zone environment artwork."""
from __future__ import annotations

from pathlib import Path

import pygame

from src.paths import ASSETS_DIR

GREEN_ZONE_ROOT = ASSETS_DIR / "tilesets" / "green_zone"
TILES_DIR = GREEN_ZONE_ROOT / "tiles"
BACKGROUNDS_DIR = GREEN_ZONE_ROOT / "backgrounds"
OBJECTS_DIR = GREEN_ZONE_ROOT / "objects"
ANIMATED_OBJECTS_DIR = GREEN_ZONE_ROOT / "animated_objects"
TILE_SIZE = 32


def _load_surface(path: Path):
    try:
        image = pygame.image.load(str(path))
    except (pygame.error, OSError, FileNotFoundError):
        return None
    try:
        return image.convert_alpha()
    except pygame.error:
        return image.copy()


class GreenZoneTileset:
    """Load every Green Zone asset once; rendering reuses cached surfaces."""

    _instance = None

    def __init__(self):
        self.tiles: dict[int, pygame.Surface] = {}
        self.backgrounds: dict[str, dict[str, pygame.Surface]] = {"day": {}, "night": {}}
        self.objects: dict[str, pygame.Surface] = {}
        self.animations: dict[str, tuple[pygame.Surface, ...]] = {}
        self._scaled_backgrounds: dict[tuple[str, str, int, int], pygame.Surface] = {}
        self.loaded = False
        self._load()

    def _load(self):
        for path in sorted(TILES_DIR.glob("Tile_*.png")):
            try:
                tile_id = int(path.stem.split("_", 1)[1])
            except (ValueError, IndexError):
                continue
            image = _load_surface(path)
            if image is not None:
                self.tiles[tile_id] = image

        for time_of_day in ("day", "night"):
            for path in sorted((BACKGROUNDS_DIR / time_of_day).glob("*.png")):
                image = _load_surface(path)
                if image is not None:
                    self.backgrounds[time_of_day][path.stem] = image

        object_folders = {
            "trees": OBJECTS_DIR / "trees",
            "stones": OBJECTS_DIR / "stones",
            "fountains": OBJECTS_DIR / "fountains",
        }
        for folder_name, directory in object_folders.items():
            for path in sorted(directory.glob("*.png")):
                image = _load_surface(path)
                if image is not None:
                    self.objects[path.stem] = image

        layouts = {"Fountain": (72, 72), "Money": (24, 24)}
        for path in sorted(ANIMATED_OBJECTS_DIR.glob("*.png")):
            sheet = _load_surface(path)
            if sheet is None:
                continue
            frame_size = layouts.get(path.stem)
            if frame_size is None:
                continue
            frame_width, frame_height = frame_size
            if frame_height > sheet.get_height() or sheet.get_width() % frame_width:
                continue
            frames = []
            for x in range(0, sheet.get_width(), frame_width):
                frame = pygame.Rect(x, 0, frame_width, frame_height)
                frames.append(sheet.subsurface(frame).copy())
            if frames:
                self.animations[path.stem] = tuple(frames)

        self.loaded = bool(self.tiles) and bool(self.backgrounds["day"])

    def tile(self, tile_id: int):
        return self.tiles.get(int(tile_id))

    def background(self, name: str, time_of_day: str = "day"):
        return self.backgrounds.get(time_of_day, {}).get(name)

    def scaled_background(self, name: str, time_of_day: str, width: int, height: int):
        key = (time_of_day, name, int(width), int(height))
        if key not in self._scaled_backgrounds:
            image = self.background(name, time_of_day)
            if image is None:
                return None
            self._scaled_backgrounds[key] = pygame.transform.scale(image, (int(width), int(height)))
        return self._scaled_backgrounds[key]

    def object(self, name: str):
        return self.objects.get(name)

    def animation_frame(self, name: str, tick_ms: int | None = None, frame_ms: int = 150):
        frames = self.animations.get(name)
        if not frames:
            return None
        if tick_ms is None:
            tick_ms = pygame.time.get_ticks()
        return frames[(int(tick_ms) // max(1, int(frame_ms))) % len(frames)]


_instance = None


def get_tileset() -> GreenZoneTileset:
    global _instance
    if _instance is None:
        _instance = GreenZoneTileset()
    return _instance
