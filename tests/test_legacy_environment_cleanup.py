from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_industrial_environment_is_not_shipped_or_imported():
    assert not (PROJECT_ROOT / "assets" / "tilesets" / "industrial_zone").exists()
    assert not (PROJECT_ROOT / "assets" / "tilesets" / "normal_tileset.png").exists()
    assert not (PROJECT_ROOT / "src" / "world" / "industrial_renderer.py").exists()
    assert not (PROJECT_ROOT / "src" / "world" / "industrial_tileset.py").exists()
    source_files = [path for path in (PROJECT_ROOT / "src").rglob("*.py")]
    assert all("industrial_renderer" not in path.read_text(encoding="utf-8") for path in source_files)
    assert all("industrial_tileset" not in path.read_text(encoding="utf-8") for path in source_files)


def test_twenty_level_campaign_still_uses_the_two_world_renderers():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.settings import MAX_LEVELS
    from src.world.level_data import LEVELS

    assert MAX_LEVELS == 20
    assert tuple(LEVELS["easy"]) == tuple(range(1, 11))
    assert tuple(LEVELS["normal"]) == tuple(range(1, 11))
    level_source = (PROJECT_ROOT / "src" / "world" / "level.py").read_text(encoding="utf-8")
    assert "draw_green_zone_background" in level_source
    assert "draw_easy_ground" in level_source
    assert "generate_obstacles" not in level_source
    assert "generate_bushes" not in level_source
    assert "update_bush_effects" not in level_source
