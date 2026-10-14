"""
Level definitions.

Each difficulty (easy / normal / hard) has its own independent set of
MAX_LEVELS levels (see src.settings.MAX_LEVELS). Progress, unlocks, stars,
and checkpoints are all tracked separately per difficulty (see
src.systems.save_system), so LEVELS[difficulty][n] is a fully separate
level slot from LEVELS[other_difficulty][n], even though they share a name.
"""

from src.settings import MAX_LEVELS

DIFFICULTIES = ("easy", "normal", "hard")

# Flavor names for levels 1..MAX_LEVELS, reused across difficulties.
LEVEL_NAMES = [
    "Snackland Meadows",
    "Dangerous Kitchen",
    "Chef's Castle",
    "Pumpkin Patch",
    "Soggy Swamp",
    "Frosty Freezer",
    "Spice Rack Peaks",
    "Sizzling Skillet",
    "Candy Cliffs",
    "Snackland Summit",
]

# World width for level 1 and how much wider each subsequent level gets,
# per difficulty. Harder difficulties start bigger and grow faster.
_WIDTH_START = {"easy": 3500, "normal": 5000, "hard": 6500}
_WIDTH_STEP = {"easy": 800, "normal": 1100, "hard": 1400}


def _build_levels():
    levels = {}
    for difficulty in DIFFICULTIES:
        levels[difficulty] = {}
        start = _WIDTH_START[difficulty]
        step = _WIDTH_STEP[difficulty]
        for n in range(1, MAX_LEVELS + 1):
            world_width = start + step * (n - 1)
            name_index = (n - 1) % len(LEVEL_NAMES)
            levels[difficulty][n] = {
                "name": LEVEL_NAMES[name_index],
                "difficulty": difficulty.capitalize(),
                "world_width": world_width,
                "player_start": (100, 400),
                "finish_x": world_width - 200,
            }
    return levels


LEVELS = _build_levels()
