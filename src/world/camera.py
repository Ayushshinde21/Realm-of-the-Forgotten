import pygame

from src.settings import (
    WIDTH,
    HEIGHT,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    CAMERA_SMOOTHNESS,
    CAMERA_DEADZONE_X,
    CAMERA_DEADZONE_Y,
)


class Camera:
    """
    Two-axis camera: smoothly follows the target on both X and Y,
    using a dead zone so small movements/jumps don't constantly nudge
    the camera, and clamps to the world bounds on both axes.
    """

    def __init__(self):

        self.x = 0.0
        self.y = 0.0

        # Where the camera is currently "aiming" (focus point). This is
        # what the dead zone is measured against, and it only moves once
        # the target leaves the dead zone - not every frame.
        self.focus_x = WIDTH // 2
        self.focus_y = HEIGHT // 2

    def update(self, target):

        target_x = target.rect.centerx
        target_y = target.rect.centery

        # ==========================================
        # DEAD ZONE
        # ==========================================
        # Only move the focus point once the target has moved far
        # enough away from it - prevents constant tiny adjustments
        # while standing still or making small jumps.

        if target_x > self.focus_x + CAMERA_DEADZONE_X:
            self.focus_x = target_x - CAMERA_DEADZONE_X
        elif target_x < self.focus_x - CAMERA_DEADZONE_X:
            self.focus_x = target_x + CAMERA_DEADZONE_X

        if target_y > self.focus_y + CAMERA_DEADZONE_Y:
            self.focus_y = target_y - CAMERA_DEADZONE_Y
        elif target_y < self.focus_y - CAMERA_DEADZONE_Y:
            self.focus_y = target_y + CAMERA_DEADZONE_Y

        # ==========================================
        # SMOOTH FOLLOW
        # ==========================================

        target_camera_x = self.focus_x - WIDTH / 2
        target_camera_y = self.focus_y - HEIGHT / 2

        self.x += (target_camera_x - self.x) * CAMERA_SMOOTHNESS
        self.y += (target_camera_y - self.y) * CAMERA_SMOOTHNESS

        # ==========================================
        # WORLD BOUNDS
        # ==========================================

        world_width = getattr(self, "world_width", WORLD_WIDTH)
        max_camera_x = max(0, world_width - WIDTH)
        if self.x < 0:
            self.x = 0
        elif self.x > max_camera_x:
            self.x = max_camera_x

        if WORLD_HEIGHT <= HEIGHT:
            # World shorter than the screen: keep it fixed/centered
            # instead of producing a negative offset.
            self.y = -(HEIGHT - WORLD_HEIGHT) / 2
        else:
            max_camera_y = WORLD_HEIGHT - HEIGHT
            if self.y < 0:
                self.y = 0
            elif self.y > max_camera_y:
                self.y = max_camera_y

    def apply(self, rect):

        return pygame.Rect(
            rect.x - int(self.x),
            rect.y - int(self.y),
            rect.width,
            rect.height
        )
