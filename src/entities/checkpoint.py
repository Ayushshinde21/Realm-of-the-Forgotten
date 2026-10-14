import os
import pygame


class Checkpoint:

    def __init__(self, x, y, checkpoint_id=0):
        self.x = x
        self.y = y
        self.checkpoint_id = checkpoint_id

        self.respawn_x = x
        self.respawn_y = y - 60

        # Keep the existing, forgiving player collision area unchanged.
        self.rect = pygame.Rect(x, y - 50, 20, 50)
        self.activated = False

        # An unchecked checkpoint waves red; once activated, it waves green.
        # Asset paths are resolved from the project root, not the shell CWD.
        self.red_frames = self._load_animation_frames("red")
        self.green_frames = self._load_animation_frames("green")
        self.red_fallback = self._load_fallback_image("red")
        self.green_fallback = self._load_fallback_image("green")

        # Legacy frame paths remain as a fallback for older installations.
        self.legacy_frames = self._load_legacy_animation_frames()
        self.legacy_fallback = self._load_legacy_fallback_image()
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_interval = 8

    def _project_root(self):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _load_image(self, path, size=(50, 84)):
        try:
            image = pygame.image.load(path)
            if pygame.display.get_surface() is not None:
                image = image.convert_alpha()
            return pygame.transform.scale(image, size)
        except (pygame.error, FileNotFoundError, OSError):
            return None

    def _load_animation_frames(self, color):
        frames = []
        frames_dir = os.path.join(
            self._project_root(), "assets", "checkpoints", color, "frames"
        )
        for frame_number in range(1, 9):
            path = os.path.join(frames_dir, f"checkpoint_{frame_number:02d}.png")
            image = self._load_image(path)
            if image is not None:
                frames.append(image)
        return frames

    def _load_fallback_image(self, color):
        path = os.path.join(
            self._project_root(), "assets", "checkpoints", color, "checkpoint.png"
        )
        return self._load_image(path)

    def _load_legacy_animation_frames(self):
        frames = []
        frames_dir = os.path.join(self._project_root(), "assets", "checkpoints", "frames")
        for frame_number in range(1, 9):
            path = os.path.join(frames_dir, f"checkpoint_{frame_number:02d}.png")
            image = self._load_image(path)
            if image is not None:
                frames.append(image)
        return frames

    def _load_legacy_fallback_image(self):
        path = os.path.join(self._project_root(), "assets", "ui", "checkpoint.png")
        return self._load_image(path)

    def _current_frames(self):
        if self.activated:
            return self.green_frames or self.red_frames or self.legacy_frames
        return self.red_frames or self.green_frames or self.legacy_frames

    def _current_fallback(self):
        if self.activated:
            return self.green_fallback or self.red_fallback or self.legacy_fallback
        return self.red_fallback or self.green_fallback or self.legacy_fallback

    def update(self, player):
        # Both flag colors use the same eight-frame timing. The selected color
        # switches immediately on activation and remains green thereafter.
        frames = self._current_frames()
        if frames:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_interval:
                self.animation_timer = 0
                self.animation_frame = (self.animation_frame + 1) % len(frames)

        if self.activated:
            return

        if self.rect.colliderect(player.rect):
            self.activated = True
            self.animation_frame = 0
            self.animation_timer = 0

    def draw(self, screen, camera):
        screen_rect = camera.apply(self.rect)
        frames = self._current_frames()
        if frames:
            image = frames[self.animation_frame % len(frames)]
        else:
            image = self._current_fallback()

        if image is not None:
            image_rect = image.get_rect()
            image_rect.midbottom = (screen_rect.centerx, screen_rect.bottom + 2)
            screen.blit(image, image_rect)
            return

        # Last-resort primitive fallback if no image assets are available.
        pygame.draw.rect(screen, (80, 80, 80), screen_rect)
        flag_color = (80, 200, 80) if self.activated else (200, 80, 80)
        pygame.draw.polygon(
            screen,
            flag_color,
            [
                (screen_rect.right, screen_rect.top),
                (screen_rect.right + 25, screen_rect.top + 10),
                (screen_rect.right, screen_rect.top + 20),
            ],
        )
