"""Sprite config and animation loading for sprite-driven enemies (split out of enemy.py)."""
import os
import pygame


# ==================================================
# SPRITE-DRIVEN ENEMIES (World 2 only)
# ==================================================
# Sprite-driven enemies use cached idle/run/attack/hurt/death animations.
# World 2 uses the seven zombie variants below; World 1 keeps its separate
# slime/swordsman enemy roster.
NORMAL_ZOMBIE_TYPES = (
    "zombie_1", "zombie_2", "zombie_3", "zombie_4",
    "wild_zombie", "zombie_man", "zombie_woman",
)

SPRITE_ENEMY_TYPES = (
    "worker", "soldier", "boxer", "minebot", "chopper", "hammerbot",
    "green_slime", "blue_slime", "red_slime",
    "swordsman_pink", "swordsman_silver", "swordsman_blue",
    *NORMAL_ZOMBIE_TYPES,
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
    # short-range enemies suited to World 1 and later campaign levels.
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
    # Sword-wielding pixel heroes are additional World 1 ground enemies.
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
    # World 2's complete enemy roster uses the supplied zombie
    # spritesheets. The variants share melee behavior but differ in height,
    # detection, reach, and recovery to retain useful enemy variety.
    "zombie_1": {
        "target_h": 62, "style": "melee", "detect": 225,
        "act_range": 47, "cooldown": 68, "hit_frame": 2,
    },
    "zombie_2": {
        "target_h": 60, "style": "melee", "detect": 210,
        "act_range": 44, "cooldown": 62, "hit_frame": 2,
    },
    "zombie_3": {
        "target_h": 62, "style": "melee", "detect": 245,
        "act_range": 50, "cooldown": 74, "hit_frame": 2,
    },
    "zombie_4": {
        "target_h": 65, "style": "melee", "detect": 250,
        "act_range": 54, "cooldown": 80, "hit_frame": 4,
    },
    "wild_zombie": {
        "target_h": 64, "style": "melee", "detect": 270,
        "act_range": 57, "cooldown": 58, "hit_frame": 2,
    },
    "zombie_man": {
        "target_h": 63, "style": "melee", "detect": 235,
        "act_range": 51, "cooldown": 66, "hit_frame": 2,
    },
    "zombie_woman": {
        "target_h": 61, "style": "melee", "detect": 220,
        "act_range": 47, "cooldown": 64, "hit_frame": 2,
    },
}

ENEMY_ANIM_NAMES = ("idle", "run", "attack", "hurt", "death")

_ENEMY_FRAME_CACHE = {}

_ENEMY_ASSET_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "assets",
    "enemies"
)
_ZOMBIE_SHEETS_ROOT = os.path.join(_ENEMY_ASSET_ROOT, "zombie_sheets")
_ZOMBIE_FRAME_ROOT = os.path.join(_ZOMBIE_SHEETS_ROOT, "frames")

# Each supplied image is a horizontal spritesheet of square, transparent
# frames. The aliases adapt the source pack's naming to the shared enemy AI.
_ZOMBIE_SHEET_CONFIG = {
    "zombie_1": ("urban_pack/Zombie_1", {
        "idle": "Idle.png", "run": "Walk.png", "attack": "Attack.png",
        "hurt": "Hurt.png", "death": "Dead.png",
    }),
    "zombie_2": ("urban_pack/Zombie_2", {
        "idle": "Idle.png", "run": "Walk.png", "attack": "Attack.png",
        "hurt": "Hurt.png", "death": "Dead.png",
    }),
    "zombie_3": ("urban_pack/Zombie_3", {
        "idle": "Idle.png", "run": "Walk.png", "attack": "Attack.png",
        "hurt": "Hurt.png", "death": "Dead.png",
    }),
    "zombie_4": ("urban_pack/Zombie_4", {
        "idle": "Idle.png", "run": "Walk.png", "attack": "Attack.png",
        "hurt": "Hurt.png", "death": "Dead.png",
    }),
    "wild_zombie": ("variety_pack/Wild Zombie", {
        "idle": "Idle.png", "run": "Run.png", "attack": "Attack_1.png",
        "hurt": "Hurt.png", "death": "Dead.png",
    }),
    "zombie_man": ("variety_pack/Zombie Man", {
        "idle": "Idle.png", "run": "Run.png", "attack": "Attack_1.png",
        "hurt": "Hurt.png", "death": "Dead.png",
    }),
    "zombie_woman": ("variety_pack/Zombie Woman", {
        "idle": "Idle.png", "run": "Run.png", "attack": "Attack_1.png",
        "hurt": "Hurt.png", "death": "Dead.png",
    }),
}


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


