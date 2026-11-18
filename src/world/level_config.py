"""Level constants (split out of level.py)."""

# Legacy Adventure backgrounds used as static fallbacks. Normal renders its
# Green Zone layers from assets/tilesets/green_zone/backgrounds/.
BACKGROUND_FILES = [
    "assets/backgrounds/background_1.png",
    "assets/backgrounds/background_2.png",
    "assets/backgrounds/background_3.png",
    "assets/backgrounds/background_4.png",
]

# Extra pit depth so falling players reach a visible death floor.
PIT_FLOOR_OFFSET = 35

# The 4 optional objectives a level can ask for on top of "complete the
# level" (which is always required). Each level randomly picks 2 of these
# as its actual quests, so there are always exactly 3 quests -> 3 stars:
# 1 for completing + 1 for each of the 2 chosen objectives.
QUEST_DEFINITIONS = [
    "killed_all_enemies",
    "no_enemy_hits",
    "collected_all_coins",
    "within_time_limit",
]

ITEM_MIN_SPACING = 140
