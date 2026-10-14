"""Level constants (split out of level.py)."""

# Random pixel-art backgrounds supplied for the game.
# Normal difficulty gets its own dedicated background set; easy/hard keep
# the original shared set.
BACKGROUND_FILES = [
    "assets/backgrounds/background_1.png",
    "assets/backgrounds/background_2.png",
    "assets/backgrounds/background_3.png",
    "assets/backgrounds/background_4.png",
]

NORMAL_BACKGROUND_FILES = [
    "assets/backgrounds/background_normal_1.png",
    "assets/backgrounds/background_normal_2.png",
    "assets/backgrounds/background_normal_3.png",
    "assets/backgrounds/background_normal_4.png",
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
ROCK_MIN_SPACING = 550
BUSH_MIN_SPACING = 90
ROCKS_PER_1000 = 2
BUSHES_PER_1000_MIN = 4
BUSHES_PER_1000_MAX = 5