def _load_zombie_sheet_animations(sprite_key, target_h):
    """Load and cache explicit zombie animation frames, with a sheet fallback."""
    folder, anim_files = _ZOMBIE_SHEET_CONFIG[sprite_key]
    animations = {}
    target_h = max(1, int(target_h))

    for anim_name in ENEMY_ANIM_NAMES:
        filename = anim_files.get(anim_name)
        if not filename:
            animations[anim_name] = []
            continue

        frame_action = os.path.splitext(filename)[0]
        frame_dir = os.path.join(_ZOMBIE_FRAME_ROOT, folder, frame_action)
        frame_paths = []
        if os.path.isdir(frame_dir):
            frame_paths = [
                os.path.join(frame_dir, name)
                for name in os.listdir(frame_dir)
                if name.startswith("frame_") and name.endswith(".png")
            ]
            frame_paths.sort(key=lambda name: int(os.path.basename(name).split("_")[1].split(".")[0]))

        source_frames = []
        if frame_paths:
            for frame_path in frame_paths:
                try:
                    source_frames.append(pygame.image.load(frame_path).convert_alpha())
                except (pygame.error, FileNotFoundError):
                    continue
        else:
            # Compatibility fallback: slice the original horizontal sheet if
            # explicit frame assets are missing (for example, older installs).
            path = os.path.join(_ZOMBIE_SHEETS_ROOT, folder, filename)
            try:
                sheet = pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                animations[anim_name] = []
                continue

            frame_size = sheet.get_height()
            if frame_size <= 0 or sheet.get_width() < frame_size:
                animations[anim_name] = []
                continue

            frame_count = sheet.get_width() // frame_size
            for index in range(frame_count):
                frame_rect = pygame.Rect(index * frame_size, 0, frame_size, frame_size)
                frame = sheet.subsurface(frame_rect).copy()
                source_frames.append(frame)

        alpha_bounds = []
        for frame in source_frames:
            bounds = frame.get_bounding_rect(min_alpha=16)
            if bounds.width and bounds.height:
                alpha_bounds.append(bounds)

        # Crop shared bounds per animation to remove transparent frame padding
        # without making the character jump sideways between adjacent frames.
        if not alpha_bounds:
            animations[anim_name] = []
            continue
        left = min(bounds.left for bounds in alpha_bounds)
        top = min(bounds.top for bounds in alpha_bounds)
        right = max(bounds.right for bounds in alpha_bounds)
        bottom = max(bounds.bottom for bounds in alpha_bounds)
        crop_rect = pygame.Rect(left, top, right - left, bottom - top)
        source_height = max(1, crop_rect.height)
        target_width = max(1, round(crop_rect.width * target_h / source_height))

        frames = []
        for frame in source_frames:
            cropped = frame.subsurface(crop_rect).copy()
            frames.append(pygame.transform.scale(cropped, (target_width, target_h)))
        animations[anim_name] = frames

    return animations


def _load_enemy_animations(sprite_key, target_h):
    """Loads + scales animations once so repeated spawns stay inexpensive."""
    cache_key = (sprite_key, target_h)
    if cache_key in _ENEMY_FRAME_CACHE:
        return _ENEMY_FRAME_CACHE[cache_key]

    if sprite_key in _ZOMBIE_SHEET_CONFIG:
        animations = _load_zombie_sheet_animations(sprite_key, target_h)
        _ENEMY_FRAME_CACHE[cache_key] = animations
        return animations

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
