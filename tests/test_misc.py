import pytest

from src import settings, user_settings
from src.systems import achievements


def test_star_thresholds_are_ordered():
    low, high = settings.STAR_THRESHOLDS
    assert 0 < low < high


def test_jump_constants_match_physics():
    # A flat jump lasts 2*jump/gravity frames and moves PLAYER_SPEED per frame.
    airtime = 2 * abs(settings.PLAYER_JUMP_STRENGTH) / settings.PLAYER_GRAVITY
    assert settings.MAX_JUMP_HORIZONTAL == int(settings.PLAYER_SPEED * airtime)


def test_user_settings_defaults_and_clamping(tmp_path):
    assert user_settings.load()["music_volume"] == 0.2
    user_settings.save({"music_volume": 5, "sound_volume": "x", "fullscreen": 1, "keys": {"jump": 32}})
    loaded = user_settings.load()
    assert loaded["music_volume"] == 1.0
    assert loaded["sound_volume"] == user_settings.DEFAULTS["sound_volume"]
    assert loaded["fullscreen"] is True
    assert loaded["keys"] == {"jump": 32}


def test_corrupted_settings_file_uses_defaults():
    from src import paths
    paths.settings_file().write_text("nope")
    assert user_settings.load()["music_volume"] == 0.2


def test_achievements_first_steps_and_all_stars():
    level = type("L", (), {"level_number": 1, "damage_taken": True, "elapsed_seconds": 500})()
    state = achievements.evaluate(level, {"total_collectibles": 0, "level_stars": {}, "achievements": {}})
    assert state["first_steps"] and not state["no_damage"] and not state["all_stars"]
    stars = {str(i): 3 for i in range(1, settings.MAX_LEVELS + 1)}
    state = achievements.evaluate(level, {"level_stars": stars, "achievements": {}})
    assert state["all_stars"]


def test_platform_generator_gaps_are_jumpable():
    pytest.importorskip("pygame")
    from src.world.platform_generator import PlatformGenerator
    gen = PlatformGenerator(world_width=20000)
    assert gen.max_jump_distance <= settings.MAX_JUMP_HORIZONTAL
    assert gen.safe_jump_height <= settings.MAX_JUMP_VERTICAL + 1
