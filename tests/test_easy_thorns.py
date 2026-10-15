from pathlib import Path
import importlib.util

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEVEL_SOURCE = (PROJECT_ROOT / "src" / "world" / "level.py").read_text(encoding="utf-8")
THORN_SOURCE = (PROJECT_ROOT / "src" / "entities" / "thorn.py").read_text(encoding="utf-8")


def test_easy_pit_locations_become_thorn_hazards_and_keep_solid_ground():
    assert 'if self.difficulty == "easy":' in LEVEL_SOURCE
    assert "self.thorns.append(" in LEVEL_SOURCE
    assert "self.pits.append(pit)" in LEVEL_SOURCE
    assert "if not inside_pit:" in LEVEL_SOURCE
    assert "THORN_SLOW_FACTOR = 5.0" in LEVEL_SOURCE
    assert "THORN_DAMAGE_INTERVAL_FRAMES = 30" in LEVEL_SOURCE


def test_thorn_strip_is_loaded_as_eight_animated_frames():
    assert "FRAME_COUNT = 8" in THORN_SOURCE
    assert '"thorns_strip.png"' in THORN_SOURCE
    assert (PROJECT_ROOT / "assets" / "obstacles" / "thorns_strip.png").is_file()
    assert "self.frame_index = (self.frame_index + 1) % self.FRAME_COUNT" in THORN_SOURCE


@pytest.mark.skipif(importlib.util.find_spec("pygame") is None, reason="Pygame is not installed")
def test_easy_regular_level_uses_thorns_instead_of_pits_and_applies_damage():
    import pygame

    pygame.init()
    pygame.display.set_mode((1280, 720))
    from src.world.level import Level, THORN_SLOW_FACTOR

    try:
        level = Level(seed=81273, level_number=1, difficulty="easy")
        assert not level.pits
        assert level.thorns

        thorn = level.thorns[0]
        level.player.rect.centerx = thorn.hitbox.centerx
        level.player.rect.bottom = level.ground.rect.top
        health_before = level.player.health
        base_speed = level.player.base_speed
        base_jump = level.base_player_jump_strength

        level._apply_thorn_movement_effect()
        assert level.player.speed == pytest.approx(base_speed / THORN_SLOW_FACTOR)
        assert level.player.jump_strength == pytest.approx(base_jump / THORN_SLOW_FACTOR)

        for _ in range(60):
            level._update_thorn_effects()

        assert level.player.health == health_before - 2

        normal = Level(seed=81273, level_number=1, difficulty="normal")
        hard = Level(seed=81273, level_number=1, difficulty="hard")
        assert not normal.thorns
        assert not hard.thorns
    finally:
        pygame.quit()


def test_thorn_patches_are_wider_repeated_and_half_embedded_into_the_ground():
    assert "WIDTH_SCALE = 1.8" in THORN_SOURCE
    assert "VISIBLE_ABOVE_GROUND_RATIO = 0.5" in THORN_SOURCE
    assert "TILE_OVERLAP_RATIO = 0.18" in THORN_SOURCE
    assert "expanded_width = max(width, round(width * self.WIDTH_SCALE))" in THORN_SOURCE
    assert "frame.get_width() / frame.get_height()" in THORN_SOURCE
    assert "while tile_x < screen_rect.right:" in THORN_SOURCE
    assert "floor_y - visible_height" in THORN_SOURCE
    draw_source = LEVEL_SOURCE[LEVEL_SOURCE.index("    def draw(self, screen):"):]
    thorn_draw = draw_source.index("thorn.draw(screen, self.camera)")
    ground_draw = draw_source.index("draw_easy_ground(screen, self.camera, self.ground.rect)")
    assert thorn_draw < ground_draw
    assert "drawn before the ground on Easy" in draw_source
