import pygame


class Projectile:
    """A simple thrown/fired enemy attack.

    kind="bomb": affected by gravity, arcs downward (dropped by flyers).
    kind="bullet": travels in a straight horizontal line, no gravity.
    """

    def __init__(self, x, y, kind="bullet", direction=1, damage=1, vx=None):

        self.kind = kind
        self.direction = direction
        self.damage = damage
        self.alive = True
        self.life = 0
        self.max_life = 240

        if kind == "bomb":
            width, height = 14, 18
            self.vx = 0.6 * direction if vx is None else vx
            self.vy = 0.5
            self.gravity = 0.35
            self.max_fall_speed = 9
        else:
            width, height = 16, 6
            self.vx = 7.5 * direction if vx is None else vx
            self.vy = 0
            self.gravity = 0
            self.max_fall_speed = 0

        self.rect = pygame.Rect(
            int(x - width / 2),
            int(y - height / 2),
            width,
            height
        )

        self.spin = 0

    # ==============================================
    # UPDATE
    # ==============================================

    def update(self, platforms=None, world_width=None):

        if not self.alive:
            return

        self.life += 1
        if self.life > self.max_life:
            self.alive = False
            return

        if self.gravity:
            self.vy = min(self.max_fall_speed, self.vy + self.gravity)

        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

        self.spin += 14

        # Off-world cleanup
        if world_width is not None and (self.rect.right < -50 or self.rect.left > world_width + 50):
            self.alive = False
            return

        if self.rect.top > 2000:
            self.alive = False
            return

        # Land on / hit a platform -> explode (bomb) or stop (bullet)
        if platforms:
            for platform in platforms:
                if self.rect.colliderect(platform.rect):
                    self.alive = False
                    return

    # ==============================================
    # COLLISION
    # ==============================================

    def check_collision(self, player):
        if not self.alive:
            return False
        return self.rect.colliderect(player.rect)

    # ==============================================
    # DRAW
    # ==============================================

    def draw(self, screen, camera):

        rect = camera.apply(self.rect)

        if self.kind == "bomb":
            pygame.draw.ellipse(screen, (35, 35, 40), rect)
            pygame.draw.ellipse(screen, (90, 95, 105), rect.inflate(-5, -6))
            fuse_x = rect.centerx
            fuse_top = rect.top - 5
            pygame.draw.line(screen, (200, 160, 90), (fuse_x, rect.top), (fuse_x + 3, fuse_top), 2)
            pygame.draw.circle(screen, (255, 190, 70), (fuse_x + 3, fuse_top), 2)
        else:
            glow = pygame.Surface((rect.width + 6, rect.height + 6), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 210, 90, 120), glow.get_rect())
            screen.blit(glow, (rect.x - 3, rect.y - 3))
            pygame.draw.ellipse(screen, (255, 235, 150), rect)
            pygame.draw.ellipse(screen, (255, 140, 40), rect.inflate(-4, -2))
