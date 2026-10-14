import os
import pygame


class Bush:

    SLOW = "slow"
    FAST = "fast"
    POISON = "poison"

    _image = None

    def __init__(
        self,
        x,
        ground_top,
        bush_type="slow",
        width=34,
        height=36,
        variant=0,
        platform=None
    ):
        self.bush_type = bush_type
        self.variant = variant % 5
        self.platform = platform

        # Keep the existing small collision area for gameplay.
        # The supplied bush image is only the visual representation.
        self.rect = pygame.Rect(
            int(x),
            int(ground_top - height),
            int(width),
            int(height),
        )

        self.active = True
        self.triggered = False

        self._load_image()

    @classmethod
    def _load_image(cls):
        if cls._image is not None:
            return

        path = os.path.join(
            "assets",
            "bushes",
            "bush.png"
        )

        try:
            cls._image = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            cls._image = None

    def reset_trigger(self):
        self.triggered = False

    def draw(self, screen, camera):
        if not self.active:
            return

        self._load_image()

        if self._image is None:
            return

        # The collision rect stays small, while the bush is drawn larger
        # so it looks like the supplied pixel-art bush.
        if self.platform is not None:
            platform_rect = camera.apply(self.platform.rect)
            center_x = platform_rect.centerx
            ground_y = platform_rect.top
            visual_width = max(
                38,
                min(40, int(platform_rect.width * 0.72))
            )
        else:
            bush_rect = camera.apply(self.rect)
            center_x = bush_rect.centerx
            ground_y = bush_rect.bottom
            visual_width = max(38, self.rect.width * 3)

        source_width, source_height = self._image.get_size()
        visual_height = max(
            1,
            int(visual_width * source_height / source_width)
        )

        image = pygame.transform.smoothscale(
            self._image,
            (visual_width, visual_height)
        )

        image_rect = image.get_rect(
            midbottom=(int(center_x), int(ground_y))
        )

        screen.blit(image, image_rect)
