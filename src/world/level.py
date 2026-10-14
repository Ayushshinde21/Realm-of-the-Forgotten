import pygame
import random
import os
import math

from src.settings import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, MAX_LEVELS
from src.entities.player import Player
from src.entities.platform import Platform
from src.entities.moving_platform import MovingPlatform
from src.entities.collectible import Collectible
from src.entities.checkpoint import Checkpoint
from src.world.camera import Camera
from src.world.platform_generator import PlatformGenerator
from src.entities.obstacle import Obstacle
from src.entities.bush import Bush
from src.entities.enemy import Enemy, SPRITE_ENEMY_TYPES
from src.entities.boss import Boss
from src.entities.projectile import Projectile
from src.systems.save_system import save_game, load_game
from src.effects.particle import Particle
from src.entities.npc import NPC
from src.systems.dialogue import Dialogue
from src.world.level_data import LEVELS
from src.world.industrial_renderer import (
    draw_industrial_platform,
    draw_industrial_ground,
    draw_industrial_moving_platform,
    draw_industrial_pit,
    draw_industrial_background,
)
from src.world.easy_tileset import (
    draw_easy_ground,
    draw_easy_platform,
)

from src.world.level_config import (  # noqa: F401
    BACKGROUND_FILES,
    NORMAL_BACKGROUND_FILES,
    PIT_FLOOR_OFFSET,
    QUEST_DEFINITIONS,
    ITEM_MIN_SPACING,
    ROCK_MIN_SPACING,
    BUSH_MIN_SPACING,
    ROCKS_PER_1000,
    BUSHES_PER_1000_MIN,
    BUSHES_PER_1000_MAX,
)


# Enemies farther than this (px) from the player are not updated, and
# enemies/coins farther than DRAW_MARGIN outside the screen are not drawn.
ENTITY_ACTIVE_RANGE = 1800
DRAW_MARGIN = 300
EASY_SLIME_SIZE_MULTIPLIER = 1.12
EASY_ENEMY_SPACING = 450  # Aim for one enemy per 450 horizontal world pixels.
EASY_ENEMY_START_BUFFER = 300
EASY_ENEMY_MIN_SEPARATION = 260
EASY_SLIME_TYPES = ("green_slime", "blue_slime", "red_slime")
EASY_SWORDSMAN_TYPES = ("swordsman_pink", "swordsman_silver", "swordsman_blue")
EASY_COIN_SIZE = 30
EASY_COIN_DRAW_HEIGHT = 34
EASY_COIN_LINE_OFFSET = 18
EASY_COIN_ARC_HEIGHT = 28
EASY_COIN_SPACING = 42
EASY_COIN_MAX_RAISE = 108
_EASY_COIN_FRAME_CACHE = None


