"""Sprite config and animation loading for sprite-driven enemies (split out of enemy.py)."""
import os
import pygame


# ==================================================
# SPRITE-DRIVEN ENEMIES (normal difficulty only)
# ==================================================
# These 6 enemy "sprite_key" types come with real animated sprite sheets
# (idle/run/attack/hurt/death) instead of the vector-drawn shapes used by
# the classic slime/fast/jumper/flyer/heavy types. They patrol normally
# and only attack once they notice the player.
SPRITE_ENEMY_TYPES = (
    "worker", "soldier", "boxer", "minebot", "chopper", "hammerbot",
    "green_slime", "blue_slime", "red_slime",
    "swordsman_pink", "swordsman_silver", "swordsman_blue",
)

SPRITE_ENEMY_CONFIG = {
    # Ground melee: simple punch when the player gets close.
    "worker": {
        "target_h": 62, "style": "melee",
        "detect": 230, "act_range": 46, "cooldown": 55, "hit_frame": 3,
    },
    # Ground ranged: keeps its distance and fires a straight bullet.
    "soldier": {
        "target_h": 62, "style": "ranged",
        "detect": 430, "act_range": 260, "cooldown": 85, "hit_frame": 1,
    },
    # Ground melee: heavier boxing flurry, slightly longer reach.
    "boxer": {
        "target_h": 68, "style": "melee",
        "detect": 240, "act_range": 52, "cooldown": 60, "hit_frame": 3,
    },
    # Ground rush: sprints at the player and self-destructs on arrival.
    "minebot": {
        "target_h": 40, "style": "rush",
        "detect": 260, "act_range": 40, "cooldown": 999999,
        "hit_frame": 2, "chase_speed": 2.6,
    },
    # Flyer: patrols above, drops a gravity-affected bomb on the player.
    "chopper": {
        "target_h": 56, "style": "bomber",
        "detect": 480, "act_range": 90, "cooldown": 130, "hit_frame": 2,
    },
    # Ground melee: slow tank with a heavy left-right hammer swing.
    "hammerbot": {
        "target_h": 74, "style": "melee",
        "detect": 250, "act_range": 62, "cooldown": 70, "hit_frame": 3,
    },
    # Animated slimes use the supplied pixel-art sheets. They are simpler,
    # short-range enemies suited to Easy and the later Hard encounters.
    "green_slime": {
        "target_h": 62, "style": "melee",
        "detect": 175, "act_range": 38, "cooldown": 78, "hit_frame": 2,
    },
    "blue_slime": {
        "target_h": 62, "style": "melee",
        "detect": 190, "act_range": 42, "cooldown": 72, "hit_frame": 2,
    },
    "red_slime": {
        "target_h": 66, "style": "melee",
        "detect": 215, "act_range": 46, "cooldown": 65, "hit_frame": 2,
    },
    # Sword-wielding pixel heroes are additional Easy-only ground enemies.
    # Their cooldowns and attack reach are deliberately forgiving.
    "swordsman_pink": {
        "target_h": 54, "style": "melee",
        "detect": 185, "act_range": 43, "cooldown": 88, "hit_frame": 3,
    },
    "swordsman_silver": {
        "target_h": 56, "style": "melee",
        "detect": 195, "act_range": 44, "cooldown": 84, "hit_frame": 3,
    },
    "swordsman_blue": {
        "target_h": 58, "style": "melee",
        "detect": 205, "act_range": 46, "cooldown": 80, "hit_frame": 3,
    },
}

ENEMY_ANIM_NAMES = ("idle", "run", "attack", "hurt", "death")

_ENEMY_FRAME_CACHE = {}

_ENEMY_ASSET_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "assets",
    "enemies"
)


def _enemy_frame_files(sprite_key, anim_name):
    directory = os.path.join(_ENEMY_ASSET_ROOT, sprite_key, anim_name)
    if not os.path.isdir(directory):
        return []
    files = [
        f for f in os.listdir(directory)
        if f.startswith("frame_") and f.endswith(".png")
    ]
    files.sort(key=lambda f: int(f.split("_")[1].split(".")[0]))

    # Hammerbot idle frame 4/5 contain only the hammer head from the source
    # animation sheet. Keeping them makes the robot's upper body disappear
    # for two idle frames. Use the four complete robot poses instead.
    if sprite_key == "hammerbot" and anim_name == "idle":
        files = files[:4]

    return [os.path.join(directory, f) for f in files]


def _load_enemy_animations(sprite_key, target_h):
    """Loads + scales every animation for a sprite-driven enemy type once,
    caching the result so repeated spawns of the same type are cheap."""

    cache_key = (sprite_key, target_h)
    if cache_key in _ENEMY_FRAME_CACHE:
        return _ENEMY_FRAME_CACHE[cache_key]

    reference = _enemy_frame_files(sprite_key, "idle") or _enemy_frame_files(sprite_key, "run")

    tallest = 0
    for path in reference:
        try:
            image = pygame.image.load(path)
            tallest = max(tallest, image.get_height())
        except (pygame.error, FileNotFoundError):
            continue

    scale = (target_h / float(tallest)) if tallest > 0 else 1.0

    animations = {}
    for anim_name in ENEMY_ANIM_NAMES:
        frames = []
        for path in _enemy_frame_files(sprite_key, anim_name):
            try:
                image = pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                continue
            new_w = max(1, round(image.get_width() * scale))
            new_h = max(1, round(image.get_height() * scale))
            frames.append(pygame.transform.scale(image, (new_w, new_h)))
        animations[anim_name] = frames

    _ENEMY_FRAME_CACHE[cache_key] = animations
    return animations
