WIDTH = 960
HEIGHT = 540
FPS = 60
TITLE = "Veggie Quest: Rescue at Snackland"
FULLSCREEN = False
WORLD_WIDTH = 100000

# Vertical size of the game world. The ground sits near the bottom of
# this space (WORLD_HEIGHT - 80) and platforms/structures can be
# generated well above the screen, letting the camera pan upward as
# the player climbs instead of the world being a single flat strip.
WORLD_HEIGHT = 1500

# Camera smoothing / dead-zone tuning.
CAMERA_SMOOTHNESS = 0.10
CAMERA_DEADZONE_X = 140
CAMERA_DEADZONE_Y = 90

VERSION = "1.0.0"

# The campaign is one continuous progression split into two worlds.
# World 1 uses the former Easy content (levels 1-10); World 2 uses the
# former Normal content (levels 11-20). Difficulty is selected automatically
# from the global level number rather than from a separate menu.
WORLD_LEVEL_COUNT = 10
MAX_LEVELS = WORLD_LEVEL_COUNT * 2
WORLD_NAMES = {
    1: "Snackland Meadows",
    2: "Greenwild Frontier",
}

# Score thresholds for star ratings: below the first value = 1 star,
# below the second value = 2 stars, otherwise 3 stars.
STAR_THRESHOLDS = (300, 600)

SKY_BLUE = (135, 206, 235)
GROUND_GREEN = (80, 180, 80)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_SPEED = 5
PLAYER_GRAVITY = 0.8
PLAYER_JUMP_STRENGTH = -14

# Derived from the physics above, so they can never drift out of sync.
# Flat jump: airtime = 2 * jump / gravity frames, distance = speed * airtime.
# (The old hard-coded 500 was far beyond what the player can actually jump.)
MAX_JUMP_VERTICAL = int(PLAYER_JUMP_STRENGTH ** 2 / (2 * PLAYER_GRAVITY))      # 122
MAX_JUMP_HORIZONTAL = int(PLAYER_SPEED * 2 * abs(PLAYER_JUMP_STRENGTH) / PLAYER_GRAVITY)  # 175
