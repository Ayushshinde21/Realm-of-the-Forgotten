"""Regression coverage for Normal-only procedural level generation fixes."""
import random
from pathlib import Path

import pytest

pygame = pytest.importorskip("pygame")

from src.settings import MAX_LEVELS, WORLD_HEIGHT
from src.world.level import Level
from src.world.level_data import LEVELS
from src.world.platform_generator import PlatformGenerator


@pytest.fixture(scope="module", autouse=True)
def pygame_display():
    pygame.init()
    pygame.display.set_mode((1280, 720))
    yield
    pygame.quit()


@pytest.mark.parametrize("level_number", range(11, MAX_LEVELS + 1))
def test_world_two_platform_generation_succeeds_for_200_seeds(level_number):
    """Stress World 2's platform generation for all ten campaign levels."""
    world_level = level_number - 10
    width = LEVELS["normal"][world_level]["world_width"]
    progress = (level_number - 1) / max(1, MAX_LEVELS - 1)
    generator = PlatformGenerator(width, world_height=WORLD_HEIGHT)
    generator.platform_size_multiplier = 2.0
    generator.base_difficulty = 0.5 + progress * 1.9
    generator.safe_start_zone_width = 300

    for seed in range(200):
        random.seed(seed)
        platforms = generator.generate()
        assert platforms
        assert all(
            generator.get_platform_settings(generator.get_difficulty(platform.rect.x))[2]
            <= generator.get_platform_settings(generator.get_difficulty(platform.rect.x))[3]
            <= generator.max_jump_distance
            for platform in platforms
        )
        assert all(
            right.rect.left - left.rect.right <= generator.max_jump_distance
            for left, right in zip(platforms, platforms[1:])
        )


def _sweep(level, moving):
    distance = abs(int(moving.movement_distance))
    sweep, max_down = level._normal_moving_platform_sweep(
        moving.start_x,
        moving.start_y,
        moving.rect.width,
        moving.rect.height,
        moving.movement_type,
        distance,
    )
    return sweep, max_down


@pytest.mark.parametrize("level_number", range(11, MAX_LEVELS + 1))
def test_world_two_layout_has_safe_moving_platforms_checkpoint_and_finish(level_number):
    level = Level(seed=20261017 + level_number, level_number=level_number)

    if level_number == 11:
        assert len(level.moving_platforms) >= 2

    static_platforms = [platform for platform in level.platforms]
    for moving in level.moving_platforms:
        sweep, max_down = _sweep(level, moving)
        assert all(not sweep.colliderect(static.rect) for static in static_platforms)
        assert sweep.left >= 300
        assert sweep.right <= level.final_approach_start
        assert sweep.top >= 130
        if moving.movement_type == "vertical":
            assert moving.rect.top <= level.ground.rect.top - 80
            assert moving.start_y + max_down + moving.rect.height <= level.ground.rect.top - 40

    assert level.checkpoints, f"World 2 level {level_number} has no checkpoint"
    assert abs(level.finish_x - (level.width - 200)) <= 400

    spawn_safe_zone = pygame.Rect(0, level.ground.rect.top - 140, 300, 140)
    assert all(
        not platform.rect.colliderect(spawn_safe_zone)
        for platform in level.platforms
        if platform is not level.ground
    )
    assert all(not enemy.rect.colliderect(spawn_safe_zone) for enemy in level.enemies)


def test_pit_ground_collision_uses_predicted_player_bottom():
    import inspect
    source = inspect.getsource(Level.update)
    assert "predicted_bottom = (" in source
    assert "self.player.rect.bottom +" in source
    assert "if predicted_bottom >= self.world_height - 100:" in source
