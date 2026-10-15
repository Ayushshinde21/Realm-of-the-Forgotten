from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MOVING_PLATFORM_SOURCE = (PROJECT_ROOT / "src" / "entities" / "moving_platform.py").read_text(encoding="utf-8")
LEVEL_SOURCE = (PROJECT_ROOT / "src" / "world" / "level.py").read_text(encoding="utf-8")


def test_moving_platform_supports_asymmetric_vertical_limits():
    assert "movement_min_offset=None" in MOVING_PLATFORM_SOURCE
    assert "movement_max_offset=None" in MOVING_PLATFORM_SOURCE
    assert "if self.offset >= self.movement_max_offset:" in MOVING_PLATFORM_SOURCE
    assert "elif self.offset <= self.movement_min_offset:" in MOVING_PLATFORM_SOURCE


def test_vertical_platform_starts_upward_and_stays_above_ground():
    assert "ground_clearance = 40" in LEVEL_SOURCE
    assert "self.ground.rect.top" in LEVEL_SOURCE
    assert '"movement_min_offset": -movement_distance' in LEVEL_SOURCE
    assert '"movement_max_offset": min(' in LEVEL_SOURCE
    assert 'platform.direction = -1' in LEVEL_SOURCE


def test_horizontal_platforms_keep_default_symmetric_motion():
    assert "-abs(float(movement_distance))" in MOVING_PLATFORM_SOURCE
    assert "abs(float(movement_distance))" in MOVING_PLATFORM_SOURCE
    assert 'if movement_type == "vertical":' in LEVEL_SOURCE


def test_player_is_carried_before_platform_collision_resolution():
    player_source = (PROJECT_ROOT / "src" / "entities" / "player.py").read_text(encoding="utf-8")
    carry_marker = "# Carry a grounded player with the platform before applying gravity"
    gravity_marker = "self.apply_gravity()"
    collision_marker = "self.handle_platform_collision(platforms, previous_rect)"

    assert carry_marker in player_source
    assert player_source.index(carry_marker) < player_source.index("previous_rect = self.rect.copy()")
    assert player_source.index("previous_rect = self.rect.copy()") < player_source.index(gravity_marker)
    assert player_source.index(gravity_marker) < player_source.index(collision_marker)
    assert "self.rect.right > landing_rect.left" in player_source
    assert "self.rect.left < landing_rect.right" in player_source
