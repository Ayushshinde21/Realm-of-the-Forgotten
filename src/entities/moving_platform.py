import pygame

from src.entities.platform import Platform


class MovingPlatform(Platform):

    def __init__(
        self,
        x,
        y,
        width,
        height=20,
        movement_type="horizontal",
        movement_distance=120,
        movement_speed=1.0,
        movement_min_offset=None,
        movement_max_offset=None
    ):

        super().__init__(
            x,
            y,
            width,
            height
        )

        # ==========================================
        # MOVEMENT SETTINGS
        # ==========================================

        self.movement_type = movement_type
        self.movement_distance = movement_distance
        self.movement_speed = movement_speed
        self.movement_min_offset = (
            -abs(float(movement_distance))
            if movement_min_offset is None
            else float(movement_min_offset)
        )
        self.movement_max_offset = (
            abs(float(movement_distance))
            if movement_max_offset is None
            else float(movement_max_offset)
        )
        if self.movement_min_offset > self.movement_max_offset:
            raise ValueError("movement_min_offset must not exceed movement_max_offset")

        # ==========================================
        # ORIGINAL POSITION
        # ==========================================

        self.start_x = x
        self.start_y = y
        self.previous_x = x
        self.previous_y = y

        # ==========================================
        # DIRECTION
        # ==========================================

        self.direction = 1

        # ==========================================
        # OFFSET
        # ==========================================

        self.offset = 0.0
        self.previous_x = self.rect.x
        self.previous_y = self.rect.y

    # ==============================================
    # UPDATE
    # ==============================================

    def update(self):

        self.previous_x = self.rect.x
        self.previous_y = self.rect.y

        self.offset += self.movement_speed * self.direction

        if self.offset >= self.movement_max_offset:
            self.offset = self.movement_max_offset
            self.direction = -1
        elif self.offset <= self.movement_min_offset:
            self.offset = self.movement_min_offset
            self.direction = 1

        if self.movement_type == "horizontal":
            self.rect.x = int(self.start_x + self.offset)
            self.rect.y = self.start_y
        elif self.movement_type == "vertical":
            self.rect.y = int(self.start_y + self.offset)
            self.rect.x = self.start_x

    # ==============================================
    # DRAW
    # ==============================================

    def draw(self, screen, camera):

        camera_rect = camera.apply(
            self.rect
        )

        # Platform body

        pygame.draw.rect(
            screen,
            (90, 90, 100),
            camera_rect
        )

        # Platform top

        pygame.draw.rect(
            screen,
            (180, 190, 200),
            (
                camera_rect.x,
                camera_rect.y,
                camera_rect.width,
                5
            )
        )