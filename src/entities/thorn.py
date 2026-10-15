import os
import pygame


class ThornHazard:
    """Animated thorn patch that slows and damages a player on contact."""

    _frames = None
    _scaled_frame_cache = {}
    FRAME_COUNT = 8
    FRAME_CROP_TOP = 285
    FRAME_CROP_BOTTOM = 420

    WIDTH_SCALE = 1.8
    SPRITE_HEIGHT = 70
    VISIBLE_ABOVE_GROUND_RATIO = 0.5
    TILE_OVERLAP_RATIO = 0.18

    def __init__(self, x, floor_y, width):
        width = max(1, int(width))
        floor_y = int(floor_y)
        expanded_width = max(width, round(width * self.WIDTH_SCALE))
        left = int(x) - (expanded_width - width) // 2
        visible_height = round(self.SPRITE_HEIGHT * self.VISIBLE_ABOVE_GROUND_RATIO)
        self.rect = pygame.Rect(
            left,
            floor_y - visible_height,
            expanded_width,
            self.SPRITE_HEIGHT,
        )
        self.hitbox = pygame.Rect(
            left + 5,
            floor_y - visible_height,
            max(1, expanded_width - 10),
            visible_height + 1,
        )
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_duration = 6

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return cls._frames

        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(__file__))
        )
        image_path = os.path.join(
            project_root,
            "assets",
            "obstacles",
            "thorns_strip.png",
        )

        try:
            strip = pygame.image.load(image_path)
        except (pygame.error, FileNotFoundError):
            cls._frames = ()
            return cls._frames

        frame_width = strip.get_width() // cls.FRAME_COUNT
        top = min(cls.FRAME_CROP_TOP, strip.get_height() - 1)
        bottom = min(cls.FRAME_CROP_BOTTOM, strip.get_height())
        frames = []
        for index in range(cls.FRAME_COUNT):
            frame_rect = pygame.Rect(
                index * frame_width,
                top,
                frame_width,
                max(1, bottom - top),
            )
            frames.append(strip.subsurface(frame_rect).copy())

        cls._frames = tuple(frames)
        return cls._frames

    def update(self):
        self.frame_timer += 1
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % self.FRAME_COUNT

    def draw(self, screen, camera):
        screen_rect = camera.apply(self.rect)
        frames = self._load_frames()

        if frames:
            frame = frames[self.frame_index]
            tile_width = max(
                1,
                round(screen_rect.height * frame.get_width() / frame.get_height()),
            )
            cache_key = (self.frame_index, tile_width, screen_rect.height)
            image = self._scaled_frame_cache.get(cache_key)
            if image is None:
                image = pygame.transform.scale(
                    frame,
                    (tile_width, screen_rect.height),
                )
                self._scaled_frame_cache[cache_key] = image

            previous_clip = screen.get_clip()
            screen.set_clip(previous_clip.clip(screen_rect))
            stride = max(
                1,
                round(tile_width * (1.0 - self.TILE_OVERLAP_RATIO)),
            )
            tile_x = screen_rect.left
            while tile_x < screen_rect.right:
                screen.blit(image, (tile_x, screen_rect.top))
                tile_x += stride
            screen.set_clip(previous_clip)
            return

        # Readable fallback if the image asset is missing.
        ground_y = screen_rect.top + round(
            screen_rect.height * self.VISIBLE_ABOVE_GROUND_RATIO
        )
        base = pygame.Rect(
            screen_rect.x,
            ground_y - 4,
            screen_rect.width,
            screen_rect.bottom - ground_y + 4,
        )
        pygame.draw.rect(screen, (35, 57, 28), base)
        step = 18
        for x in range(screen_rect.left, screen_rect.right, step):
            pygame.draw.polygon(
                screen,
                (83, 112, 42),
                [(x, ground_y), (x + step // 2, ground_y - 28), (x + step, ground_y)],
            )
