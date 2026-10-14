import math
import os
import pygame


from src.entities.enemy_sprites import (  # noqa: F401
    SPRITE_ENEMY_TYPES,
    SPRITE_ENEMY_CONFIG,
    ENEMY_ANIM_NAMES,
    _ENEMY_FRAME_CACHE,
    _enemy_frame_files,
    _load_enemy_animations,
)


class Enemy:

    def __init__(
        self,
        x,
        y,
        left_limit,
        right_limit,
        speed=2,
        enemy_type="slime",
        platform_top=None,
        sprite_key=None,
        sprite_scale=1.0,
    ):

        # ==========================================
        # SPRITE-DRIVEN SETUP (normal difficulty)
        # ==========================================

        self.sprite_key = sprite_key if sprite_key in SPRITE_ENEMY_TYPES else None
        self.cfg = dict(SPRITE_ENEMY_CONFIG.get(self.sprite_key, {}))
        self.anims = {}

        # ==========================================
        # POSITION
        # ==========================================

        if self.sprite_key:

            target_height = max(
                1,
                round(self.cfg.get("target_h", 60) * max(0.1, float(sprite_scale)))
            )
            self.anims = _load_enemy_animations(
                self.sprite_key,
                target_height
            )
            reference = (
                self.anims.get("idle")
                or self.anims.get("run")
                or []
            )
            if reference:
                width, height = reference[0].get_size()
            else:
                width, height = 32, 48

        elif enemy_type == "heavy":

            width = 60
            height = 60

        else:

            width = 32
            height = 32

        self.rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        # ==========================================
        # MOVEMENT
        # ==========================================

        self.speed = speed

        self.direction = 1
        # ==========================================
        # FAST ENEMY
        # ==========================================

        self.fast_timer = 0

        self.fast_burst_timer = 0

        self.fast_burst_duration = 12

        self.fast_burst_cooldown = 120

        self.fast_burst_speed = 2.2

        # ==========================================
        # HEAVY ENEMY
        # ==========================================

        self.heavy_timer = 0

        self.heavy_pause = 0

        self.heavy_pause_duration = 20

        self.heavy_move_duration = 90

        # ==========================================
        # PATROL LIMITS
        # ==========================================

        self.left_limit = left_limit

        self.right_limit = right_limit

        # ==========================================
        # TYPE
        # ==========================================

        self.enemy_type = enemy_type

        # ==========================================
        # STATE
        # ==========================================

        self.alive = True

        # Combat health: normal enemies need 3 hits.
        self.hit_points = 3
        self.max_hit_points = 3
        self.last_attack_id = -1
        self.stomp_count = 0

        # ==========================================
        # JUMPER
        # ==========================================

        self.velocity_y = 0

        self.gravity = 0.5

        self.jump_strength = -10

        self.jump_timer = 0

        self.jump_delay = 90

        self.landing_timer = 0

        self.platform_top = platform_top

        # ==========================================
        # FLYER
        # ==========================================

        self.fly_direction = 1

        self.fly_speed = 1.5

        self.fly_top = y - 40

        self.fly_bottom = y + 40

        self.fly_time = 0

        self.fly_amplitude = 25

        self.fly_center_y = y

        self.animation_timer = 0
        self.animation_offset = 0

        # ==========================================
        # SPRITE AI STATE (normal difficulty only)
        # ==========================================
        # states: patrol -> approach/chase -> attack -> hurt/dying
        self.state = "patrol"
        self.facing = 1
        self.anim_name = "run"
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 7
        self.hurt_timer = 0
        self.dying_timer = 0
        self.attack_cooldown_timer = 0
        self._fired = False
        self.pending_projectile = None
        self.pending_attack = None
        self.finished_dying = False

    # ==============================================
    # UPDATE
    # ==============================================

    def update(self, player=None, level=None):

        # Enemy animation
        self.animation_timer += 1

        if self.animation_timer >= 6:
            self.animation_timer = 0
            self.animation_offset += 1

            if self.animation_offset > 1:
                self.animation_offset = 0

        if self.sprite_key:
            self._update_sprite(player, level)
            return

        if not self.alive:
            return

        if self.enemy_type == "slime":

            self.move_horizontal()

        elif self.enemy_type == "fast":

            self.update_fast()

        elif self.enemy_type == "jumper":

            self.move_horizontal()

            self.update_jump()

        elif self.enemy_type == "flyer":

            self.move_horizontal()

            self.update_fly()

        elif self.enemy_type == "heavy":

            self.update_heavy()

    # ==============================================
    # HORIZONTAL MOVEMENT
    # ==============================================

    def move_horizontal(self):

        self.rect.x += (
            self.speed
            * self.direction
        )

        if self.rect.left <= self.left_limit:

            self.rect.left = self.left_limit

            self.direction = 1

        if self.rect.right >= self.right_limit:

            self.rect.right = self.right_limit

            self.direction = -1

    # ==============================================
    # FAST ENEMY
    # ==============================================

    def update_fast(self):

        self.fast_timer += 1

        # ------------------------------------------
        # START BURST
        # ------------------------------------------

        if (
            self.fast_burst_timer == 0
            and self.fast_timer >= self.fast_burst_cooldown
        ):

            self.fast_burst_timer = (
                self.fast_burst_duration
            )

            self.fast_timer = 0

        # ------------------------------------------
        # BURST MOVEMENT
        # ------------------------------------------

        if self.fast_burst_timer > 0:

            self.fast_burst_timer -= 1

            old_speed = self.speed

            self.speed = self.fast_burst_speed

            self.move_horizontal()

            self.speed = old_speed

        else:

            self.move_horizontal()

    # ==============================================
    # HEAVY ENEMY
    # ==============================================

    def update_heavy(self):

        # ------------------------------------------
        # PAUSE
        # ------------------------------------------

        if self.heavy_pause > 0:

            self.heavy_pause -= 1

            return

        # ------------------------------------------
        # MOVE
        # ------------------------------------------

        self.move_horizontal()

        self.heavy_timer += 1

        # ------------------------------------------
        # TAKE A BREAK
        # ------------------------------------------

        if (
            self.heavy_timer
            >= self.heavy_move_duration
        ):

            self.heavy_timer = 0

            self.heavy_pause = (
                self.heavy_pause_duration
            )

    # ==============================================
    # JUMPER
    # ==============================================

    def update_jump(self):

        # ------------------------------------------
        # LANDING PAUSE
        # ------------------------------------------

        if self.landing_timer > 0:
            self.landing_timer -= 1

            return

        # ------------------------------------------
        # JUMP TIMER
        # ------------------------------------------

        self.jump_timer += 1

        if (
                self.jump_timer >= self.jump_delay
                and abs(self.velocity_y) < 0.1
        ):
            self.velocity_y = (
                self.jump_strength
            )

            self.jump_timer = 0

        # ------------------------------------------
        # GRAVITY
        # ------------------------------------------

        self.velocity_y += self.gravity

        self.rect.y += int(
            self.velocity_y
        )

        # ------------------------------------------
        # LANDING
        # ------------------------------------------

        if self.platform_top is not None:

            if (
                    self.rect.bottom >= self.platform_top
                    and self.velocity_y > 0
            ):
                self.rect.bottom = (
                    self.platform_top
                )

                self.velocity_y = 0

                self.landing_timer = 8

    # ==============================================
    # FLYER
    # ==============================================

    def update_fly(self):

        self.fly_time += 1

        # ------------------------------------------
        # HORIZONTAL MOVEMENT
        # ------------------------------------------

        self.rect.x += (
                self.speed
                * self.direction
        )

        if self.rect.left <= self.left_limit:
            self.rect.left = self.left_limit

            self.direction = 1

        if self.rect.right >= self.right_limit:
            self.rect.right = self.right_limit

            self.direction = -1

        # ------------------------------------------
        # SMOOTH VERTICAL MOVEMENT
        # ------------------------------------------


        offset = (
                math.sin(
                    self.fly_time
                    * 0.025
                )
                * self.fly_amplitude
        )

        self.rect.centery = int(
            self.fly_center_y
            + offset
        )

    # ==============================================
    # SPRITE AI (normal difficulty enemies)
    # ==============================================
    # Shared state machine for every sprite-driven enemy type: patrol on
    # the platform like the classic enemies, notice the player once close
    # enough, then either approach-and-melee, rush-and-explode, or hold
    # ground and fire a ranged attack (bullet / dropped bomb).

    def _enter_patrol(self):
        self.state = "patrol"
        self.anim_name = "run"
        self.anim_frame = 0
        self.anim_timer = 0

    def _enter_attack(self):
        self.state = "attack"
        self.anim_name = "attack"
        self.anim_frame = 0
        self.anim_timer = 0
        self._fired = False

    def _advance_animation(self):
        frames = self.anims.get(self.anim_name) or []
        self.anim_timer += 1
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.anim_frame += 1
        return frames

    def _trigger_attack_effect(self, player, level):
        style = self.cfg.get("style")

        if style == "ranged":
            reach = max(20, self.rect.width // 2 + 6)
            spawn_x = self.rect.centerx + reach * self.facing
            spawn_y = self.rect.centery - self.rect.height * 0.12
            self.pending_projectile = {
                "kind": "bullet",
                "x": spawn_x,
                "y": spawn_y,
                "direction": self.facing,
            }

        elif style == "bomber":
            self.pending_projectile = {
                "kind": "bomb",
                "x": self.rect.centerx,
                "y": self.rect.bottom,
                "direction": self.facing,
            }

        elif style == "melee":
            # Melee enemies deal damage only on the attack animation hit
            # frame. Merely touching/overlapping the enemy is harmless.
            self.pending_attack = {
                "range": self.cfg.get("act_range", 50),
                "vertical_range": 78,
                "damage": 1,
            }

        elif style == "rush":
            # Minebot's explosion is also an attack, not a body collision.
            self.pending_attack = {
                "range": self.cfg.get("act_range", 40) + 18,
                "vertical_range": 70,
                "damage": 1,
            }
            if level is not None:
                level.create_particles(
                    self.rect.centerx,
                    self.rect.centery,
                    (255, 150, 60),
                    count=18
                )

    def _update_sprite(self, player, level):

        cfg = self.cfg
        style = cfg.get("style", "melee")

        # ------------------------------------------
        # DYING
        # ------------------------------------------
        if self.state == "dying":
            frames = self._advance_animation()
            if not frames or self.anim_frame >= len(frames) - 1:
                self.anim_frame = max(0, len(frames) - 1)
                self.dying_timer -= 1
                if self.dying_timer <= 0:
                    self.finished_dying = True
            return

        # ------------------------------------------
        # HURT (brief flinch, no control)
        # ------------------------------------------
        if self.state == "hurt":
            frames = self._advance_animation()
            if frames and self.anim_frame >= len(frames):
                self.anim_frame = len(frames) - 1
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self._enter_patrol()
            return

        if not self.alive:
            return

        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1

        detect = cfg.get("detect", 220)
        act_range = cfg.get("act_range", 50)

        dx = 0
        dist_x = 999999
        same_level = False
        if player is not None:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            dist_x = abs(dx)
            same_level = (abs(dy) < 90) or style == "bomber"

        # ------------------------------------------
        # PATROL
        # ------------------------------------------
        if self.state == "patrol":
            self.move_horizontal()
            self.anim_name = "run"
            self.facing = self.direction

            if (
                player is not None
                and same_level
                and dist_x < detect
                and self.attack_cooldown_timer <= 0
            ):
                self.facing = 1 if dx >= 0 else -1
                if style == "rush":
                    self.state = "chase"
                elif dist_x <= act_range:
                    self._enter_attack()
                else:
                    self.state = "approach"

        # ------------------------------------------
        # APPROACH (close the distance, then attack)
        # ------------------------------------------
        elif self.state == "approach":
            self.facing = 1 if dx >= 0 else -1
            self.rect.x += int(self.speed * self.facing)
            self.rect.left = max(self.rect.left, self.left_limit)
            self.rect.right = min(self.rect.right, self.right_limit)
            self.anim_name = "run"

            if player is None or not same_level or dist_x > detect * 1.3:
                self._enter_patrol()
            elif dist_x <= act_range:
                self._enter_attack()

        # ------------------------------------------
        # CHASE (minebot rush, ignores patrol bounds a little)
        # ------------------------------------------
        elif self.state == "chase":
            self.facing = 1 if dx >= 0 else -1
            chase_speed = cfg.get("chase_speed", self.speed * 2)
            self.rect.x += int(chase_speed * self.facing)
            self.anim_name = "run"

            if player is None or dist_x > detect * 1.6:
                self._enter_patrol()
            elif dist_x <= act_range:
                self._enter_attack()

        # ------------------------------------------
        # ATTACK
        # ------------------------------------------
        elif self.state == "attack":
            frames = self._advance_animation()
            self.anim_name = "attack"
            hit_frame = cfg.get("hit_frame", 2)

            if not self._fired and self.anim_frame >= hit_frame:
                self._fired = True
                self._trigger_attack_effect(player, level)

            if not frames or self.anim_frame >= len(frames):
                if style == "rush":
                    # Self-destructs after its blast animation finishes.
                    self.alive = False
                    self.state = "dying"
                    self.anim_name = "death"
                    self.anim_frame = 0
                    self.anim_timer = 0
                    self.dying_timer = 30
                else:
                    self.attack_cooldown_timer = cfg.get("cooldown", 60)
                    self._enter_patrol()
            return

        # Keep ground/flyer patrol enemies inside their platform bounds.
        if style != "rush":
            if self.rect.left < self.left_limit:
                self.rect.left = self.left_limit
            if self.rect.right > self.right_limit:
                self.rect.right = self.right_limit

        # Advance whichever locomotion animation is currently playing.
        if self.state in ("patrol", "approach", "chase"):
            self._advance_animation()

    # ==============================================
    # COMBAT
    # ==============================================

    def take_hit(self, attack_id=None):
        # Prevent the same attack animation from damaging this
        # enemy more than once.
        if attack_id is not None:
            if self.last_attack_id == attack_id:
                return False
            self.last_attack_id = attack_id

        self.hit_points -= 1

        if self.hit_points <= 0:
            self.alive = False
            if self.sprite_key:
                self.state = "dying"
                self.anim_name = "death"
                self.anim_frame = 0
                self.anim_timer = 0
                self.dying_timer = 30
            return True

        if self.sprite_key:
            self.state = "hurt"
            self.anim_name = "hurt"
            self.anim_frame = 0
            self.anim_timer = 0
            self.hurt_timer = 14

        return False

    def stomp(self):
        self.stomp_count += 1
        defeated = self.stomp_count >= 3

        if defeated:
            self.alive = False
            if self.sprite_key:
                self.state = "dying"
                self.anim_name = "death"
                self.anim_frame = 0
                self.anim_timer = 0
                self.dying_timer = 30
        elif self.sprite_key:
            self.state = "hurt"
            self.anim_name = "hurt"
            self.anim_frame = 0
            self.anim_timer = 0
            self.hurt_timer = 10

        return defeated

    # ==============================================
    # PLAYER COLLISION
    # ==============================================

    def check_collision(self, player):

        if not self.alive:
            return False

        return self.rect.colliderect(
            player.rect
        )

    # ==============================================
    # SPRITE DRAW
    # ==============================================

    def _draw_sprite(self, screen, camera):

        if not self.alive:
            if self.state != "dying" or self.finished_dying:
                return

        frames = self.anims.get(self.anim_name) or self.anims.get("idle") or []
        if not frames:
            return

        frame_index = min(self.anim_frame, len(frames) - 1)
        image = frames[frame_index]

        if self.facing < 0:
            image = pygame.transform.flip(image, True, False)

        # Hover bob for the flying chopper so it never looks static.
        bob = 0
        if self.cfg.get("style") == "bomber" and self.state != "dying":
            bob = int(math.sin(pygame.time.get_ticks() * 0.006 + self.rect.x) * 4)

        camera_rect = camera.apply(self.rect)

        draw_x = camera_rect.centerx - image.get_width() // 2
        draw_y = camera_rect.bottom - image.get_height() + bob

        # Brief white flash while hurt for extra readability.
        if self.state == "hurt" and (self.hurt_timer // 3) % 2 == 0:
            flash = image.copy()
            tint = pygame.Surface(image.get_size(), pygame.SRCALPHA)
            tint.fill((255, 255, 255, 130))
            flash.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            image = flash

        # Fade out during the last stretch of the death animation.
        if self.state == "dying" and self.dying_timer < 12:
            alpha = max(0, int(255 * (self.dying_timer / 12)))
            image = image.copy()
            image.set_alpha(alpha)

        screen.blit(image, (draw_x, draw_y))

    def draw(self, screen, camera):

        if self.sprite_key:
            self._draw_sprite(screen, camera)
            return

        if not self.alive:
            return

        camera_rect = camera.apply(
            self.rect
        )

        # Small bobbing animation
        draw_rect = camera_rect.copy()

        if self.animation_offset == 1:
            draw_rect.y -= 3

        # ==========================================
        # BODY COLOR
        # ==========================================

        if self.enemy_type == "fast":

            body_color = (
                220,
                70,
                70
            )

        elif self.enemy_type == "jumper":

            body_color = (
                220,
                190,
                50
            )

        elif self.enemy_type == "flyer":

            body_color = (
                60,
                150,
                210
            )


        elif self.enemy_type == "heavy":
            body_color = (
                40,
                40,
                40
            )

        else:

            body_color = (
                120,
                70,
                190
            )

        # ==========================================
        # HEAVY BODY
        # ==========================================

        if self.enemy_type == "heavy":

            pygame.draw.rect(
                screen,
                body_color,
                draw_rect,
                border_radius=8
            )

        else:

            pygame.draw.ellipse(
                screen,
                body_color,
                draw_rect
            )

        # ==========================================
        # FLYER WINGS
        # ==========================================

        if self.enemy_type == "flyer":

            left_wing = pygame.Rect(
                camera_rect.x - 10,
                camera_rect.y + 10,
                15,
                20
            )

            right_wing = pygame.Rect(
                camera_rect.right - 5,
                camera_rect.y + 10,
                15,
                20
            )

            pygame.draw.ellipse(
                screen,
                body_color,
                left_wing
            )

            pygame.draw.ellipse(
                screen,
                body_color,
                right_wing
            )

        # ==========================================
        # EYES
        # ==========================================

        eye_y = (
            camera_rect.y
            + camera_rect.height // 3
        )

        left_eye = (
            camera_rect.x
            + camera_rect.width // 3,
            eye_y
        )

        right_eye = (
            camera_rect.x
            + (camera_rect.width * 2) // 3,
            eye_y
        )

        eye_size = 6

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            left_eye,
            eye_size
        )

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            right_eye,
            eye_size
        )

        pygame.draw.circle(
            screen,
            (0, 0, 0),
            left_eye,
            3
        )

        pygame.draw.circle(
            screen,
            (0, 0, 0),
            right_eye,
            3
        )