class Level:

    def __init__(self, seed=None, level_number=1, sound_manager=None, difficulty="normal"):

        super().__init__()
        self.level_number = level_number
        self.difficulty = str(difficulty).lower() if str(difficulty).lower() in ("easy", "normal", "hard") else "normal"
        self.start_time = pygame.time.get_ticks()
        self.elapsed_seconds = 0.0
        self.damage_taken = False
        self.new_collectibles = 0
        self.star_rating = 1
        self.star_breakdown = None
        self.fail_requested = False

        # Levels are looked up per-difficulty: LEVELS[difficulty][level_number].
        # Each difficulty has its own independent set of MAX_LEVELS levels.
        difficulty_levels = LEVELS.get(self.difficulty, LEVELS["normal"])
        self.level_config = dict(difficulty_levels.get(
            level_number,
            difficulty_levels[1]
        ))
        self.is_boss_level = self.difficulty == "easy" and level_number in (5, 10)
        self.boss_kind = "orc" if self.is_boss_level and level_number == 5 else (
            "yokai" if self.is_boss_level and level_number == 10 else None
        )
        self.boss = None
        if self.is_boss_level:
            arena_width = 1050
            self.level_config["name"] = "Orc Boss Fight" if self.boss_kind == "orc" else "Yokai Boss Fight"
            self.level_config["world_width"] = arena_width
            self.level_config["finish_x"] = arena_width - 160

        self.level_name = self.level_config["name"]
        self.level_difficulty = self.level_config["difficulty"]
        self.world_width = self.level_config["world_width"]
        self.finish_x = self.level_config["finish_x"]

        # Time-based star threshold: 60s baseline, +30s for every extra
        # 2500px of world width (60 / 90 / 120 / 150 / ...), so wider
        # levels give proportionally more time to earn the time star.
        self.time_limit_seconds = 60 + 30 * (self.world_width // 2500)

        # Enemy-hit tracking is separate from damage_taken (which also
        # covers bush/rock hazards) so the "no enemy hits" star can be
        # judged purely on enemy contact, per the star rules.
        self.enemy_hit_taken = False

        # Level-specific platform difficulty ramps smoothly from level 1
        # to MAX_LEVELS instead of being hardcoded to 3 fixed levels.
        level_progress = (self.level_number - 1) / max(1, MAX_LEVELS - 1)
        if level_progress < 0.34:
            self.platform_difficulty = "easy"
        elif level_progress < 0.67:
            self.platform_difficulty = "medium"
        else:
            self.platform_difficulty = "hard"

        # Player-selected difficulty controls world generation and enemy behavior.
        if self.difficulty == "easy":
            self.enemy_spawn_multiplier = 0.70
            self.enemy_speed_multiplier = 0.90
        elif self.difficulty == "hard":
            self.enemy_spawn_multiplier = 1.15
            self.enemy_speed_multiplier = 1.35
        else:
            self.enemy_spawn_multiplier = 1.0
            self.enemy_speed_multiplier = 1.0

        self.sound_manager = sound_manager

        # ==========================================
        # LEVEL SEED
        # ==========================================
        if seed is None:
            seed = random.randint(
                0,
                999999999
            )

        self.seed = seed

        random.seed(self.seed)

        # ==========================================
        # RANDOM QUESTS
        # ==========================================
        # Always 3 quests total: "complete the level" (implicit, always
        # required) plus 2 randomly chosen from QUEST_DEFINITIONS below.
        self.active_quests = random.sample(QUEST_DEFINITIONS, 2)

        # ==========================================
        # RANDOM BACKGROUND
        # ==========================================
        # Pick one of the supplied backgrounds for this level instance.
        # The image is scaled once to the game window and stays fixed
        # behind the scrolling world.
        background_pool = (
            NORMAL_BACKGROUND_FILES
            if self.difficulty == "normal"
            else BACKGROUND_FILES
        )
        self.background_path = random.choice(background_pool)
        try:
            self.background_image = pygame.image.load(
                self.background_path
            ).convert()
            self.background_image = pygame.transform.scale(
                self.background_image,
                (WIDTH, HEIGHT)
            )
        except (pygame.error, FileNotFoundError):
            self.background_image = None

        # ==========================================
        # WORLD
        # ==========================================

        self.width = self.level_config["world_width"]
        self.world_height = WORLD_HEIGHT

        # ==========================================
        # CAMERA
        # ==========================================

        self.camera = Camera()
        if self.is_boss_level:
            self.camera.world_width = self.width

        # ==========================================
        # GROUND
        # ==========================================

        # Slightly deeper ground so the bottom of the world feels less thin.
        self.ground = Platform(
            0,
            self.world_height - 80,
            self.width,
            100
        )

        # ==========================================
        # PLATFORM GENERATOR
        # ==========================================

        self.generator = PlatformGenerator(self.width, world_height=self.world_height)

        # Normal keeps its doubled platforms. Easy platforms are lengthened
        # by 35% to support safer traversal and the new continuous coin paths.
        # Hard keeps its existing geometry unchanged.
        self.generator.platform_size_multiplier = (
            2.0 if self.difficulty == "normal"
            else 1.35 if self.difficulty == "easy"
            else 1.0
        )
        self.generator.minimum_ground_platform_gap = (
            80 if self.difficulty == "normal" else 75
        )
        ground_y = self.world_height - 80
        self.generator.max_platform_y = (
            ground_y - self.generator.minimum_ground_platform_gap
        )

        # Ramp difficulty across a difficulty's 1..MAX_LEVELS progression
        # (level_progress: 0.0 at level 1, 1.0 at level MAX_LEVELS), then
        # apply the player-selected difficulty as a further multiplier/offset.
        level_progress = (self.level_number - 1) / max(1, MAX_LEVELS - 1)
        if self.difficulty == "easy":
            self.generator.base_difficulty = 0.5 + level_progress * 1.0
        elif self.difficulty == "hard":
            self.generator.base_difficulty = 1.5 + level_progress * 2.0
        else:
            self.generator.base_difficulty = 0.8 + level_progress * 1.4

        if self.is_boss_level:
            # Boss arenas have the ground and four spaced stepping platforms.
            # The boss stays inside a clear central lane between the platforms.
            self.platforms = [self.ground]
            self.platforms.extend(self._create_boss_arena_platforms())
        else:
            self.platforms = self.generator.generate()
            self.platforms.insert(0, self.ground)

        # ==========================================
        # MOVING PLATFORMS
        # ==========================================

        self.moving_platforms = []

        self.generate_moving_platforms()
        # ==========================================
        # DEEP PITS
        # ==========================================

        self.pits = []
        self.generate_pits()

        # Regular levels need a safe final checkpoint approach. Boss arenas
        # have no finish marker, so preserve their symmetric side platforms.
        if not self.is_boss_level:
            self.finish_x = self._find_safe_finish_x()
        self._clear_final_approach_zone()

        # ==========================================
        # PLAYER
        # ==========================================

        self.player_start_x = 100
        self.player_start_y = self.ground.rect.top - 90 if self.is_boss_level else self.world_height - 160

        self.player = Player(
            self.player_start_x,
            self.player_start_y,
            character_type="fighter" if self.difficulty == "easy" else "default",
        )
        if self.is_boss_level:
            self.player.jump_strength = -17.0

        # ==========================================
        # COLLECTIBLES
        # ==========================================

        self.collectibles = []

        # Preserve the existing Normal/Hard collectible timing. Easy coins
        # are generated after enemies and checkpoints exist, so their paths
        # can be placed outside enemy patrol and checkpoint collision areas.
        if self.difficulty != "easy":
            self.generate_collectibles()

        # ==========================================
        # SCORE
        # ==========================================

        self.score = 0

        # ==========================================
        # CHECKPOINTS
        # ==========================================

        self.checkpoints = []

        self.current_checkpoint = None

        self.generate_checkpoints()

        # ==========================================
        # LOAD SAVED GAME
        # ==========================================

        load_game(self)

        # ==========================================
        # FINISH
        # ==========================================

        self.level_complete = False

        # finish_x was already made safe after pit generation.

        # ==========================================
        # UI
        # ==========================================

        self.font = self._load_uncial_font(32)

        self.big_font = self._load_uncial_font(64)

        # ==========================================
        # UI / WORLD ART ASSETS
        # ==========================================

        self.health_icon = self._load_ui_image(
            "health_icon.png"
        )
        self.star_icon = self._load_ui_image(
            "star_icon.png"
        )
        self.ui_frame = self._load_ui_image(
            "ui_frame.png"
        )
        self.score_frame = self._load_ui_image(
            "score_frame.png"
        )
        self.final_checkpoint_image = self._load_ui_image(
            "final_checkpoint.png"
        )

        # ==========================================
        # ENEMIES
        # ==========================================

        self.enemies = []
        self.projectiles = []
        self.generate_enemies()

        # ==========================================
        # OBSTACLES
        # ==========================================

        self.obstacles = []
        self.bushes = []

        self.generate_obstacles()
        self.generate_bushes()

        if self.difficulty == "easy":
            self.generate_collectibles()

        # ==========================================
        # ENEMY DAMAGE
        # ==========================================

        self.damage_cooldown = 0
        self.damage_cooldown_max = 60

        # Death screen effect
        self.death_flash_timer = 0
        self.death_flash_duration = 21

        self.particles = []

        self.npcs = [
            NPC(
                600,
                400,
                name="Snackland Guide",
                dialogue=[
                    "Welcome to Snackland!",
                    "Collect the stars and rescue your friends!",
                    "Good luck, Carrot!"
                ]
            ),

            NPC(
                1200,
                400,
                name="Chef Tomato",
                dialogue=[
                    "Hey Carrot!",
                    "The next area is dangerous.",
                    "Watch out for the enemies!"
                ]
            )
        ]

        self.dialogue = Dialogue(self.npcs[0].dialogue)
        self.current_npc = None

    def _draw_boss_arena_background(self, screen):
        """Draw a purpose-built backdrop for Easy boss encounters."""
        if self.boss_kind == "orc":
            top = (32, 25, 37)
            bottom = (102, 53, 43)
            moon = (227, 119, 78)
            ridge = (42, 33, 42)
        else:
            top = (13, 24, 52)
            bottom = (51, 39, 91)
            moon = (117, 221, 238)
            ridge = (20, 31, 59)

        height = screen.get_height()
        width = screen.get_width()
        band_height = 12
        for y in range(0, height, band_height):
            t = y / max(1, height - 1)
            color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            pygame.draw.rect(screen, color, (0, y, width, band_height))

        pygame.draw.circle(screen, moon, (width - 170, 170), 58)
        pygame.draw.polygon(screen, ridge, [(0, height - 240), (180, height - 370), (360, height - 240), (540, height - 345), (760, height - 245), (930, height - 360), (width, height - 230), (width, height), (0, height)])
        pillar_color = (58, 43, 47) if self.boss_kind == "orc" else (27, 45, 74)
        for px in (70, width - 120):
            pygame.draw.rect(screen, pillar_color, (px, height - 290, 48, 210))
            pygame.draw.rect(screen, pillar_color, (px - 12, height - 292, 72, 18))
            pygame.draw.rect(screen, pillar_color, (px - 8, height - 92, 64, 18))

    def _draw_boss_arena_platform(self, screen, platform):
        """Render a stone ledge matching the boss arena instead of grassy tiles."""
        rect = self.camera.apply(platform.rect)
        if self.boss_kind == "orc":
            body = (65, 48, 48)
            top = (166, 93, 67)
            seam = (91, 62, 58)
        else:
            body = (34, 42, 71)
            top = (84, 156, 169)
            seam = (48, 73, 103)

        pygame.draw.rect(screen, body, rect)
        pygame.draw.rect(screen, top, (rect.x, rect.y, rect.width, 7))
        pygame.draw.line(
            screen,
            seam,
            (rect.left, rect.bottom - 1),
            (rect.right, rect.bottom - 1),
            2,
        )
        segment = 48
        for x in range(rect.left + segment, rect.right, segment):
            pygame.draw.line(screen, seam, (x, rect.y + 7), (x, rect.bottom), 2)

    def _draw_boss_arena_ground(self, screen):
        """Render a continuous stone arena floor instead of platforming grass."""
        ground_rect = self.camera.apply(self.ground.rect)
        if self.boss_kind == "orc":
            soil = (65, 48, 48)
            top = (166, 93, 67)
            seam = (91, 62, 58)
        else:
            soil = (34, 42, 71)
            top = (84, 156, 169)
            seam = (48, 73, 103)
        pygame.draw.rect(screen, soil, ground_rect)
        pygame.draw.rect(screen, top, (ground_rect.x, ground_rect.y, ground_rect.width, 14))
        start_x = (ground_rect.left // 70) * 70
        for x in range(start_x, ground_rect.right, 70):
            pygame.draw.line(screen, seam, (x, ground_rect.y + 14), (x, ground_rect.bottom), 2)
            pygame.draw.line(screen, seam, (x, ground_rect.y + 48), (min(x + 70, ground_rect.right), ground_rect.y + 48), 2)

    def _load_ui_image(self, filename):
        path = os.path.join(
            "assets",
            "ui",
            filename
        )

        try:
            return pygame.image.load(
                path
            ).convert_alpha()
        except (pygame.error, FileNotFoundError):
            return None

    def _load_uncial_font(self, size):
        """Load Uncial Antiqua for the HUD, with a safe fallback."""
        font_path = os.path.join(
            "assets",
            "fonts",
            "UncialAntiqua-Regular.ttf"
        )

        try:
            if os.path.exists(font_path):
                return pygame.font.Font(font_path, size)

            # Also allow a Windows-installed copy of the font.
            return pygame.font.SysFont("Uncial Antiqua", size)
        except (pygame.error, OSError):
            return pygame.font.Font(None, size)

    def _create_boss_arena_platforms(self):
        """Create four spaced stepping platforms around the clear boss lane."""
        floor_top = self.ground.rect.top
        platform_height = 24
        # Each side has a lower outer ledge and a higher inner ledge.
        # Their 160px edge-to-edge gap is deliberately demanding when
        # climbing 140px. The existing 15px landing tolerance makes it possible
        # with a carefully timed jump; jump strength and gravity stay unchanged.
        # The inner edges leave a clear 350px central boss lane.
        left_layout = [
            (20, 100, 80),
            (260, 240, 90),
        ]
        platforms = []
        for x, height_above_floor, width in left_layout:
            y = floor_top - height_above_floor
            platforms.append(Platform(x, y, width, platform_height))
            platforms.append(
                Platform(self.width - x - width, y, width, platform_height)
            )
        return platforms

    def _clear_final_approach_zone(self):
        """Keep the last 600 px before a regular level's finish clear."""
        if self.is_boss_level:
            self.final_approach_start = self.width
            return

        approach_distance = 600
        approach_start = max(0, int(self.finish_x) - approach_distance)

        # Remove every generated static platform that enters the reserved zone.
        # The ground is intentionally kept because the final checkpoint must
        # always stand on solid ground.
        self.platforms = [
            platform
            for platform in self.platforms
            if platform is self.ground
            or platform.rect.right <= approach_start
        ]

        # Remove pits that touch the reserved zone.
        self.pits = [
            pit
            for pit in self.pits
            if pit.right <= approach_start
        ]

        # Remove moving platforms that would enter the reserved zone.
        self.moving_platforms = [
            platform
            for platform in self.moving_platforms
            if platform.rect.right <= approach_start
        ]

        # Keep the final marker comfortably inside the clear area.
        self.final_approach_start = approach_start


    def _find_safe_finish_x(self):
        """Find a finish position on the ground with no platform overlapping the
        final checkpoint's visible area."""
        target = int(self.finish_x)

        # The final checkpoint is drawn at 120x120 and its bottom sits on
        # the ground. Keep a little extra clearance so nearby platforms
        # cannot visually/collision-wise overlap the marker.
        marker_half_width = 70
        marker_height = 125
        ground_top = self.ground.rect.top

        def safe(x):
            if not (marker_half_width + 30 <= x <= self.width - marker_half_width - 30):
                return False

            marker_rect = pygame.Rect(
                int(x - marker_half_width),
                int(ground_top - marker_height),
                marker_half_width * 2,
                marker_height,
            )

            # Never place the final checkpoint over a pit or too close to
            # its edge.
            for pit in self.pits:
                if marker_rect.colliderect(
                    pygame.Rect(pit.left - 20, 0, pit.width + 40, self.world_height)
                ):
                    return False

            # Do not allow any generated static platform to overlap the
            # final checkpoint. The ground itself is intentionally ignored.
            for platform in self.platforms:
                if platform is self.ground:
                    continue
                if marker_rect.colliderect(platform.rect):
                    return False

            return True

        if safe(target):
            return target

        # Search around the intended finish point first.
        for distance in range(25, 3001, 25):
            for candidate in (target - distance, target + distance):
                if 100 <= candidate <= self.width - 100 and safe(candidate):
                    return candidate

        # If the nearby area is crowded, scan the whole level for a valid
        # ground position instead of returning a position that overlaps a
        # platform.
        for candidate in range(100, self.width - 100, 25):
            if safe(candidate):
                return candidate

        # Extremely unlikely fallback: keep the original target clamped.
        return max(100, min(self.width - 100, target))

    # ==============================================
    # GENERATE COLLECTIBLES
    # ==============================================

    def _item_center_xs(self, exclude=None):
        xs = []
        for group in (
            getattr(self, "collectibles", []),
            getattr(self, "checkpoints", []),
            getattr(self, "enemies", []),
            getattr(self, "obstacles", []),
            getattr(self, "bushes", []),
        ):
            for item in group:
                if item is exclude:
                    continue
                rect = getattr(item, "rect", None)
                if rect is not None:
                    xs.append(rect.centerx)
        return xs

    def _item_position_clear(self, center_x, min_spacing=ITEM_MIN_SPACING, exclude=None):
        return all(abs(center_x - other_x) >= min_spacing for other_x in self._item_center_xs(exclude))

    def _load_easy_coin_frames(self):
        global _EASY_COIN_FRAME_CACHE
        if _EASY_COIN_FRAME_CACHE is not None:
            return _EASY_COIN_FRAME_CACHE

        asset_root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets",
            "coins",
            "easy",
        )
        frames = []
        for frame_number in range(21, 31):
            path = os.path.join(asset_root, f"Gold_{frame_number}.png")
            try:
                image = pygame.image.load(path)
            except (pygame.error, FileNotFoundError):
                continue

            target_height = EASY_COIN_DRAW_HEIGHT
            target_width = max(
                1,
                round(image.get_width() * target_height / image.get_height()),
            )
            frames.append(
                pygame.transform.smoothscale(image, (target_width, target_height))
            )

        _EASY_COIN_FRAME_CACHE = tuple(frames)
        return _EASY_COIN_FRAME_CACHE

    def _easy_coin_group_is_clear(self, positions, size):
        """Return False if any coin overlaps an enemy's patrol corridor or a checkpoint/hazard."""
        patrol_rects = []
        for enemy in getattr(self, "enemies", []):
            left = int(getattr(enemy, "left_limit", enemy.rect.left))
            right = int(getattr(enemy, "right_limit", enemy.rect.right))
            patrol_rects.append(
                pygame.Rect(
                    left,
                    enemy.rect.top - 8,
                    max(1, right - left),
                    enemy.rect.height + 16,
                )
            )

        static_hazards = []
        for group_name in ("checkpoints", "obstacles", "bushes"):
            for item in getattr(self, group_name, []):
                rect = getattr(item, "rect", None)
                if rect is not None:
                    static_hazards.append(rect)

        for x, y in positions:
            coin_rect = pygame.Rect(x, y, size, size)
            if any(coin_rect.colliderect(rect) for rect in patrol_rects):
                return False
            if any(coin_rect.colliderect(rect) for rect in static_hazards):
                return False
        return True

    def _generate_easy_collectibles(self):
        """Generate alternating rows and semi-circle coin trails for Easy only."""
        self.collectibles.clear()
        frames = self._load_easy_coin_frames()
        final_start = getattr(self, "final_approach_start", self.width)
        size = EASY_COIN_SIZE
        base_y_offset = size + EASY_COIN_LINE_OFFSET
        placed_groups = 0

        eligible_platforms = [
            platform
            for platform in self.platforms[1:]
            if (
                platform.rect.width >= size * 4
                and platform.rect.left >= EASY_ENEMY_START_BUFFER - 20
                and platform.rect.right < final_start - 35
            )
        ]

        for platform in eligible_platforms:
            left = platform.rect.left + 24
            right = platform.rect.right - 24
            span = right - left
            if span < size * 3:
                continue

            coin_count = max(4, min(7, int(span // EASY_COIN_SPACING) + 1))
            centers = [
                round(left + (span * index / (coin_count - 1)))
                for index in range(coin_count)
            ]
            is_arc = placed_groups % 2 == 1
            base_y = platform.rect.top - base_y_offset

            positions = []
            for index, center_x in enumerate(centers):
                arc_raise = (
                    round(math.sin(math.pi * index / (coin_count - 1)) * EASY_COIN_ARC_HEIGHT)
                    if is_arc else 0
                )
                positions.append((center_x - size // 2, base_y - arc_raise))

            # Keep the pattern intact by raising the whole row/arc if needed.
            # If a rare layout still cannot clear collision areas, skip that
            # platform instead of placing a coin where an enemy can reach it.
            safe_positions = None
            for raise_by in range(0, EASY_COIN_MAX_RAISE + 1, 12):
                candidate = [(x, y - raise_by) for x, y in positions]
                if self._easy_coin_group_is_clear(candidate, size):
                    safe_positions = candidate
                    break

            if safe_positions is None:
                continue

            for x, y in safe_positions:
                self.collectibles.append(
                    Collectible(
                        x,
                        y,
                        size=size,
                        value=10,
                        animation_frames=frames,
                    )
                )
            placed_groups += 1

    def generate_collectibles(self):
        self.collectibles.clear()
        if getattr(self, "is_boss_level", False):
            return

        if self.difficulty == "easy":
            self._generate_easy_collectibles()
            return

        final_start = getattr(self, "final_approach_start", self.width)

        for platform in self.platforms[1:]:
            if platform.rect.centerx >= final_start - 70:
                continue
            if random.random() > 0.65:
                continue
            margin = 18
            size = 24
            if platform.rect.width <= margin * 2 + size:
                continue
            for _attempt in range(20):
                x = random.randint(platform.rect.left + margin, platform.rect.right - margin - size)
                if not self._item_position_clear(x + size // 2, 100):
                    continue
                self.collectibles.append(Collectible(x, platform.rect.top - 30))
                break

    def generate_checkpoints(self):
        self.checkpoints.clear()
        if getattr(self, "is_boss_level", False):
            return
        # Fewer checkpoints per level: one every 3000px of world width
        # instead of every 1800px.
        checkpoint_spacing = 3000
        next_checkpoint_x = checkpoint_spacing
        for platform in self.platforms[1:]:
            if platform.rect.centerx < next_checkpoint_x:
                continue
            checkpoint_x = platform.rect.centerx
            if not self._item_position_clear(checkpoint_x, 130):
                continue
            self.checkpoints.append(Checkpoint(checkpoint_x, platform.rect.top, len(self.checkpoints)))
            next_checkpoint_x = checkpoint_x + checkpoint_spacing

    def generate_pits(self):

        self.pits.clear()
        if getattr(self, "is_boss_level", False):
            return

        # Need at least two platforms
        if len(self.platforms) < 3:
            return

        # Start checking after the first few platforms
        for i in range(1, len(self.platforms) - 1):

            current_platform = self.platforms[i]
            next_platform = self.platforms[i + 1]

            # ======================================
            # GAP BETWEEN PLATFORMS
            # ======================================

            gap_start = current_platform.rect.right
            gap_end = next_platform.rect.left

            gap_width = gap_end - gap_start

            # ======================================
            # GAP TOO SMALL
            # ======================================

            if gap_width < 120:
                continue

            # ======================================
            # DON'T MAKE EVERY GAP A PIT
            # ======================================

            progress = (
                    current_platform.rect.centerx
                    / self.width
            )

            if progress < 0.25:

                pit_chance = 0.25

            elif progress < 0.60:

                pit_chance = 0.40

            else:

                pit_chance = 0.55

            if random.random() > pit_chance:
                continue

            # ======================================
            # KEEP SAFE LANDING AREA
            # ======================================

            safe_margin = 25

            pit_left = gap_start + safe_margin
            pit_right = gap_end - safe_margin

            pit_width = (
                    pit_right - pit_left
            )

            # ======================================
            # PIT TOO SMALL
            # ======================================

            if pit_width < 80:
                continue

            # ======================================
            # LIMIT PIT SIZE
            # ======================================

            # ======================================
            # PIT DIFFICULTY
            # ======================================

            if progress < 0.35:

                pit_limit = random.randint(
                    140,
                    180
                )

            elif progress < 0.70:

                pit_limit = random.randint(
                    160,
                    210
                )

            else:

                pit_limit = random.randint(
                    180,
                    230
                )

            pit_width = min(
                pit_width,
                pit_limit
            )

            # Center the pit inside the gap

            pit_center = (
                    (pit_left + pit_right) // 2
            )

            pit_left = (
                    pit_center
                    - pit_width // 2
            )

            # ======================================
            # CREATE PIT
            # ======================================

            # Make pits extend slightly below the visible ground.
            pit = pygame.Rect(
                pit_left,
                self.world_height - 80,
                pit_width,
                100
            )

            self.pits.append(pit)

    # ==============================================
    # GENERATE MOVING PLATFORMS
    # ==============================================

    def generate_moving_platforms(self):

        self.moving_platforms.clear()
        if getattr(self, "is_boss_level", False):
            return

        # ==========================================
        # FIXED POSITIONS FOR NOW
        # ==========================================
        # Y values are authored relative to the old fixed-height world
        # (ground at HEIGHT - 80); shift them down by the extra vertical
        # room the world now has so they still sit near the factory
        # floor instead of floating high in the new tall world.
        vertical_offset = self.world_height - HEIGHT

        positions = [
            (1800, 420 + vertical_offset, "horizontal"),
            (3600, 350 + vertical_offset, "vertical"),
            (5400, 430 + vertical_offset, "horizontal"),
            (7200, 360 + vertical_offset, "vertical"),
            (8600, 420 + vertical_offset, "horizontal")
        ]

        for x, y, movement_type in positions:

            if self.difficulty == "normal":
                # Match the normal-difficulty platform size pass.
                # Moving platforms must also start at least 80px above the ground.
                y = min(y, self.ground.rect.top - 80)
                platform_width = 280
                platform_height = 40
            else:
                platform_width = 140
                platform_height = 20

            platform = MovingPlatform(
                x,
                y,
                platform_width,
                platform_height,
                movement_type=movement_type,
                movement_distance=120,
                movement_speed=1.0
            )

            self.moving_platforms.append(
                platform
            )


    # ==============================================
    # RESPAWN
    # ==============================================

    def respawn_player(self):

        # Clear any in-flight bullets/bombs so the player doesn't get hit
        # again the instant they respawn.
        self.projectiles.clear()

        # ==========================================
        # RED DEATH EFFECT
        # ==========================================

        self.death_flash_timer = (
            self.death_flash_duration
        )

        # Death particles
        self.create_particles(
            self.player.rect.centerx,
            self.player.rect.centery,
            (255, 100, 50),
            count=20
        )

        # ==========================================
        # RESPAWN POSITION
        # ==========================================

        if self.current_checkpoint is not None:

            self.player.rect.x = (
                self.current_checkpoint.respawn_x
            )

            self.player.rect.y = (
                self.current_checkpoint.respawn_y
            )

        else:

            self.player.rect.x = (
                self.player_start_x
            )

            self.player.rect.y = (
                self.player_start_y
            )

        # ==========================================
        # RESET PHYSICS
        # ==========================================

        self.player.velocity_y = 0
        self.player.on_ground = False
        self.player.current_platform = None

        # ==========================================
        # RESPAWN EFFECT
        # ==========================================

        self.player.start_respawn_effect()

    # ==============================================
    # CHECK DEATH
    # ==============================================

    def check_player_death(self):

        if self.player.death_timer > 0 or self.player.respawn_timer > 0:
            return

        # --------------------------------------
        # PIT DEATH
        # --------------------------------------
        # Let the player fall all the way to the bottom of the pit.
        # When the feet reach the bottom edge of the visible world,
        # freeze the player there and play the complete DEAD animation
        # before respawning at the checkpoint.
        player_center_x = self.player.rect.centerx
        inside_pit = False

        for pit in self.pits:
            if pit.left <= player_center_x <= pit.right:
                inside_pit = True
                break

        if inside_pit and self.player.rect.bottom >= self.world_height - 20:

            # Keep the character visible while the death animation plays.
            self.player.rect.bottom = self.world_height - 20
            self.player.velocity_y = 0
            self.player.on_ground = False
            self.player.current_platform = None

            if self.sound_manager is not None:
                self.sound_manager.play("death")

            self.player.start_death_animation()

            self.create_particles(
                self.player.rect.centerx,
                self.player.rect.bottom - 10,
                (255, 100, 50),
                count=20
            )
            return

        # --------------------------------------
        # FALLBACK WORLD DEATH
        # --------------------------------------

        if self.player.rect.top > self.world_height + 300:

            if self.sound_manager is not None:
                self.sound_manager.play("death")

            self.player.start_death_animation()

            self.create_particles(
                self.player.rect.centerx,
                self.player.rect.centery,
                (255, 100, 50),
                count=20
            )

    # ==============================================
    # CHECK LEVEL COMPLETION
    # ==============================================

    def check_level_completion(self):

        if self.is_boss_level:
            if (
                self.boss is not None
                and not self.boss.alive
                and self.boss.finished_dying
                and not self.level_complete
            ):
                self.level_complete = True
                self._compute_star_breakdown()
            return

        if self.player.rect.centerx >= self.finish_x:
            self.level_complete = True
            self._compute_star_breakdown()

    # ==============================================
    # STAR BREAKDOWN
    # ==============================================
    # Works out exactly which quest conditions were met so the UI can show
    # the player *why* they got the stars they got, instead of just a
    # bare 1-3 star number. There are always exactly 3 quests:
    #   - Completed the level                     (always required/true on win)
    #   - 2 quests randomly chosen (per level, via self.active_quests) from:
    #       - Killed every enemy in the level
    #       - Finished without getting hit by an enemy (bushes/rocks are fine)
    #       - Collected every coin in the level
    #       - Finished within the level's time limit
    #
    # Each of the 3 quests is worth exactly 1 star, so stars always range
    # from 1 (just completed) to 3 (completed + both chosen quests).

    def _compute_star_breakdown(self):

        total_enemies = len(self.enemies)
        enemies_killed = sum(1 for e in self.enemies if not e.alive)
        killed_all_enemies = enemies_killed >= total_enemies

        total_coins = len(self.collectibles)
        coins_collected = sum(1 for c in self.collectibles if c.collected)
        collected_all_coins = coins_collected >= total_coins

        no_enemy_hits = not self.enemy_hit_taken
        within_time_limit = self.elapsed_seconds <= self.time_limit_seconds

        # All 4 possible objective results, keyed the same as
        # QUEST_DEFINITIONS, along with a human-readable label and met flag.
        results = {
            "killed_all_enemies": (
                killed_all_enemies,
                f"Kill all enemies ({enemies_killed}/{total_enemies})",
            ),
            "no_enemy_hits": (
                no_enemy_hits,
                "No enemy hits (bushes/rocks OK)",
            ),
            "collected_all_coins": (
                collected_all_coins,
                f"Collect all coins ({coins_collected}/{total_coins})",
            ),
            "within_time_limit": (
                within_time_limit,
                f"Finish within {self.time_limit_seconds}s",
            ),
        }

        # Only the 2 quests chosen for this level count toward stars.
        quest_items = [("Completed the level", True)]
        stars = 1
        for key in self.active_quests:
            met, label = results[key]
            quest_items.append((label, met))
            if met:
                stars += 1

        self.star_rating = stars
        self.star_breakdown = {
            "completed": True,
            "killed_all_enemies": killed_all_enemies,
            "enemies_killed": enemies_killed,
            "total_enemies": total_enemies,
            "no_enemy_hits": no_enemy_hits,
            "collected_all_coins": collected_all_coins,
            "coins_collected": coins_collected,
            "total_coins": total_coins,
            "within_time_limit": within_time_limit,
            "elapsed_seconds": self.elapsed_seconds,
            "time_limit_seconds": self.time_limit_seconds,
            "active_quests": list(self.active_quests),
            "quest_items": quest_items,
        }

    # ==============================================
    # UPDATE
    # ==============================================

    def update(self):

        self.elapsed_seconds = max(0.0, (pygame.time.get_ticks() - self.start_time) / 1000.0)

        # Don't continue normal gameplay
        # after level completion

        if self.level_complete:
            return

        # ------------------------------------------
        # PLAYER DEATH / RESPAWN SEQUENCE
        # ------------------------------------------
        # Keep the player frozen while the complete DEAD animation plays.
        # Only after the animation finishes do we move the player to the
        # checkpoint/start position and begin the short respawn delay.
        if self.player.death_timer > 0:
            self.player.update([])

            if self.player.death_timer == 0:
                if self.fail_requested:
                    self.player.respawn_timer = 0
                    self.update_particles()
                    self.camera.update(self.player)
                    return
                self.player.health = 3
                self.respawn_player()

            self.update_particles()
            self.camera.update(self.player)
            return

        # Keep gameplay paused during the short respawn delay.
        if self.player.respawn_timer > 0:
            self.player.update([])
            self.update_particles()
            self.camera.update(self.player)
            return

        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

        if self.death_flash_timer > 0:
            self.death_flash_timer -= 1

        # ------------------------------------------
        # MOVING PLATFORMS
        # ------------------------------------------

        for platform in self.moving_platforms:
            platform.update()

        # ------------------------------------------
        # PLAYER
        # ------------------------------------------

        collision_platforms = (
                self.platforms
                + self.moving_platforms
        )

        # ------------------------------------------
        # REMOVE GROUND COLLISION INSIDE PITS
        # ------------------------------------------

        if self.player.rect.bottom >= self.world_height - 100:

            collision_platforms = []

            for platform in self.platforms:

                # Never remove normal platforms

                if platform is not self.ground:
                    collision_platforms.append(
                        platform
                    )

                    continue

                # Check whether player's center
                # is inside a pit

                player_center_x = (
                    self.player.rect.centerx
                )

                inside_pit = False

                for pit in self.pits:

                    if pit.left <= player_center_x <= pit.right:
                        inside_pit = True
                        break

                if not inside_pit:
                    collision_platforms.append(
                        platform
                    )

            # --------------------------------------
            # KEEP MOVING PLATFORMS
            # --------------------------------------

            collision_platforms.extend(
                self.moving_platforms
            )


        # ------------------------------------------
        # PLAYER
        # ------------------------------------------

        if self.is_boss_level:
            self.player.update(collision_platforms, world_width=self.width)
        else:
            self.player.update(collision_platforms)

        if self.is_boss_level:
            # Keep the player inside the dedicated arena; regular levels keep
            # their existing world-bound behavior unchanged.
            self.player.rect.left = max(0, self.player.rect.left)
            self.player.rect.right = min(self.width, self.player.rect.right)

        # ------------------------------------------
        # ROCK COLLISION / DAMAGE
        # ------------------------------------------
        # Rocks are ground hazards only. They are never part of the
        # platform collision list, so the player cannot stand on them.

        for obstacle in self.obstacles:

            if not obstacle.active or not obstacle.check_collision(self.player):
                continue

            if self.damage_cooldown > 0:
                continue

            self.player.health = max(0, self.player.health - 1)
            self.damage_taken = True
            self.damage_cooldown = self.damage_cooldown_max
            self.player.take_damage()

            if self.player.rect.centerx < obstacle.rect.centerx:
                self.player.rect.right = obstacle.rect.left
            else:
                self.player.rect.left = obstacle.rect.right

            self.player.velocity_y = -5

        # ------------------------------------------
        # BUSH EFFECTS
        # ------------------------------------------
        self.update_bush_effects()
        # ------------------------------------------
        # DEATH
        # ------------------------------------------

        self.check_player_death()

        # ------------------------------------------
        # HEALTH DEATH
        # ------------------------------------------

        # ------------------------------------------
        # HEALTH DEATH
        # ------------------------------------------


        # ------------------------------------------
        # LEVEL COMPLETE
        # ------------------------------------------

        self.check_level_completion()

        # ------------------------------------------
        # CAMERA
        # ------------------------------------------

        self.camera.update(
            self.player
        )

        # ------------------------------------------
        # COLLECTIBLES
        # ------------------------------------------

        for collectible in self.collectibles:
            if not collectible.collected and collectible.rect.colliderect(self.player.rect):

                # Save position before collecting
                particle_x = collectible.rect.centerx
                particle_y = collectible.rect.centery

                # Collect the item
                collectible.collect()
                self.score += collectible.value
                self.new_collectibles += 1

                # Collect sound
                if self.sound_manager is not None:
                    self.sound_manager.play("collect")

                # Golden pickup particles
                self.create_particles(
                    particle_x,
                    particle_y,
                    (255, 215, 0),
                    count=10
                )

        # ------------------------------------------
        # CHECKPOINTS
        # ------------------------------------------

        for checkpoint in self.checkpoints:

            was_activated = checkpoint.activated

            checkpoint.update(
                self.player
            )

            if checkpoint.activated:

                self.current_checkpoint = checkpoint

                # ----------------------------------
                # NEW CHECKPOINT ACTIVATED
                # ----------------------------------

                if not was_activated:

                    # Save progress
                    save_game(self)

                    # Play checkpoint sound
                    if self.sound_manager is not None:
                        self.sound_manager.play(
                            "checkpoint"
                        )

                    # Checkpoint activation particles
                    self.create_particles(
                        checkpoint.rect.centerx,
                        checkpoint.rect.centery,
                        (80, 255, 120),
                        count=15
                    )


        # ------------------------------------------
        # ENEMIES
        # ------------------------------------------

        player_cx = self.player.rect.centerx
        for enemy in self.enemies:
            # The world is 100,000 px wide: skip enemies far from the player.
            if abs(enemy.rect.centerx - player_cx) > ENTITY_ACTIVE_RANGE:
                continue
            enemy.update(self.player, self)

            pending = enemy.pending_projectile
            if pending is not None:
                enemy.pending_projectile = None
                self.projectiles.append(
                    Projectile(
                        pending["x"],
                        pending["y"],
                        kind=pending["kind"],
                        direction=pending.get("direction", 1),
                        damage=1
                    )
                )

            pending_attack = enemy.pending_attack
            if pending_attack is not None:
                enemy.pending_attack = None
                self.handle_enemy_attack(enemy, pending_attack)

        self.update_projectiles()
        self.handle_projectile_collisions()

        # ------------------------------------------
        # PLAYER ATTACK
        # ------------------------------------------

        self.handle_player_attack()

        # Enemy bodies are non-solid: the player can pass through them.
        # Player damage comes only from an enemy's attack animation/effect.
        self.update_particles()
        # ------------------------------------------
        # HEALTH DEATH (enemy / bush / rock)
        # ------------------------------------------
        # Same treatment as a pit fall: play the death animation, then
        # respawn at the last checkpoint. fail_requested is intentionally
        # left False here so the update() death-sequence branch below
        # routes into respawn_player() instead of the Fail screen.

        if self.player.health <= 0 and self.player.death_timer == 0 and self.player.respawn_timer == 0:

            if self.sound_manager is not None:
                self.sound_manager.play(
                    "death"
                )

            # Do NOT teleport immediately.
            # Play the full death animation first.
            self.player.start_death_animation()



    # ==============================================
    # DRAW
    # ==============================================

    def draw(self, screen):

        # ==========================================
        # BACKGROUND
        # ==========================================

        if self.is_boss_level:
            self._draw_boss_arena_background(screen)
        elif self.background_image is not None:
            if self.difficulty == "normal":
                # Subtle far-background parallax so the vertical camera
                # doesn't make the backdrop feel like a static sticker.
                parallax = 0.06
                offset_x = -int(self.camera.x * parallax) % max(1, WIDTH)
                offset_y = -int(self.camera.y * parallax)
                offset_y = max(-40, min(40, offset_y))
                screen.blit(self.background_image, (offset_x - WIDTH, offset_y))
                screen.blit(self.background_image, (offset_x, offset_y))
            else:
                screen.blit(
                    self.background_image,
                    (0, 0)
                )

        # ==========================================
        # INDUSTRIAL BACKGROUND STRUCTURES (normal only)
        # ==========================================

        if self.difficulty == "normal":
            draw_industrial_background(
                screen,
                self.camera,
                self.width,
                self.ground.rect.top
            )

        # ==========================================
        # GROUND
        # ==========================================

        if self.is_boss_level:
            self._draw_boss_arena_ground(screen)
        elif self.difficulty == "normal":
            draw_industrial_ground(
                screen,
                self.camera,
                self.ground.rect,
                seed=1
            )
        elif self.difficulty == "easy":
            draw_easy_ground(screen, self.camera, self.ground.rect)
        else:
            ground_rect = self.camera.apply(
                self.ground.rect
            )

            pygame.draw.rect(
                screen,
                (80, 180, 80),
                ground_rect
            )

            soil_rect = pygame.Rect(
                ground_rect.x,
                ground_rect.y + 8,
                ground_rect.width,
                ground_rect.height - 8
            )

            pygame.draw.rect(
                screen,
                (69, 48, 28),
                soil_rect
            )

            pygame.draw.rect(
                screen,
                (15, 66, 19),
                (
                    ground_rect.x,
                    ground_rect.y,
                    ground_rect.width,
                    8
                )
            )

        # ==========================================
        # PLATFORMS
        # ==========================================

        for index, platform in enumerate(self.platforms):

            if platform is self.ground:
                continue

            if self.difficulty == "normal":
                draw_industrial_platform(
                    screen,
                    self.camera,
                    platform.rect,
                    seed=index
                )
                continue

            if self.is_boss_level:
                self._draw_boss_arena_platform(screen, platform)
                continue

            if self.difficulty == "easy":
                draw_easy_platform(
                    screen,
                    self.camera,
                    platform.rect,
                    variant=index,
                )
                continue

            camera_rect = self.camera.apply(
                platform.rect
            )

            pygame.draw.rect(
                screen,
                (69, 48, 28),
                camera_rect
            )

            pygame.draw.rect(
                screen,
                (15, 66, 19),
                (
                    camera_rect.x,
                    camera_rect.y,
                    camera_rect.width,
                    5
                )
            )
        # ==========================================
        # OBSTACLES
        # ==========================================

        for obstacle in self.obstacles:
            obstacle.draw(
                screen,
                self.camera
            )

        # ==========================================
        # BUSHES
        # ==========================================

        for bush in self.bushes:
            bush.draw(screen, self.camera)

        # ==========================================
        # MOVING PLATFORMS
        # ==========================================

        for index, platform in enumerate(self.moving_platforms):

            if self.difficulty == "normal":
                draw_industrial_moving_platform(
                    screen,
                    self.camera,
                    platform.rect,
                    seed=index
                )
            elif self.difficulty == "easy":
                draw_easy_platform(
                    screen,
                    self.camera,
                    platform.rect,
                    variant=index,
                    moving=True,
                )
            else:
                platform.draw(
                    screen,
                    self.camera
                )
        # ==========================================
        # DEEP PITS
        # ==========================================

        for pit in self.pits:

            pit_rect = self.camera.apply(
                pit
            )

            if self.difficulty == "normal":
                draw_industrial_pit(
                    screen,
                    self.camera,
                    pit,
                    self.ground.rect.top
                )
            else:
                # Dark empty area

                pygame.draw.rect(
                    screen,
                    (20, 20, 20),
                    pit_rect
                )

            # Bottom of the pit. This gives the player a visible
            # surface to reach before the DEAD animation starts.
            pit_floor_height = 14
            pit_floor_world_rect = pygame.Rect(
                pit.left,
                self.world_height - 20 - pit_floor_height,
                pit.width,
                pit_floor_height
            )
            pit_floor_rect = self.camera.apply(pit_floor_world_rect)
            pygame.draw.rect(
                screen,
                (75, 50, 35),
                pit_floor_rect
            )
            pygame.draw.line(
                screen,
                (110, 75, 45),
                (pit_floor_rect.left, pit_floor_rect.top),
                (pit_floor_rect.right, pit_floor_rect.top),
                3
            )

            # Small warning edge

            pygame.draw.line(
                screen,
                (180, 60, 40),
                (
                    pit_rect.left,
                    pit_rect.top
                ),
                (
                    pit_rect.right,
                    pit_rect.top
                ),
                5
            )


        # ==========================================
        # CHECKPOINTS
        # ==========================================

        for checkpoint in self.checkpoints:

            checkpoint.draw(
                screen,
                self.camera
            )

        # ==========================================
        # COLLECTIBLES
        # ==========================================

        for collectible in self.collectibles:
            if not (self.camera.x - DRAW_MARGIN <= collectible.rect.centerx
                    <= self.camera.x + screen.get_width() + DRAW_MARGIN):
                continue

            collectible.draw(
                screen,
                self.camera
            )

        # ==========================================
        # FINAL CHECKPOINT / FINISH
        # ==========================================

        # The final marker is omitted from boss arenas; defeating the boss completes the level.
        finish_screen_x = self.finish_x - self.camera.x
        finish_screen_ground_top = self.ground.rect.top - self.camera.y

        if not self.is_boss_level and self.final_checkpoint_image is not None:
            final_image = pygame.transform.scale(
                self.final_checkpoint_image,
                (120, 120)
            )

            final_rect = final_image.get_rect()
            final_rect.midbottom = (
                int(finish_screen_x),
                int(finish_screen_ground_top)
            )

            screen.blit(final_image, final_rect)
        elif not self.is_boss_level:
            pygame.draw.rect(
                screen,
                (80, 80, 80),
                (
                    int(finish_screen_x),
                    int(finish_screen_ground_top) - 100,
                    6,
                    100
                )
            )

        # ==========================================
        # PLAYER
        # ==========================================

        player_rect = self.camera.apply(
            self.player.rect
        )

        self.player.draw(
            screen,
            player_rect
        )
        # ==========================================
        # POLISHED IMAGE-BASED HUD
        # ==========================================

        hud_font = self._load_uncial_font(24)
        small_font = self._load_uncial_font(19)
        title_font = self._load_uncial_font(25)

        def draw_panel(rect):
            # Use the supplied pixel-art rectangle as the UI frame.
            if self.ui_frame is not None:
                frame = pygame.transform.scale(
                    self.ui_frame,
                    rect.size
                )
                screen.blit(
                    frame,
                    rect.topleft
                )
            else:
                pygame.draw.rect(
                    screen,
                    (20, 25, 30),
                    rect,
                    border_radius=6
                )
                pygame.draw.rect(
                    screen,
                    (255, 255, 255),
                    rect,
                    2,
                    border_radius=6
                )

        def draw_shadow_text(text, font, center):
            shadow = font.render(
                text,
                True,
                (0, 0, 0)
            )
            surface = font.render(
                text,
                True,
                (40, 40, 40)
            )
            shadow_rect = shadow.get_rect(
                center=(center[0] + 2, center[1] + 2)
            )
            text_rect = surface.get_rect(
                center=center
            )
            screen.blit(shadow, shadow_rect)
            screen.blit(surface, text_rect)

        # ------------------------------------------
        # HEALTH — TOP LEFT
        # ------------------------------------------

        # Health is represented only by heart icons. The numeric health
        # count and the separate checkpoint HUD icon have been removed.
        health_panel = pygame.Rect(
            12,
            10,
            145,
            62
        )

        draw_panel(health_panel)

        if self.health_icon is not None:
            heart_size = 30
            heart_gap = 8
            total_width = heart_size * 3 + heart_gap * 2
            start_x = health_panel.x + (health_panel.width - total_width) // 2
            icon_y = health_panel.y + (health_panel.height - heart_size) // 2

            for i in range(3):
                icon = pygame.transform.scale(
                    self.health_icon,
                    (heart_size, heart_size)
                )

                if i >= self.player.health:
                    icon.set_alpha(55)

                screen.blit(
                    icon,
                    (start_x + i * (heart_size + heart_gap), icon_y)
                )

        # ------------------------------------------
        # LEVEL — TOP CENTER
        # ------------------------------------------

        level_panel = pygame.Rect(
            screen.get_width() // 2 - 185,
            10,
            370,
            62
        )

        draw_panel(level_panel)

        level_title = (
            f"LEVEL {self.level_number}  •  "
            f"{self.level_name}"
        )

        level_surface = title_font.render(
            level_title,
            True,
            (40, 40, 40)
        )

        screen.blit(
            level_surface,
            level_surface.get_rect(
                center=(
                    level_panel.centerx,
                    level_panel.y + 22
                )
            )
        )

        difficulty_surface = small_font.render(
            f"Difficulty: {self.level_difficulty}",
            True,
            (80, 80, 80)
        )

        screen.blit(
            difficulty_surface,
            difficulty_surface.get_rect(
                center=(
                    level_panel.centerx,
                    level_panel.y + 45
                )
            )
        )

        # ------------------------------------------
        # SCORE — TOP RIGHT
        # ------------------------------------------

        score_panel = pygame.Rect(
            screen.get_width() - 205,
            10,
            193,
            62
        )

        # Use the dedicated rectangle artwork for the score only.
        if self.score_frame is not None:
            score_frame = pygame.transform.scale(
                self.score_frame,
                score_panel.size
            )
            screen.blit(score_frame, score_panel.topleft)
        else:
            draw_panel(score_panel)

        # No star icon: score is text-only.
        score_surface = hud_font.render(
            str(self.score),
            True,
            (40, 40, 40)
        )

        screen.blit(
            score_surface,
            score_surface.get_rect(
                center=score_panel.center
            )
        )

        # ==========================================
        # EASY BOSS HEALTH HUD (Levels 5 and 10 only)
        # ==========================================

        if self.is_boss_level and self.boss is not None and self.boss.alive:
            boss_panel = pygame.Rect(screen.get_width() // 2 - 245, 80, 490, 58)
            pygame.draw.rect(screen, (23, 19, 31), boss_panel, border_radius=8)
            pygame.draw.rect(screen, (204, 184, 132), boss_panel, 2, border_radius=8)

            boss_label = (
                "ORC BOSS" if self.boss_kind == "orc" else "YOKAI BOSS"
            )
            hp_text = f"{boss_label}: {self.boss.hit_points} / {self.boss.max_hit_points} HP"
            hp_surface = pygame.font.Font(None, 23).render(hp_text, True, (255, 244, 220))
            screen.blit(hp_surface, hp_surface.get_rect(center=(boss_panel.centerx, boss_panel.y + 16)))

            bar_rect = pygame.Rect(boss_panel.x + 16, boss_panel.y + 35, boss_panel.width - 32, 13)
            pygame.draw.rect(screen, (63, 49, 49), bar_rect, border_radius=5)
            fill_width = int(bar_rect.width * max(0, self.boss.hit_points) / self.boss.max_hit_points)
            if fill_width > 0:
                pygame.draw.rect(
                    screen,
                    (208, 53, 65) if self.boss_kind == "orc" else (134, 68, 208),
                    pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_rect.height),
                    border_radius=5,
                )

        # ==========================================
        # LEVEL COMPLETE SCREEN
        # ==========================================

        if self.level_complete:

            overlay = pygame.Surface(
                screen.get_size(),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 150)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            complete_text = (
                self.big_font.render(
                    "LEVEL COMPLETE!",
                    True,
                    (255, 255, 255)
                )
            )

            score_complete = (
                self.font.render(
                    f"Carrots Collected: {self.score}",
                    True,
                    (255, 220, 50)
                )
            )

            screen.blit(
                complete_text,
                complete_text.get_rect(
                    center=(
                        screen.get_width() // 2,
                        screen.get_height() // 2 - 40
                    )
                )
            )

            screen.blit(
                score_complete,
                score_complete.get_rect(
                    center=(
                        screen.get_width() // 2,
                        screen.get_height() // 2 + 30
                    )
                )
            )
        # ==========================================
        # ENEMIES
        # ==========================================

        view_left = self.camera.x - DRAW_MARGIN
        view_right = self.camera.x + screen.get_width() + DRAW_MARGIN
        for enemy in self.enemies:
            if not (view_left <= enemy.rect.centerx <= view_right):
                continue
            enemy.draw(
                screen,
                self.camera
            )

        # ==========================================
        # PROJECTILES
        # ==========================================

        for projectile in self.projectiles:
            projectile.draw(screen, self.camera)

        # ==========================================
        # DEATH FLASH
        # ==========================================

        if self.death_flash_timer > 0:

            flash = pygame.Surface(
                screen.get_size(),
                pygame.SRCALPHA
            )

            alpha = int(
                140
                * (
                    self.death_flash_timer
                    / self.death_flash_duration
                )
            )

            flash.fill(
                (255, 60, 60, alpha)
            )

            screen.blit(
                flash,
                (0, 0)
            )

        for npc in ([] if self.is_boss_level else self.npcs):

            npc.draw(
                screen,
                self.camera
            )

            # ==========================================
            # TALK PROMPT
            # ==========================================

            distance = abs(
                self.player.rect.centerx -
                npc.rect.centerx
            )

            if distance < 80 and not self.dialogue.active:
                prompt_font = pygame.font.Font(
                    None,
                    22
                )

                prompt = prompt_font.render(
                    "Press E to talk",
                    True,
                    (255, 255, 255)
                )

                prompt_rect = prompt.get_rect(
                    center=(
                        npc.rect.centerx - self.camera.x,
                        npc.rect.top - 35
                    )
                )

                # Small background
                background_rect = prompt_rect.inflate(
                    12,
                    8
                )

                pygame.draw.rect(
                    screen,
                    (30, 30, 30),
                    background_rect
                )

                screen.blit(
                    prompt,
                    prompt_rect
                )

        for particle in self.particles:
            particle.draw(
                screen,
                self.camera
            )

        self.draw_dialogue(screen)

    # ==============================================
    # GENERATE ENEMIES
    # ==============================================

    # ==============================================
    # EASY ENEMY DENSITY
    # ==============================================

    def _generate_easy_enemies_by_density(self):
        """Place Easy enemies at a steady rate of about one per 450 world px."""
        final_start = getattr(self, "final_approach_start", self.width)
        playable_end = max(
            EASY_ENEMY_START_BUFFER,
            min(self.width, int(final_start) - 70),
        )

        eligible_platforms = [
            platform
            for platform in self.platforms[1:]
            if (
                platform.rect.width >= 110
                and EASY_ENEMY_START_BUFFER <= platform.rect.centerx < playable_end
                and platform.rect.right <= final_start
            )
        ]
        if not eligible_platforms:
            return

        used_platforms = set()
        placed_centers = []

        for zone_start in range(
            EASY_ENEMY_START_BUFFER, playable_end, EASY_ENEMY_SPACING
        ):
            zone_end = min(zone_start + EASY_ENEMY_SPACING, playable_end)
            target_x = (zone_start + zone_end) // 2

            zone_platforms = [
                platform
                for platform in eligible_platforms
                if id(platform) not in used_platforms
                and zone_start <= platform.rect.centerx < zone_end
            ]

            # Some platform layouts leave a density zone without a usable
            # platform. Use the closest unused platform instead of leaving a
            # large part of the level empty.
            if not zone_platforms:
                zone_platforms = [
                    platform
                    for platform in eligible_platforms
                    if id(platform) not in used_platforms
                    and abs(platform.rect.centerx - target_x) <= EASY_ENEMY_SPACING
                ]

            zone_platforms.sort(
                key=lambda platform: abs(platform.rect.centerx - target_x)
            )

            for platform in zone_platforms:
                sprite_key = random.choices(
                    [
                        "green_slime", "blue_slime", "red_slime",
                        "swordsman_pink", "swordsman_silver", "swordsman_blue",
                    ],
                    weights=[0.42, 0.21, 0.07, 0.10, 0.10, 0.10],
                    k=1,
                )[0]

                if sprite_key in EASY_SLIME_TYPES:
                    base_size = {
                        "green_slime": 62,
                        "blue_slime": 62,
                        "red_slime": 66,
                    }[sprite_key]
                    enemy_width = round(base_size * EASY_SLIME_SIZE_MULTIPLIER)
                    enemy_height = enemy_width
                    speed = 1.0
                    sprite_scale = EASY_SLIME_SIZE_MULTIPLIER
                else:
                    enemy_width = 58
                    enemy_height = 58
                    speed = 0.85
                    sprite_scale = 1.0

                margin = 20
                left_limit = platform.rect.left + margin
                right_limit = platform.rect.right - margin
                max_x = right_limit - enemy_width
                if max_x < left_limit:
                    continue

                preferred_x = max(
                    left_limit,
                    min(max_x, target_x - enemy_width // 2),
                )
                position_options = [preferred_x]
                position_options.extend(
                    random.randint(left_limit, max_x) for _ in range(12)
                )
                position_options = list(dict.fromkeys(position_options))

                clear_positions = []
                safe_positions = []
                for x in position_options:
                    center_x = x + enemy_width // 2
                    if any(
                        abs(center_x - placed_x) < EASY_ENEMY_MIN_SEPARATION
                        for placed_x in placed_centers
                    ):
                        continue
                    safe_positions.append(x)
                    if self._item_position_clear(center_x, 115):
                        clear_positions.append(x)

                # Prefer clearance from collectibles/checkpoints, but keep
                # the spacing guarantee if every candidate has a nearby item.
                choices = clear_positions or safe_positions
                if not choices:
                    continue

                x = min(
                    choices,
                    key=lambda candidate_x: abs(
                        candidate_x + enemy_width // 2 - target_x
                    ),
                )
                enemy_center_x = x + enemy_width // 2
                y = platform.rect.top - enemy_height

                enemy = Enemy(
                    x,
                    y,
                    left_limit,
                    right_limit,
                    speed * self.enemy_speed_multiplier,
                    "slime",
                    platform.rect.top,
                    sprite_key,
                    sprite_scale=sprite_scale,
                )
                enemy.rect.bottom = platform.rect.top
                enemy.rect.centerx = enemy_center_x
                if enemy.rect.left < left_limit:
                    enemy.rect.left = left_limit
                if enemy.rect.right > right_limit:
                    enemy.rect.right = right_limit
                enemy.platform_top = platform.rect.top

                self.enemies.append(enemy)
                placed_centers.append(enemy.rect.centerx)
                used_platforms.add(id(platform))
                break

    # ==============================================
    # GENERATE ENEMIES - DIFFICULTY ROUTER
    # ==============================================

    def generate_enemies(self):

        self.enemies.clear()

        if self.is_boss_level:
            if self.boss_kind == "orc":
                variant_hp = {
                    "orc_berserk": 20,
                    "orc_shaman": 15,
                    "orc_warrior": 10,
                }
                variant = random.choice(tuple(variant_hp))
                max_hp = variant_hp[variant]
                target_height = 165
            else:
                variant_hp = {
                    "karasu_tengu": 32,
                    "kitsune": 35,
                    "yamabushi_tengu": 38,
                }
                variant = random.choice(tuple(variant_hp))
                max_hp = variant_hp[variant]
                target_height = 205

            self.boss = Boss(
                boss_kind=self.boss_kind,
                variant=variant,
                center_x=self.width // 2,
                floor_y=self.ground.rect.top,
                left_limit=0,
                right_limit=self.width,
                hit_points=max_hp,
                target_height=target_height,
            )

            # Derive patrol limits from the full sprite frame, not just the
            # smaller damage body, so the boss cannot overlap a platform.
            side_platforms = self.platforms[1:]
            left_clear_edge = max(
                platform.rect.right for platform in side_platforms
                if platform.rect.centerx < self.width // 2
            )
            right_clear_edge = min(
                platform.rect.left for platform in side_platforms
                if platform.rect.centerx > self.width // 2
            )
            frame_width = self.boss.rect.width
            body_bounds = self.boss.body_bounds
            body_width = body_bounds.width
            body_left_offsets = (
                -(body_bounds.left + body_width / 2),
                -((frame_width - body_bounds.right) + body_width / 2),
            )
            frame_left_offset = min(body_left_offsets)
            frame_right_offset = max(offset + frame_width for offset in body_left_offsets)
            center_min = left_clear_edge - frame_left_offset
            center_max = right_clear_edge - frame_right_offset
            half_body = self.boss.body_rect.width / 2
            self.boss.left_limit = math.ceil(center_min - half_body)
            self.boss.right_limit = math.floor(center_max + half_body)

            self.enemies.append(self.boss)
            return

        # Easy uses a world-distance density rule rather than independent
        # per-platform random rolls. Normal and Hard continue through the
        # existing generation code unchanged.
        if self.difficulty == "easy":
            self._generate_easy_enemies_by_density()
            return

        total_platforms = 0
        small_platforms = 0
        chance_failed = 0
        space_failed = 0
        created = 0

        heavy_count = 0
        for platform in self.platforms[1:]:

            total_platforms += 1

            # ======================================
            # PLATFORM SIZE
            # ======================================

            if platform.rect.width < 55:

                small_platforms += 1
                continue

            # ======================================
            # SPAWN CHANCE
            # ======================================

            progress = (
                platform.rect.centerx
                / self.width
            )

            final_start = getattr(self, "final_approach_start", self.width)
            if platform.rect.centerx >= final_start - 70:
                continue

            if progress < 0.30:
                spawn_chance = 0.55
            elif progress < 0.60:
                spawn_chance = 0.65
            else:
                spawn_chance = 0.75

            spawn_chance = min(0.95, spawn_chance * self.enemy_spawn_multiplier)
            if random.random() > spawn_chance:

                chance_failed += 1
                continue

            # ======================================
            # ENEMY TYPE
            # ======================================

            roll = random.random()

            if progress < 0.30:

                if roll < 0.40:
                    enemy_type = "slime"

                elif roll < 0.75:
                    enemy_type = "fast"

                else:
                    enemy_type = "jumper"

            elif progress < 0.60:

                if roll < 0.20:
                    enemy_type = "slime"

                elif roll < 0.45:
                    enemy_type = "fast"

                elif roll < 0.70:
                    enemy_type = "jumper"

                else:
                    enemy_type = "flyer"


            else:

                if roll < 0.10:

                    enemy_type = "slime"


                elif roll < 0.25:

                    enemy_type = "fast"


                elif roll < 0.40:

                    enemy_type = "jumper"


                elif roll < 0.60:

                    enemy_type = "flyer"


                else:

                    enemy_type = "heavy"

                # ======================================
                # FLYER SAFETY
                # ======================================

                if (
                        enemy_type == "flyer"
                        and platform.rect.width < 180
                ):
                    # Small platforms should not have flyers

                    enemy_type = random.choice([
                        "slime",
                        "fast",
                        "jumper"
                    ])

            # ======================================
            # EASY DIFFICULTY: SLIMES + SWORDSMEN
            # ======================================
            # Keep the existing spawn locations/chance while allowing Easy
            # to select the original slimes or one of three new sword enemies.
            if self.difficulty == "easy":
                enemy_type = "slime"

            # ======================================
            # NORMAL DIFFICULTY: SPRITE ENEMY TYPE
            # ======================================
            # Reuses the same progress-based rarity curve above, but on
            # normal difficulty every legacy slot is re-skinned as one of
            # the 6 animated sprite enemies instead of a vector shape.

            sprite_key = None

            if enemy_type == "slime" and self.difficulty in ("easy", "hard"):
                if self.difficulty == "easy":
                    sprite_key = random.choices(
                        [
                            "green_slime", "blue_slime", "red_slime",
                            "swordsman_pink", "swordsman_silver", "swordsman_blue",
                        ],
                        # Keep the existing slime ratio within its 70% share;
                        # the new sword enemies make up the remaining 30%.
                        weights=[0.42, 0.21, 0.07, 0.10, 0.10, 0.10],
                        k=1,
                    )[0]
                else:
                    sprite_key = random.choices(
                        ["green_slime", "blue_slime", "red_slime"],
                        weights=[0.20, 0.35, 0.45],
                        k=1,
                    )[0]

            if self.difficulty == "normal":

                legacy_to_sprite = {
                    "slime": "worker",
                    "jumper": "boxer",
                    "flyer": "chopper",
                    "heavy": "hammerbot",
                }

                if enemy_type == "fast":
                    sprite_key = random.choice(["minebot", "soldier"])
                else:
                    sprite_key = legacy_to_sprite.get(enemy_type, "worker")

            # ======================================
            # EASY PLATFORM FIT
            # ======================================
            # Sword sprites are wider than slimes. Use a slime on narrow
            # platforms so their patrol boundaries remain valid.
            if (
                self.difficulty == "easy"
                and sprite_key in EASY_SWORDSMAN_TYPES
                and platform.rect.width < 105
            ):
                sprite_key = random.choice(EASY_SLIME_TYPES)

            # ======================================
            # ENEMY SIZE
            # ======================================

            if self.difficulty == "easy" and sprite_key in EASY_SLIME_TYPES:

                base_size = {
                    "green_slime": 62,
                    "blue_slime": 62,
                    "red_slime": 66,
                }[sprite_key]
                enemy_width = round(base_size * EASY_SLIME_SIZE_MULTIPLIER)
                enemy_height = enemy_width
                speed = 1.0

            elif self.difficulty == "easy" and sprite_key in EASY_SWORDSMAN_TYPES:

                enemy_width = 58
                enemy_height = 58
                speed = 0.85

            elif enemy_type == "heavy":

                # Heavy enemies need larger platforms

                if platform.rect.width < 140:
                    continue

                enemy_width = 50
                enemy_height = 50
                speed = 1

            elif platform.rect.width < 75:

                # Very small platform

                enemy_width = 24
                enemy_height = 24

                if enemy_type == "fast":
                    speed = 1.5
                else:
                    speed = 1.0

            else:

                enemy_width = 32
                enemy_height = 32

                if enemy_type == "fast":
                    speed = 1.5
                else:
                    speed = 1.0

            # ======================================
            # PATROL AREA
            # ======================================

            margin = 20

            left_limit = (
                platform.rect.left + margin
            )

            right_limit = (
                platform.rect.right - margin
            )

            if (
                right_limit - left_limit
                < enemy_width
            ):

                space_failed += 1
                continue

            # ======================================
            # POSITION
            # ======================================

            x = random.randint(
                left_limit,
                right_limit - enemy_width
            )

            y = (
                platform.rect.top
                - enemy_height
            )

            # ======================================
            # CREATE
            # ======================================

            enemy_center_x = x + enemy_width // 2
            if not self._item_position_clear(enemy_center_x, 115):
                continue

            enemy = Enemy(
                x,
                y,
                left_limit,
                right_limit,
                speed * self.enemy_speed_multiplier,
                enemy_type,
                platform.rect.top,
                sprite_key,
                sprite_scale=(
                    EASY_SLIME_SIZE_MULTIPLIER
                    if self.difficulty == "easy" and sprite_key in EASY_SLIME_TYPES
                    else 1.0
                ),
            )

            if sprite_key:
                # Sprite enemies size themselves from their real artwork,
                # which rarely matches the legacy 24/32/50px placeholder
                # box above, so re-anchor them to stand on the platform
                # (or hover above it, for the flying chopper) and stay
                # within their patrol bounds afterwards.
                if sprite_key == "chopper":
                    # Keep the chopper clearly above the 60px player body.
                    enemy.rect.bottom = platform.rect.top - 80
                else:
                    enemy.rect.bottom = platform.rect.top
                enemy.rect.centerx = enemy_center_x
                if enemy.rect.left < left_limit:
                    enemy.rect.left = left_limit
                if enemy.rect.right > right_limit:
                    enemy.rect.right = right_limit
                enemy.platform_top = platform.rect.top

            self.enemies.append(enemy)
            if enemy_type == "heavy":
                heavy_count += 1

            created += 1

        # ==========================================
        # DEBUG RESULTS
        # ==========================================






    # ==============================================
    # GENERATE GROUND ROCKS
    # ==============================================

    def generate_obstacles(self):
        """Generate exactly 2 rocks per 1000 world pixels on solid ground.

        Rocks are independent from bushes and are never placed on platforms,
        inside pits, or inside the protected final approach.
        """
        self.obstacles.clear()

        # Easy and Normal have no rocks; Hard retains its existing rocks.
        if self.difficulty in ("easy", "normal"):
            return

        ground_top = self.ground.rect.top
        final_start = getattr(self, "final_approach_start", self.width)
        playable_end = max(0, min(self.width, final_start - 70))

        if playable_end <= 200:
            return

        # Split the usable world into 1000-pixel zones. Each complete zone
        # receives exactly two rocks. A short final zone also receives two
        # when there is enough room for safe placement.
        zone_starts = list(range(0, playable_end, 1000))

        for zone_start in zone_starts:
            zone_end = min(zone_start + 1000, playable_end)
            if zone_end - zone_start < 300:
                continue

            created = 0
            attempts = 0

            while created < ROCKS_PER_1000 and attempts < 500:
                attempts += 1
                width = random.randint(35, 50)
                height = random.randint(30, 45)
                margin = 80

                left = zone_start + margin
                right = zone_end - margin - width
                if right <= left:
                    continue

                x = random.randint(left, right)
                rect = pygame.Rect(x, ground_top - height, width, height)

                # Never place a rock in a pit.
                if any(rect.inflate(24, 0).colliderect(pit) for pit in self.pits):
                    continue

                # Keep rocks separated from every other gameplay item.
                if any(abs(rect.centerx - o.rect.centerx) < ROCK_MIN_SPACING for o in self.obstacles):
                    continue

                # Rocks have their own large spacing rule. Other item types do
                # not prevent a rock from being generated.
                if any(abs(rect.centerx - getattr(item, "rect").centerx) < 80
                       for item in getattr(self, "collectibles", [])):
                    continue

                self.obstacles.append(
                    Obstacle(
                        x,
                        ground_top - height,
                        width,
                        height,
                        "rock"
                    )
                )
                created += 1

    def generate_bushes(self):
        """Generate bushes on platforms with strict spacing rules.

        Rules:
        - At most ONE bush per platform.
        - Two consecutive platforms can never both have bushes.
        - Bushes are placed only on normal platforms, never on ground.
        - Target density remains 4-5 bushes per 1000 world pixels when the
          available platform layout allows it.
        """
        self.bushes.clear()

        # Easy and Normal have no bushes; Hard retains its existing bushes.
        if self.difficulty in ("easy", "normal"):
            return

        final_start = getattr(self, "final_approach_start", self.width)
        playable_end = max(0, min(self.width, final_start - 70))

        bush_types = [Bush.SLOW, Bush.FAST, Bush.POISON]
        weights = [0.40, 0.35, 0.25]

        # Keep only regular generated platforms. Ground is excluded.
        platform_candidates = [
            (index, platform)
            for index, platform in enumerate(self.platforms[1:], start=1)
            if platform.rect.width >= 75
            and platform.rect.centerx < playable_end
        ]

        selected_platform_indices = set()

        for zone_start in range(0, playable_end, 1000):
            zone_end = min(zone_start + 1000, playable_end)
            if zone_end - zone_start < 300:
                continue

            target_count = random.randint(
                BUSHES_PER_1000_MIN, BUSHES_PER_1000_MAX
            )

            # Use the platform center for zone ownership. This prevents one
            # platform from being selected again when it crosses a zone edge.
            candidates = [
                (index, platform)
                for index, platform in platform_candidates
                if zone_start <= platform.rect.centerx < zone_end
                and index not in selected_platform_indices
            ]
            random.shuffle(candidates)

            created = 0
            for index, platform in candidates:
                if created >= target_count:
                    break

                # Exactly one bush per platform, and never on consecutive
                # platforms. Check both neighboring generated platforms.
                if index - 1 in selected_platform_indices:
                    continue
                if index + 1 in selected_platform_indices:
                    continue

                width = random.randint(24, 30)
                height = random.randint(26, 32)
                margin = 12

                usable_left = max(platform.rect.left + margin, zone_start + 15)
                usable_right = min(
                    platform.rect.right - margin - width,
                    zone_end - 15 - width
                )
                if usable_right <= usable_left:
                    continue

                x = random.randint(usable_left, usable_right)
                center_x = x + width // 2
                bush_rect = pygame.Rect(
                    x,
                    platform.rect.top - height,
                    width,
                    height,
                )

                # Keep bushes apart even when they are on non-consecutive
                # platforms, so the world does not look cluttered.
                if any(
                    abs(center_x - b.rect.centerx) < BUSH_MIN_SPACING
                    for b in self.bushes
                ):
                    continue

                bush_type = random.choices(
                    bush_types,
                    weights=weights,
                    k=1,
                )[0]

                self.bushes.append(
                    Bush(
                        x,
                        platform.rect.top,
                        bush_type,
                        width,
                        height,
                        variant=random.randint(0, 4),
                        platform=platform,
                    )
                )

                selected_platform_indices.add(index)
                created += 1

    def update_bush_effects(self):
        current_x = self.player.rect.centerx
        previous_x = getattr(self.player, "previous_center_x", current_x)
        speed_modifier = 1.0

        for bush in self.bushes:
            if not bush.active:
                continue
            touching = self.player.rect.colliderect(bush.rect)

            if bush.bush_type == Bush.SLOW and touching:
                speed_modifier = min(speed_modifier, 0.55)
            elif bush.bush_type == Bush.FAST and touching:
                speed_modifier = max(speed_modifier, 1.55)
            elif bush.bush_type == Bush.POISON:
                # Poison ONLY damages a player who walks across the bush while
                # grounded. Jumping through or touching from above is harmless.
                walking_through = (
                    self.player.on_ground
                    and abs(current_x - previous_x) > 0
                    and ((previous_x < bush.rect.centerx <= current_x)
                         or (previous_x > bush.rect.centerx >= current_x))
                )
                if walking_through and not bush.triggered:
                    bush.triggered = True
                    if self.damage_cooldown <= 0:
                        self.player.health = max(0, self.player.health - 1)
                        self.damage_taken = True
                        self.damage_cooldown = self.damage_cooldown_max
                        self.player.take_damage()
                        self.create_particles(bush.rect.centerx, bush.rect.centery, (120, 220, 70), count=10)
                if not touching and abs(current_x - bush.rect.centerx) > bush.rect.width:
                    bush.triggered = False

        self.player.speed = self.player.base_speed * speed_modifier

    def handle_player_attack(self):

        if not self.player.is_attacking():
            return

        attack_rect = self.player.get_attack_rect()

        for enemy in self.enemies:

            if not enemy.alive:
                continue

            target_rect = getattr(enemy, "body_rect", enemy.rect)
            if not attack_rect.colliderect(target_rect):
                continue

            defeated = enemy.take_hit(
                self.player.attack_id
            )

            if defeated:
                self.create_particles(
                    enemy.rect.centerx,
                    enemy.rect.centery,
                    (255, 220, 80),
                    count=14
                )
            else:
                self.create_particles(
                    enemy.rect.centerx,
                    enemy.rect.centery,
                    (255, 160, 80),
                    count=7
                )

            # Attack feedback is visual/particle based for now.

    # ==============================================
    # ENEMY ATTACKS
    # ==============================================
    def handle_enemy_attack(self, enemy, attack):

        if not enemy.alive:
            return

        attack_range = attack.get("range", 50)
        vertical_range = attack.get("vertical_range", 78)
        enemy_body = getattr(enemy, "body_rect", enemy.rect)

        # Attack hitbox is a one-sided rectangle in the enemy's facing
        # direction. This is checked only when the attack animation reaches
        # its configured hit frame. Enemy body overlap never causes damage.
        if enemy.facing >= 0:
            attack_rect = pygame.Rect(
                enemy_body.right - 6,
                enemy_body.centery - vertical_range // 2,
                attack_range + 6,
                vertical_range
            )
        else:
            attack_rect = pygame.Rect(
                enemy_body.left - attack_range,
                enemy_body.centery - vertical_range // 2,
                attack_range + 6,
                vertical_range
            )

        if not attack_rect.colliderect(self.player.rect):
            return

        if self.damage_cooldown > 0:
            return

        damage = max(1, int(attack.get("damage", 1)))
        self.player.health = max(0, self.player.health - damage)
        self.damage_taken = True
        self.enemy_hit_taken = True
        self.damage_cooldown = self.damage_cooldown_max
        self.player.take_damage()

        if self.sound_manager is not None:
            self.sound_manager.play("damage")

        self.create_particles(
            self.player.rect.centerx,
            self.player.rect.centery,
            (255, 80, 80),
            count=10
        )

    # Kept as a compatibility method for older callers. Enemy bodies are
    # intentionally non-solid, so this no longer performs collision damage,
    # stomp logic, pushing, or bouncing.
    def handle_enemy_collisions(self):
        return


    def update_projectiles(self):

        for projectile in self.projectiles:
            projectile.update(
                platforms=self.platforms,
                world_width=self.width
            )

        self.projectiles = [
            projectile
            for projectile in self.projectiles
            if projectile.alive
        ]

    def handle_projectile_collisions(self):

        for projectile in self.projectiles:

            if not projectile.check_collision(self.player):
                continue

            projectile.alive = False

            if self.damage_cooldown > 0:
                continue

            self.player.health = max(0, self.player.health - projectile.damage)
            self.damage_taken = True
            self.enemy_hit_taken = True
            self.player.take_damage()

            if self.sound_manager is not None:
                self.sound_manager.play("damage")

            self.create_particles(
                self.player.rect.centerx,
                self.player.rect.centery,
                (255, 80, 80),
                count=10
            )

            self.damage_cooldown = self.damage_cooldown_max

    def update_particles(self):
        for particle in self.particles:
            particle.update()

        self.particles = [
            particle
            for particle in self.particles
            if particle.is_alive()
        ]

    def create_particles(self, x, y, color, count=8):
        for _ in range(count):
            self.particles.append(
                Particle(
                    x,
                    y,
                    color
                )
            )

    def interact_with_npc(self):
        if self.dialogue.active:
            self.dialogue.next_line()

            if not self.dialogue.active:
                self.current_npc = None

            return

        for npc in self.npcs:
            distance = abs(
                self.player.rect.centerx -
                npc.rect.centerx
            )

            if distance < 80:
                self.current_npc = npc
                self.dialogue = Dialogue(npc.dialogue)
                self.dialogue.start()
                break

    def draw_dialogue(self, screen):

        if not self.dialogue.active:
            return

        # ==========================================
        # DIALOGUE BOX
        # ==========================================

        box_width = 700
        box_height = 140

        box_x = (
                        screen.get_width() - box_width
                ) // 2

        box_y = (
                screen.get_height() - box_height - 40
        )

        # Background
        pygame.draw.rect(
            screen,
            (30, 30, 30),
            (
                box_x,
                box_y,
                box_width,
                box_height
            )
        )

        # Border
        pygame.draw.rect(
            screen,
            (255, 220, 80),
            (
                box_x,
                box_y,
                box_width,
                box_height
            ),
            4
        )

        # ==========================================
        # TEXT
        # ==========================================

        name_font = pygame.font.Font(None, 32)
        name_surface = name_font.render(
            self.current_npc.name,
            True,
            (255, 220, 80)
        )

        name_rect = name_surface.get_rect(
            center=(box_x + box_width // 2, box_y + 25)
        )

        screen.blit(name_surface, name_rect)

        text = self.dialogue.get_current_line()

        dialogue_font = pygame.font.Font(
            None,
            28
        )

        text_surface = dialogue_font.render(
            text,
            True,
            (255, 255, 255)
        )

        text_rect = text_surface.get_rect(
            center=(
                box_x + box_width // 2,
                box_y + 70
            )
        )

        screen.blit(
            text_surface,
            text_rect
        )

        # ==========================================
        # INSTRUCTION
        # ==========================================

        instruction = dialogue_font.render(
            "Press E to continue",
            True,
            (200, 200, 200)
        )

        instruction_rect = instruction.get_rect(
            center=(
                box_x + box_width // 2,
                box_y + 110
            )
        )

        screen.blit(
            instruction,
            instruction_rect
        )