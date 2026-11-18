"""Definitions for the two-world, twenty-level campaign."""

from src.settings import MAX_LEVELS, WORLD_LEVEL_COUNT, WORLD_NAMES

# Internal generation profiles retained from the two original campaigns.
# They are selected automatically by the global level number.
WORLD_PROFILES = {1: "easy", 2: "normal"}

WORLD_LEVEL_NAMES = {
    1: [
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
    ],
    2: [
        "Whispering Woods",
        "Forgotten Village",
        "Rotting Outpost",
        "Misty Graveyard",
        "Undead Stronghold",
        "Ironwood Forest",
        "Abandoned Factory",
        "Toxic Foundry",
        "Dark Citadel",
        "Greenwild Core",
    ],
}

_WIDTH_START = {"easy": 3500, "normal": 5000}
_WIDTH_STEP = {"easy": 800, "normal": 1100}


def world_for_level(level_number):
    """Return (world_number, local_level, internal_profile) for a global level."""
    level_number = max(1, min(MAX_LEVELS, int(level_number)))
    world_number = 1 if level_number <= WORLD_LEVEL_COUNT else 2
    local_level = level_number - (world_number - 1) * WORLD_LEVEL_COUNT
    return world_number, local_level, WORLD_PROFILES[world_number]


def campaign_progress(level_number):
    """Return a 0.0-1.0 difficulty-ramp value across all twenty levels."""
    level_number = max(1, min(MAX_LEVELS, int(level_number)))
    return (level_number - 1) / max(1, MAX_LEVELS - 1)


def _build_levels():
    levels = {profile: {} for profile in WORLD_PROFILES.values()}
    for world_number, profile in WORLD_PROFILES.items():
        start = _WIDTH_START[profile]
        step = _WIDTH_STEP[profile]
        for local_level in range(1, WORLD_LEVEL_COUNT + 1):
            world_width = start + step * (local_level - 1)
            levels[profile][local_level] = {
                "name": WORLD_LEVEL_NAMES[world_number][local_level - 1],
                "world_number": world_number,
                "world_name": WORLD_NAMES[world_number],
                "world_level": local_level,
                "difficulty": profile.capitalize(),
                "world_width": world_width,
                "player_start": (100, 400),
                "finish_x": world_width - 200,
            }
    return levels


LEVELS = _build_levels()
