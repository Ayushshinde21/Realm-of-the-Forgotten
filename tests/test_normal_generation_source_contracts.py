"""Source-level contracts that remain runnable when Pygame is unavailable."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_SOURCE = (PROJECT_ROOT / "src" / "world" / "platform_generator.py").read_text(encoding="utf-8")
LEVEL_SOURCE = (PROJECT_ROOT / "src" / "world" / "level.py").read_text(encoding="utf-8")


def test_platform_generator_clamps_all_random_ranges():
    assert "min_gap = min(" in GENERATOR_SOURCE
    assert "max(0, max_gap)" in GENERATOR_SOURCE
    assert "max_width = max(" in GENERATOR_SOURCE
    assert "min_height_change = min(40, max_height_change)" in GENERATOR_SOURCE
    assert "min_high_low_change = min(50, max_height_change)" in GENERATOR_SOURCE


def test_normal_moving_platforms_validate_their_full_sweep():
    assert "def _normal_moving_platform_sweep" in LEVEL_SOURCE
    assert "preferred_centers" in LEVEL_SOURCE
    assert "if any(sweep.colliderect(platform.rect) for platform in static_platforms):" in LEVEL_SOURCE
    assert "self._generate_normal_moving_platforms()" in LEVEL_SOURCE
    assert "Preserve the previous fixed moving-platform layout for Easy/Hard." in LEVEL_SOURCE


def test_normal_checkpoints_try_alternate_platforms_and_ground_fallback():
    assert "for platform in candidates:" in LEVEL_SOURCE
    assert "Try multiple safe points on the preferred platform" in LEVEL_SOURCE
    assert "Normal must not silently lose a checkpoint slot" in LEVEL_SOURCE
    assert 'self.difficulty == "normal" and self.width > 3000 and not self.checkpoints' in LEVEL_SOURCE


def test_normal_finish_is_reserved_near_world_end():
    assert 'if self.difficulty == "normal":' in LEVEL_SOURCE
    assert 'int(self.width - 200)' in LEVEL_SOURCE
    assert "The finish marker has priority over nearby decorative/platforming" in LEVEL_SOURCE


def test_spawn_zone_and_predicted_pit_bottom_are_guarded():
    assert 'self.generator.safe_start_zone_width = 300 if self.difficulty == "normal" else 0' in LEVEL_SOURCE
    assert 'start_safe_zone = pygame.Rect(' in LEVEL_SOURCE
    assert 'if predicted_bottom >= self.world_height - 100:' in LEVEL_SOURCE
