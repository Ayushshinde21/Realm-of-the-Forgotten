"""
Industrial tileset loader/slicer for NORMAL difficulty.

Loads assets/tilesets/normal_tileset.png ONCE, slices it into individual
pixel-art tiles using the real (measured) grid of the supplied sprite
sheet, and exposes them by semantic name so the renderer never has to
know raw row/column numbers.

The sheet is NOT a perfectly uniform grid (some tiles have a couple of
stray pixels of padding), so the exact pixel bounding box of every one
of the 10 columns x 8 rows was measured directly from the source image
and is hard-coded below. This avoids fractional/blurry slicing.
"""

import pygame

TILESET_PATH = "assets/tilesets/normal_tileset.png"

# Rendered tile size used everywhere in the industrial renderer.
# The source tiles are ~137-141px, which is a clean 3x of 48 -> keeps
# scaling as an integer-ish downscale instead of a blurry stretch.
TILE_SIZE = 48

# Measured (inclusive) pixel bounding boxes of each of the 10 columns
# and 8 rows of the source sheet (1800x1200).
_COL_BOUNDS = [
    (184, 320), (328, 465), (472, 607), (616, 753), (759, 897),
    (903, 1043), (1048, 1187), (1192, 1333), (1335, 1468), (1480, 1615),
]
_ROW_BOUNDS = [
    (25, 166), (169, 310), (313, 454), (457, 598),
    (601, 742), (745, 886), (890, 1024), (1034, 1174),
]


class IndustrialTileset:
    """Singleton-style tileset: loaded and sliced exactly once."""

    _instance = None

    def __init__(self):
        self.tile_size = TILE_SIZE
        self._cells = {}  # (row, col) -> pygame.Surface (TILE_SIZE x TILE_SIZE)
        self._named = {}
        self._loaded = False
        self._load()

    # ------------------------------------------------------------
    def _load(self):
        try:
            sheet = pygame.image.load(TILESET_PATH).convert_alpha()
        except (pygame.error, FileNotFoundError):
            self._loaded = False
            return

        for row, (y0, y1) in enumerate(_ROW_BOUNDS):
            for col, (x0, x1) in enumerate(_COL_BOUNDS):
                w = x1 - x0 + 1
                h = y1 - y0 + 1
                # Guard against sheet edits with different dimensions.
                w = max(1, min(w, sheet.get_width() - x0))
                h = max(1, min(h, sheet.get_height() - y0))
                try:
                    raw = sheet.subsurface(pygame.Rect(x0, y0, w, h)).copy()
                except ValueError:
                    continue
                tile = pygame.transform.scale(raw, (TILE_SIZE, TILE_SIZE))
                self._cells[(row, col)] = tile

        self._loaded = bool(self._cells)
        self._build_named_map()

    # ------------------------------------------------------------
    def _cell(self, row, col):
        return self._cells.get((row, col))

    def _build_named_map(self):
        c = self._cell

        # ---- platform / wall frame ----
        self._named.update({
            "CORNER_TOP_LEFT": c(0, 3),
            "TOP": c(0, 4),
            "CORNER_TOP_RIGHT": c(0, 5),
            "LEFT": c(1, 3),
            "CENTER": c(1, 4),
            "RIGHT": c(1, 5),
            "CORNER_BOTTOM_LEFT": c(2, 3),
            "BOTTOM": c(2, 4),
            "CORNER_BOTTOM_RIGHT": c(2, 5),

            # extra body/panel variants for visual variety
            "PANEL_VARIANT_1": c(6, 0),
            "PANEL_VARIANT_2": c(6, 1),
            "PANEL_VARIANT_3": c(7, 0),
            "PANEL_VARIANT_4": c(7, 1),
            "PANEL_PLAIN": c(0, 2),
            "PANEL_DARK": c(2, 2),

            # cross-braced structural panels (background walls)
            "CROSS_BRACE_1": c(0, 6),
            "CROSS_BRACE_2": c(0, 7),
            "BOLT_PANEL": c(0, 1),
            "BUTTON_PANEL": c(2, 6),
            "VENT_PANEL": c(2, 7),

            # hazard stripes
            "HAZARD_TOP_LEFT": c(3, 3),
            "HAZARD_TOP": c(3, 4),
            "HAZARD_TOP_RIGHT": c(3, 5),
            "HAZARD_CENTER": c(4, 4),
            "HAZARD_CENTER_2": c(4, 3),
            "HAZARD_BOTTOM_LEFT": c(7, 3),
            "HAZARD_BOTTOM": c(7, 4),
            "HAZARD_BOTTOM_RIGHT": c(7, 5),
            "HAZARD_SINGLE": c(0, 8),
            "HAZARD_CROSS": c(5, 6),

            # pipes (vertical, stack top->mid->bottom)
            "PIPE_TOP": c(4, 8),
            "PIPE_MID": c(5, 8),
            "PIPE_MID_2": c(6, 8),
            "PIPE_BOTTOM": c(7, 6),

            # support beams / small blocks
            "SUPPORT_BEAM": c(1, 8),
            "SUPPORT_BEAM_2": c(2, 8),
            "SUPPORT_BLOCK": c(1, 9),
            "SUPPORT_BLOCK_2": c(2, 9),
            "SUPPORT_SMALL": c(3, 9),

            # decoration
            "CROSS_X_BIG": c(3, 8),
            "CROSS_X_SMALL": c(6, 7),
            "WARNING_GATE": c(7, 7),
            "VENT_GRILLE": c(5, 1),
            "GRATE": c(5, 2),
            "DARK_VOID": c(5, 0),
            "LADDER": c(1, 0),
            "LADDER_2": c(3, 0),
            "ACCENT_PURPLE": c(2, 1),
            "ACCENT_PURPLE_2": c(3, 1),
            "CIRCLE_BUTTON": c(4, 0),
            "TRIANGLE_WEDGE": c(4, 1),
            "HALF_HAZARD": c(4, 9),
            "HALF_HAZARD_2": c(7, 8),
        })

    # ------------------------------------------------------------
    @property
    def loaded(self):
        return self._loaded

    def get(self, name):
        """Return a named tile surface, or None if unavailable."""
        return self._named.get(name)

    def get_variant(self, names, index):
        """Pick a deterministic variant from a list of tile names."""
        valid = [self._named.get(n) for n in names if self._named.get(n)]
        if not valid:
            return None
        return valid[index % len(valid)]


_tileset_instance = None


def get_tileset():
    """Return the process-wide IndustrialTileset, creating it once."""
    global _tileset_instance
    if _tileset_instance is None:
        _tileset_instance = IndustrialTileset()
    return _tileset_instance
