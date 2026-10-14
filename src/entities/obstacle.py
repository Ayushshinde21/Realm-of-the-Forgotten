import pygame


class Obstacle:

    _rock_image = None

    def __init__(
        self,
        x,
        y,
        width=30,
        height=40,
        obstacle_type="rock"
    ):
        self.rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        self.obstacle_type = obstacle_type
        self.active = True

        if self.obstacle_type == "rock" and Obstacle._rock_image is None:
            try:
                Obstacle._rock_image = pygame.image.load(
                    "assets/obstacles/rock.png"
                ).convert_alpha()
            except (pygame.error, FileNotFoundError):
                Obstacle._rock_image = None

    def check_collision(self, player):

        if not self.active:
            return False

        return self.rect.colliderect(
            player.rect
        )

    def draw(self, screen, camera):

        if not self.active:
            return

        camera_rect = camera.apply(
            self.rect
        )

        if self.obstacle_type == "rock":

            if Obstacle._rock_image is not None:

                visual_width = max(70, int(camera_rect.width * 1.8))
                visual_height = int(
                    Obstacle._rock_image.get_height()
                    * visual_width
                    / Obstacle._rock_image.get_width()
                )

                rock_image = pygame.transform.scale(
                    Obstacle._rock_image,
                    (visual_width, visual_height)
                )

                image_rect = rock_image.get_rect(
                    midbottom=(
                        camera_rect.centerx,
                        camera_rect.bottom + 4
                    )
                )

                screen.blit(
                    rock_image,
                    image_rect
                )

            else:
                pygame.draw.ellipse(
                    screen,
                    (90, 90, 90),
                    camera_rect
                )
