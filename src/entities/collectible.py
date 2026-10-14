import pygame


class Collectible:

    def __init__(self, x, y, size=24, value=10, animation_frames=None):
        self.rect = pygame.Rect(x, y, size, size)
        self.value = value
        self.collected = False
        self.animation_frames = tuple(animation_frames or ())
        self.animation_frame = 0
        self.animation_timer = 0

    def collect(self):
        self.collected = True

    def update(self, player):
        if self.collected:
            return

        if self.rect.colliderect(player.rect):
            self.collected = True

    def draw(self, screen, camera):
        if self.collected:
            return

        screen_rect = camera.apply(self.rect)

        if self.animation_frames:
            self.animation_timer += 1
            if self.animation_timer >= 4:
                self.animation_timer = 0
                self.animation_frame = (
                    self.animation_frame + 1
                ) % len(self.animation_frames)

            frame = self.animation_frames[self.animation_frame]
            frame_rect = frame.get_rect(center=screen_rect.center)
            screen.blit(frame, frame_rect)
            return

        pygame.draw.circle(
            screen,
            (255, 170, 40),
            screen_rect.center,
            self.rect.width // 2
        )

        pygame.draw.circle(
            screen,
            (255, 220, 80),
            (
                screen_rect.centerx - 4,
                screen_rect.centery - 4
            ),
            4
        )
