import os
import pygame

from src.settings import WORLD_WIDTH, PLAYER_SPEED, PLAYER_GRAVITY, PLAYER_JUMP_STRENGTH
from src.entities.game_object import GameObject
from src import keybinds

LANDING_TOLERANCE = 15

# Animation frames are loaded and scaled from disk once, then shared by every
# Player (a new Player is created on each level start / retry). Frames are
# never modified in place, so sharing them is safe.
_FRAME_CACHE = {}


class Player(GameObject):

    def __init__(self, x, y, character_type="default"):
        super().__init__(x, y, 40, 60)
        self.character_type = "fighter" if str(character_type).lower() == "fighter" else "default"

        # Movement
        self.base_speed = PLAYER_SPEED
        self.speed = self.base_speed
        self.facing_right = True
        self.previous_center_x = self.rect.centerx

        # Physics
        self.velocity_y = 0
        self.gravity = PLAYER_GRAVITY
        self.jump_strength = PLAYER_JUMP_STRENGTH
        self.on_ground = False
        self.current_platform = None
        self.previous_platform_x = 0
        self.previous_platform_y = 0

        # Health
        self.health = 3
        self.damage_flash_timer = 0
        self.damage_flash_duration = 12

        # Coyote time
        self.coyote_time = 0
        self.coyote_time_max = 8

        # --------------------------------------------------
        # SPRITE ANIMATIONS
        # --------------------------------------------------
        self.idle_frames = []
        self.walk_frames = []
        self.jump_frames = []
        self.attack1_frames = []
        self.attack2_frames = []
        self.dead_frames = []

        # Keep pixel-art proportions. Do NOT force every frame
        # into the same width/height rectangle.
        self.sprite_height = 88

        if self.character_type == "fighter":
            self._load_spritesheet_frames("Idle.png", self.idle_frames)
            self._load_spritesheet_frames("Run.png", self.walk_frames)
            self._load_spritesheet_frames("Jump.png", self.jump_frames)
            self._load_spritesheet_frames("Attack_1.png", self.attack1_frames)
            self._load_spritesheet_frames("Attack_2.png", self.attack2_frames)
            self._load_spritesheet_frames("Dead.png", self.dead_frames)
        else:
            self._load_animation_frames("idle", "idle_", 6, self.idle_frames)
            self._load_animation_frames("walk", "walk_", 8, self.walk_frames)
            self._load_animation_frames("jump", "jump_", 8, self.jump_frames)
            self._load_animation_frames("attack1", "attack1_", 4, self.attack1_frames)
            self._load_animation_frames("attack2", "attack2_", 4, self.attack2_frames)
            self._load_animation_frames("dead", "dead_", 5, self.dead_frames)

        # Animation state
        self.current_animation = "idle"
        self.animation_timer = 0
        self.animation_frame = 0
        self.air_animation_timer = 0
        self.jump_animation_timer = 0
        self.right_attack_requested = False
        # Set by the game each frame while the player is briefly invincible
        # after a hit, so draw() can blink the sprite.
        self.invincible_blink = False

        # --------------------------------------------------
        # ATTACK
        # --------------------------------------------------
        self.attack_frames = []
        self.attack_timer = 0
        self.attack_duration = 28
        self.attack_frame = 0
        self.attack_cooldown = 0
        self.attack_cooldown_max = 12
        self.attack_id = 0
        self.attack_combo = 0

        # --------------------------------------------------
        # DEATH / RESPAWN
        # --------------------------------------------------
        self.death_timer = 0
        self.death_duration = 48
        self.death_animation_frame = 0
        self.respawn_timer = 0
        self.respawn_delay = 24

    # ======================================================
    # SPRITES
    # ======================================================

    def _load_animation_frames(self, folder, prefix, count, target):
        """Load sprite frames with stable pixel-art scaling and foot anchoring.

        The source PNGs have different canvas sizes and transparent margins.
        We crop ONLY transparent borders, use ONE scale for the whole
        animation, then place every visible frame on the same fixed canvas.
        This prevents jumping, shrinking, and frame-to-frame drifting.
        """
        cache_key = (folder, prefix, count)
        if cache_key in _FRAME_CACHE:
            target.extend(_FRAME_CACHE[cache_key])
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        animation_dir = os.path.join(base_dir, "assets", "player", folder)

        sources = []
        for i in range(count):
            path = os.path.join(animation_dir, f"{prefix}{i}.png")
            try:
                image = pygame.image.load(path).convert_alpha()
                bbox = image.get_bounding_rect(min_alpha=10)
                if bbox.width <= 0 or bbox.height <= 0:
                    raise pygame.error("Empty sprite")
                # Crop transparent borders only. Keep all visible pixels.
                cropped = image.subsurface(bbox).copy()
                sources.append(cropped)
            except (pygame.error, FileNotFoundError):
                target.clear()
                _FRAME_CACHE[cache_key] = []
                return

        if not sources:
            return

        # One scale for the whole animation, based on the tallest visible
        # pose. This keeps every animation internally consistent.
        reference_height = max(img.get_height() for img in sources)
        TARGET_VISIBLE_HEIGHT = 92
        scale = TARGET_VISIBLE_HEIGHT / float(reference_height)

        CANVAS_WIDTH = 240
        CANVAS_HEIGHT = 130
        FOOT_Y = 116

        for image in sources:
            new_w = max(1, round(image.get_width() * scale))
            new_h = max(1, round(image.get_height() * scale))

            scaled = pygame.transform.scale(
                image,
                (new_w, new_h)
            )

            frame = pygame.Surface(
                (CANVAS_WIDTH, CANVAS_HEIGHT),
                pygame.SRCALPHA
            )

            # Every visible pose shares the exact same foot baseline.
            x = (CANVAS_WIDTH - new_w) // 2
            y = FOOT_Y - new_h
            frame.blit(scaled, (x, y))
            target.append(frame)

        _FRAME_CACHE[cache_key] = list(target)

    def _load_spritesheet_frames(self, filename, target):
        """Load a 128px-cell fighter spritesheet using stable foot anchoring."""
        cache_key = ("fighter_sheet", filename)
        if cache_key in _FRAME_CACHE:
            target.extend(_FRAME_CACHE[cache_key])
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(base_dir, "assets", "fighter", filename)

        try:
            sheet = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            _FRAME_CACHE[cache_key] = []
            return

        cell_size = sheet.get_height()
        if cell_size <= 0 or sheet.get_width() % cell_size != 0:
            _FRAME_CACHE[cache_key] = []
            return

        sources = []
        for index in range(sheet.get_width() // cell_size):
            cell = sheet.subsurface(
                (index * cell_size, 0, cell_size, cell_size)
            ).copy()
            bbox = cell.get_bounding_rect(min_alpha=10)
            if bbox.width <= 0 or bbox.height <= 0:
                continue
            sources.append(cell.subsurface(bbox).copy())

        if not sources:
            _FRAME_CACHE[cache_key] = []
            return

        target_visible_height = 92
        scale = target_visible_height / float(max(frame.get_height() for frame in sources))
        canvas_width = 240
        canvas_height = 130
        foot_y = 116
        frames = []

        for source in sources:
            scaled_width = max(1, round(source.get_width() * scale))
            scaled_height = max(1, round(source.get_height() * scale))
            scaled = pygame.transform.scale(source, (scaled_width, scaled_height))
            frame = pygame.Surface((canvas_width, canvas_height), pygame.SRCALPHA)
            frame.blit(
                scaled,
                ((canvas_width - scaled_width) // 2, foot_y - scaled_height),
            )
            frames.append(frame)

        target.extend(frames)
        _FRAME_CACHE[cache_key] = list(frames)

    # ======================================================
    # ATTACK
    # ======================================================

    def start_attack(self):
        if self.attack_cooldown > 0:
            return False
        if self.attack_timer > 0:
            return False
        if self.death_timer > 0 or self.respawn_timer > 0:
            return False

        # Alternate between Attack 1 and Attack 2.
        self.attack_combo += 1

        if self.attack_combo % 2 == 1 and self.attack1_frames:
            self.attack_frames = self.attack1_frames
        elif self.attack2_frames:
            self.attack_frames = self.attack2_frames
        elif self.attack1_frames:
            self.attack_frames = self.attack1_frames
        else:
            return False

        self.attack_timer = self.attack_duration
        self.attack_frame = 0
        self.animation_timer = 0
        self.attack_cooldown = self.attack_cooldown_max
        self.attack_id += 1
        self.current_animation = "attack"
        return True

    def is_attacking(self):
        return self.attack_timer > 0

    def get_attack_rect(self):
        attack_width = 62
        attack_height = 48
        attack_y = self.rect.y + 4

        if self.facing_right:
            return pygame.Rect(self.rect.right - 4, attack_y, attack_width, attack_height)

        return pygame.Rect(self.rect.left - attack_width + 4, attack_y, attack_width, attack_height)

    # ======================================================
    # INPUT
    # ======================================================

    def handle_input(self):
        keys = pygame.key.get_pressed()
        moving = False

        # Don't allow normal movement while the death sequence is playing.
        if self.death_timer > 0 or self.respawn_timer > 0:
            return False

        if keys[pygame.K_LEFT] or keys[keybinds.get("left")]:
            self.rect.x -= self.speed
            self.facing_right = False
            moving = True

        if keys[pygame.K_RIGHT] or keys[keybinds.get("right")]:
            self.rect.x += self.speed
            self.facing_right = True
            moving = True

        return moving

    # ======================================================
    # JUMP
    # ======================================================

    def jump(self):
        if self.death_timer > 0 or self.respawn_timer > 0 or self.attack_timer > 0:
            return False

        if self.on_ground or self.coyote_time > 0:
            self.velocity_y = self.jump_strength
            self.on_ground = False
            self.current_platform = None
            self.coyote_time = 0
            self.air_animation_timer = 0
            self.jump_animation_timer = 0
            self.animation_frame = 0
            return True

        return False

    # ======================================================
    # DAMAGE
    # ======================================================

    def take_damage(self):
        self.damage_flash_timer = self.damage_flash_duration

    # ======================================================
    # DEATH SEQUENCE
    # ======================================================

    def start_death_animation(self):
        if self.death_timer > 0 or self.respawn_timer > 0:
            return False

        self.death_timer = self.death_duration
        self.death_animation_frame = 0
        self.animation_timer = 0
        self.attack_timer = 0
        self.attack_frames = []
        self.velocity_y = 0
        self.current_platform = None
        self.on_ground = False
        self.current_animation = "dead"
        self.damage_flash_timer = 0
        return True

    def update_death_animation(self):
        if self.death_timer <= 0:
            return False

        self.death_timer -= 1
        self.current_animation = "dead"

        if self.dead_frames:
            elapsed = self.death_duration - self.death_timer
            frame_duration = max(1, self.death_duration // len(self.dead_frames))
            self.death_animation_frame = min(
                len(self.dead_frames) - 1,
                elapsed // frame_duration
            )

        return self.death_timer == 0

    def start_respawn_effect(self):
        self.respawn_timer = self.respawn_delay
        self.current_animation = "dead"

    def update_respawn_effect(self):
        if self.respawn_timer <= 0:
            return

        self.respawn_timer -= 1
        self.current_animation = "dead"

        if self.dead_frames:
            self.death_animation_frame = len(self.dead_frames) - 1

    # ======================================================
    # PHYSICS
    # ======================================================

    def apply_gravity(self):
        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y

    # ======================================================
    # COLLISION
    # ======================================================

    def handle_platform_collision(self, platforms, previous_rect):
        was_on_ground = self.on_ground
        self.on_ground = False
        self.current_platform = None

        for platform in platforms:
            landing_rect = platform.rect.inflate(LANDING_TOLERANCE * 2, 0)

            if self.velocity_y >= 0:
                if (
                    previous_rect.bottom <= platform.rect.top
                    and self.rect.bottom >= platform.rect.top
                    and self.rect.colliderect(landing_rect)
                ):
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                    self.on_ground = True
                    self.current_platform = platform
                    self.previous_platform_x = platform.rect.x
                    self.previous_platform_y = platform.rect.y
                    break

        if self.on_ground:
            self.coyote_time = self.coyote_time_max
        elif was_on_ground and self.coyote_time > 0:
            self.coyote_time -= 1
        elif self.coyote_time > 0:
            self.coyote_time -= 1

    # ======================================================
    # ANIMATION
    # ======================================================

    def update_animation(self, moving):
        # Death has absolute priority.
        if self.death_timer > 0 or self.respawn_timer > 0:
            self.current_animation = "dead"
            return

        # Attack has priority over movement/jump.
        if self.attack_timer > 0 and self.attack_frames:
            self.current_animation = "attack"

            elapsed = self.attack_duration - self.attack_timer
            # Four frames, each held for an equal portion of the attack.
            self.attack_frame = min(
                len(self.attack_frames) - 1,
                int(elapsed * len(self.attack_frames) / self.attack_duration)
            )
            return

        # --------------------------------------------------
        # JUMP
        # --------------------------------------------------
        if not self.on_ground and self.jump_frames:
            self.current_animation = "jump"

            # Drive the animation by elapsed jump time, not by velocity.
            # Velocity changes continuously and can skip pose bands.
            self.jump_animation_timer += 1

            estimated_flight = max(
                8,
                int((2 * abs(float(self.jump_strength))) /
                    max(0.01, float(self.gravity)))
            )

            progress = min(
                0.999,
                self.jump_animation_timer / float(estimated_flight)
            )

            self.animation_frame = min(
                len(self.jump_frames) - 1,
                int(progress * len(self.jump_frames))
            )
            return

        # --------------------------------------------------
        # WALK
        # --------------------------------------------------
        if moving and self.walk_frames:
            if self.current_animation != "walk":
                self.current_animation = "walk"
                self.animation_frame = 0
                self.animation_timer = 0

            self.animation_timer += 1
            if self.animation_timer >= 7:
                self.animation_timer = 0
                self.animation_frame = (
                    self.animation_frame + 1
                ) % len(self.walk_frames)
            return

        # --------------------------------------------------
        # IDLE
        # --------------------------------------------------
        if self.idle_frames:
            if self.current_animation != "idle":
                self.current_animation = "idle"
                self.animation_frame = 0
                self.animation_timer = 0

            self.animation_timer += 1
            if self.animation_timer >= 10:
                self.animation_timer = 0
                self.animation_frame = (
                    self.animation_frame + 1
                ) % len(self.idle_frames)

    # ======================================================
    # UPDATE
    # ======================================================

    def update(self, platforms, world_width=None):
        # Death animation freezes gameplay until the sequence is complete.
        if self.death_timer > 0:
            self.update_death_animation()
            return

        # Short respawn visual delay after Level handles the actual relocation.
        if self.respawn_timer > 0:
            self.update_respawn_effect()
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.attack_timer > 0:
            self.attack_timer -= 1

        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1

        previous_rect = self.rect.copy()
        self.previous_center_x = self.rect.centerx
        moving = self.handle_input()
        self.apply_gravity()
        self.handle_platform_collision(platforms, previous_rect)

        # Moving platform carry
        if (
            self.on_ground
            and self.current_platform is not None
            and hasattr(self.current_platform, "previous_x")
        ):
            platform = self.current_platform
            self.rect.x += platform.rect.x - platform.previous_x
            self.rect.y += platform.rect.y - platform.previous_y

        if self.rect.left < 0:
            self.rect.left = 0

        movement_world_width = WORLD_WIDTH if world_width is None else int(world_width)
        if self.rect.right > movement_world_width:
            self.rect.right = movement_world_width

        # Keep the character fully visible at the top of the screen.
        # Player sprites are drawn on a 130px canvas with the feet aligned
        # to a fixed baseline, so the visible character extends above the
        # physics rectangle. Stop upward movement at the screen ceiling.
        screen_top_margin = 70
        if self.rect.top < screen_top_margin:
            self.rect.top = screen_top_margin
            if self.velocity_y < 0:
                self.velocity_y = 0

        self.update_animation(moving)

    # ======================================================
    # DRAW
    # ======================================================

    def draw(self, screen, camera_rect=None):
        if camera_rect is None:
            camera_rect = self.rect

        frames = self.idle_frames
        frame_index = self.animation_frame

        if self.current_animation == "dead" and self.dead_frames:
            frames = self.dead_frames
            frame_index = self.death_animation_frame
        elif self.current_animation == "attack" and self.attack_frames:
            frames = self.attack_frames
            frame_index = self.attack_frame
        elif self.current_animation == "walk" and self.walk_frames:
            frames = self.walk_frames
            frame_index = self.animation_frame
        elif self.current_animation == "jump" and self.jump_frames:
            frames = self.jump_frames
            frame_index = self.animation_frame
        elif self.current_animation == "idle" and self.idle_frames:
            frames = self.idle_frames
            frame_index = self.animation_frame

        if not frames:
            pygame.draw.rect(screen, (255, 140, 0), camera_rect)
            return

        frame_index = max(0, min(frame_index, len(frames) - 1))
        sprite = frames[frame_index]

        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)

        # Anchor every frame at the character's feet. This prevents
        # different source-frame sizes from making the character shake.
        sprite_rect = sprite.get_rect(
            midbottom=(camera_rect.centerx, camera_rect.bottom + 14)
        )

        if self.invincible_blink and (pygame.time.get_ticks() // 90) % 2 == 0:
            ghost = sprite.copy()
            ghost.set_alpha(110)
            screen.blit(ghost, sprite_rect)
        elif self.damage_flash_timer > 0:
            flash = sprite.copy()
            flash.fill((255, 80, 80, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(flash, sprite_rect)
        else:
            screen.blit(sprite, sprite_rect)
