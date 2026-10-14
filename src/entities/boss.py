"""Asset-backed bosses used only in Easy difficulty levels 5 and 10."""
from __future__ import annotations

import os
import pygame

_BOSS_ANIMATION_CACHE = {}
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

_ORC_VARIANTS = {
    "orc_berserk": {"folder": "orc_berserk", "frame_size": 96, "hit_frame": 2},
    "orc_shaman": {"folder": "orc_shaman", "frame_size": 96, "hit_frame": 2},
    "orc_warrior": {"folder": "orc_warrior", "frame_size": 96, "hit_frame": 3},
}
_YOKAI_VARIANTS = {
    "karasu_tengu": {"folder": "karasu_tengu", "frame_size": 128, "hit_frame": 3},
    "kitsune": {"folder": "kitsune", "frame_size": 128, "hit_frame": 6},
    "yamabushi_tengu": {"folder": "yamabushi_tengu", "frame_size": 128, "hit_frame": 1},
}
_SHEETS = {
    "idle": "Idle.png",
    "run": "Run.png",
    "attack": "Attack_1.png",
    "hurt": "Hurt.png",
    "death": "Dead.png",
}


def _load_boss_animations(boss_kind: str, variant: str, target_height: int):
    cache_key = (boss_kind, variant, target_height)
    if cache_key in _BOSS_ANIMATION_CACHE:
        return _BOSS_ANIMATION_CACHE[cache_key]

    variants = _ORC_VARIANTS if boss_kind == "orc" else _YOKAI_VARIANTS
    config = variants[variant]
    folder = os.path.join(
        _PROJECT_ROOT,
        "assets",
        "bosses",
        "orcs" if boss_kind == "orc" else "yokai",
        config["folder"],
    )
    frame_size = config["frame_size"]
    scale = target_height / frame_size
    animations = {}

    for anim_name, filename in _SHEETS.items():
        sheet_path = os.path.join(folder, filename)
        frames = []
        try:
            sheet = pygame.image.load(sheet_path).convert_alpha()
            frame_count = max(1, sheet.get_width() // frame_size)
            for index in range(frame_count):
                frame_rect = pygame.Rect(index * frame_size, 0, frame_size, frame_size)
                frame = sheet.subsurface(frame_rect).copy()
                frame_width = max(1, round(frame_size * scale))
                frame_height = max(1, round(frame_size * scale))
                frames.append(pygame.transform.scale(frame, (frame_width, frame_height)))
        except (pygame.error, OSError, FileNotFoundError):
            frames = []
        animations[anim_name] = frames

    _BOSS_ANIMATION_CACHE[cache_key] = animations
    return animations


class Boss:
    """A single arena boss with independent HP, animations, and melee AI."""

    def __init__(
        self,
        boss_kind: str,
        variant: str,
        center_x: int,
        floor_y: int,
        left_limit: int,
        right_limit: int,
        hit_points: int,
        target_height: int,
    ):
        self.boss_kind = boss_kind
        self.variant = variant
        self.display_name = "ORC BOSS" if boss_kind == "orc" else "YOKAI BOSS"
        self.anims = _load_boss_animations(boss_kind, variant, target_height)
        reference = self.anims.get("idle") or self.anims.get("run") or []
        if reference:
            width, height = reference[0].get_size()
            visible_bounds = reference[0].get_bounding_rect(min_alpha=1)
            if visible_bounds.width <= 0 or visible_bounds.height <= 0:
                visible_bounds = pygame.Rect(0, 0, width, height)
        else:
            width = height = target_height
            visible_bounds = pygame.Rect(0, 0, width, height)

        self.rect = pygame.Rect(0, 0, width, height)
        self.floor_y = int(floor_y)
        self.body_bounds = visible_bounds.copy()
        self.body_rect = pygame.Rect(0, 0, visible_bounds.width, visible_bounds.height)
        self.pos_x = float(center_x)
        self.left_limit = int(left_limit)
        self.right_limit = int(right_limit)
        self.speed = 5.1 if boss_kind == "orc" else 5.7
        # Keep the boss damage zone shorter than the player's 62px sword reach,
        # so the player can safely get into striking distance before being hit.
        self.attack_range = 42 if boss_kind == "orc" else 48
        self.attack_vertical_range = 72 if boss_kind == "orc" else 80
        self.attack_cooldown_max = 54 if boss_kind == "orc" else 45
        self.attack_cooldown_timer = 18
        self.attack_damage = 1
        config = (_ORC_VARIANTS if boss_kind == "orc" else _YOKAI_VARIANTS)[variant]
        self.hit_frame = int(config["hit_frame"])

        self.hit_points = int(hit_points)
        self.max_hit_points = int(hit_points)
        self.last_attack_id = -1
        self.alive = True
        self.facing = -1
        self.direction = -1
        self.state = "idle"
        self.anim_name = "idle"
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 6 if boss_kind == "orc" else 5
        self.hurt_timer = 0
        self.pending_attack = None
        self.pending_projectile = None
        self.attack_fired = False
        self.finished_dying = False
        self._hurt_frame = 0
        self._sync_position()

    def _sync_position(self):
        """Keep the visible body anchored while the full sprite frame flips."""
        bounds = self.body_bounds
        if self.facing < 0:
            body_left = self.rect.width - bounds.right
        else:
            body_left = bounds.left
        body_center_offset = body_left + bounds.width / 2
        self.rect.x = round(self.pos_x - body_center_offset)
        self.rect.bottom = self.floor_y
        self.body_rect = pygame.Rect(
            self.rect.left + body_left,
            self.rect.top + bounds.top,
            bounds.width,
            bounds.height,
        )

    def _frames(self):
        return self.anims.get(self.anim_name) or self.anims.get("idle") or []

    def _set_animation(self, name, reset=True):
        self.anim_name = name
        if reset:
            self.anim_frame = 0
            self.anim_timer = 0

    def _advance(self, loop=False):
        frames = self._frames()
        if not frames:
            return True

        self.anim_timer += 1
        if self.anim_timer < self.anim_speed:
            return False
        self.anim_timer = 0

        if loop:
            self.anim_frame = (self.anim_frame + 1) % len(frames)
            return False

        if self.anim_frame < len(frames) - 1:
            self.anim_frame += 1
            return False

        return True

    def update(self, player=None, level=None):
        self.pending_attack = None
        self.pending_projectile = None

        if self.state == "dying":
            if self._advance(loop=False):
                self.finished_dying = True
            return

        if self.state == "hurt":
            if self._advance(loop=False):
                self.state = "idle"
                self._set_animation("idle")
            return

        if not self.alive:
            return

        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1

        if player is None:
            self.state = "idle"
            self._set_animation("idle", reset=False)
            self._advance(loop=True)
            self._sync_position()
            return

        dx = player.rect.centerx - self.body_rect.centerx
        if self.state != "attack" and abs(dx) > 20:
            self.facing = 1 if dx > 0 else -1
            self.direction = self.facing
        self._sync_position()

        dx = player.rect.centerx - self.body_rect.centerx
        vertical_distance = abs(player.rect.centery - self.body_rect.centery)
        reach = self.body_rect.width // 2 + self.attack_range + player.rect.width // 2

        if self.state == "attack":
            frames = self._frames()
            finished = self._advance(loop=False)
            hit_frame = max(0, min(len(frames) - 1, self.hit_frame)) if frames else 0
            if not self.attack_fired and self.anim_frame >= hit_frame:
                self.pending_attack = {
                    "range": self.attack_range,
                    "vertical_range": self.attack_vertical_range,
                    "damage": self.attack_damage,
                }
                self.attack_fired = True
            if finished:
                self.state = "idle"
                self._set_animation("idle")
                self.attack_cooldown_timer = self.attack_cooldown_max
            return

        if abs(dx) > reach or vertical_distance > 135:
            self.state = "run"
            self._set_animation("run", reset=self.anim_name != "run")
            self.pos_x += self.speed * self.direction
            half_body = self.body_rect.width / 2
            self.pos_x = max(self.left_limit + half_body, min(self.right_limit - half_body, self.pos_x))
            self._sync_position()
            self._advance(loop=True)
            return

        if self.attack_cooldown_timer <= 0:
            self.state = "attack"
            self._set_animation("attack")
            self.attack_fired = False
            self._advance(loop=False)
        else:
            self.state = "idle"
            self._set_animation("idle", reset=self.anim_name != "idle")
            self._advance(loop=True)

    def take_hit(self, attack_id=None):
        if not self.alive:
            return False
        if attack_id is not None:
            if self.last_attack_id == attack_id:
                return False
            self.last_attack_id = attack_id

        interrupted_attack = self.state == "attack"
        if interrupted_attack:
            self.attack_cooldown_timer = self.attack_cooldown_max

        self.hit_points = max(0, self.hit_points - 1)
        if self.hit_points <= 0:
            self.alive = False
            self.state = "dying"
            self._set_animation("death")
            self.finished_dying = not bool(self._frames())
            return True

        self.state = "hurt"
        self._set_animation("hurt")
        if not self._frames():
            self.state = "idle"
            self._set_animation("idle")
        return False

    def draw(self, screen, camera):
        if self.finished_dying:
            frames = self.anims.get("death") or self.anims.get("idle") or []
        else:
            frames = self._frames()
        if not frames:
            camera_rect = camera.apply(self.rect)
            pygame.draw.rect(screen, (120, 50, 50), camera_rect)
            return

        frame_index = max(0, min(self.anim_frame, len(frames) - 1))
        image = frames[frame_index]
        if self.facing < 0:
            image = pygame.transform.flip(image, True, False)
        camera_rect = camera.apply(self.rect)
        draw_x = camera_rect.left
        draw_y = camera_rect.bottom - image.get_height()

        if self.state == "hurt" and (self.anim_timer // 2) % 2 == 0:
            image = image.copy()
            overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 110))
            image.blit(overlay, (0, 0))

        if self.state == "dying" and not self.finished_dying:
            image = image.copy()
            alpha = min(255, max(90, int(255 * (self.anim_frame + 1) / max(1, len(frames)))))
            image.set_alpha(alpha)

        screen.blit(image, (draw_x, draw_y))
