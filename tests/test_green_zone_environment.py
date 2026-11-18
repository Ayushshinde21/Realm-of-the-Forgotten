import ast
import struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = PROJECT_ROOT / "assets" / "tilesets" / "green_zone"
TILESET_SOURCE = PROJECT_ROOT / "src" / "world" / "green_zone_tileset.py"
RENDERER_SOURCE = PROJECT_ROOT / "src" / "world" / "green_zone_renderer.py"
LEVEL_SOURCE = PROJECT_ROOT / "src" / "world" / "level.py"


def _module_constants(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        found[target.id] = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        pass
    return found


def _png_size(path):
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", header[16:24])


def test_green_zone_pack_has_tiles_day_and_night_backgrounds_and_objects():
    assert len(list((ASSET_ROOT / "tiles").glob("Tile_*.png"))) == 96
    assert len(list((ASSET_ROOT / "backgrounds" / "day").glob("*.png"))) == 6
    assert len(list((ASSET_ROOT / "backgrounds" / "night").glob("*.png"))) == 5
    assert len(list((ASSET_ROOT / "objects" / "trees").glob("*.png"))) == 4
    assert len(list((ASSET_ROOT / "objects" / "stones").glob("*.png"))) == 6
    assert len(list((ASSET_ROOT / "objects" / "fountains").glob("*.png"))) == 2
    assert {p.name for p in (ASSET_ROOT / "animated_objects").glob("*.png")} == {"Fountain.png", "Money.png"}


def test_loader_uses_project_relative_green_zone_paths_and_caches_assets():
    source = TILESET_SOURCE.read_text(encoding="utf-8")
    assert "from src.paths import ASSETS_DIR" in source
    assert 'ASSETS_DIR / "tilesets" / "green_zone"' in source
    assert "class GreenZoneTileset" in source
    assert "self._scaled_backgrounds" in source
    assert "pygame.image.load" in source
    assert "industrial_zone" not in source


def test_every_tile_referenced_by_green_zone_renderer_exists():
    constants = _module_constants(RENDERER_SOURCE)
    ids = set()
    for name in ("_GROUND_TOP_IDS", "_PLATFORM_TOP_IDS", "_SOIL_BODY_IDS", "_STONE_BODY_IDS", "_GRASS_EDGE_IDS"):
        ids.update(constants[name])
    present = {int(path.stem.split("_", 1)[1]) for path in (ASSET_ROOT / "tiles").glob("Tile_*.png")}
    assert ids <= present


def test_tree_stone_fountain_and_animation_references_exist_and_are_valid():
    constants = _module_constants(RENDERER_SOURCE)
    object_stems = set()
    for folder in ("trees", "stones", "fountains"):
        object_stems.update(path.stem for path in (ASSET_ROOT / "objects" / folder).glob("*.png"))
    assert set(constants["_TREE_NAMES"]) <= object_stems
    assert set(constants["_STONE_NAMES"]) <= object_stems

    fountain_frames = _png_size(ASSET_ROOT / "animated_objects" / "Fountain.png")
    money_frames = _png_size(ASSET_ROOT / "animated_objects" / "Money.png")
    assert fountain_frames == (288, 72)
    assert money_frames == (144, 24)
    assert fountain_frames[0] // 72 == 4
    assert money_frames[0] // 24 == 6


def test_twenty_level_campaign_keeps_ten_world_two_slots_configured():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.settings import MAX_LEVELS
    from src.world.level_data import LEVELS

    assert MAX_LEVELS == 20
    assert tuple(LEVELS["normal"]) == tuple(range(1, 11))
    assert all(level["world_number"] == 2 for level in LEVELS["normal"].values())
    assert all(level["difficulty"] == "Normal" for level in LEVELS["normal"].values())


def test_world_renderers_remain_separate():
    source = LEVEL_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    level_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Level")
    draw_method = next(node for node in level_class.body if isinstance(node, ast.FunctionDef) and node.name == "draw")
    calls = {node.func.id for node in ast.walk(draw_method) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    for name in (
        "draw_green_zone_background", "draw_green_zone_ground", "draw_green_zone_platform",
        "draw_green_zone_moving_platform", "draw_green_zone_pit", "draw_green_zone_decorations",
    ):
        assert name in calls
    assert 'elif self.difficulty == "normal":\n            draw_green_zone_background' in source
    assert 'if self.difficulty == "normal":\n            draw_green_zone_decorations' in source
    assert 'if self.difficulty == "easy":\n                draw_easy_platform' in source
    assert 'elif self.difficulty == "easy":\n            draw_easy_ground' in source
    assert "draw_industrial_" not in source


def test_green_zone_renderer_is_visual_only_and_decor_layout_is_seeded():
    source = RENDERER_SOURCE.read_text(encoding="utf-8")
    assert "random.Random((int(seed) ^ (int(level_number) * 0x45D9F3B))" in source
    assert "draw_green_zone_background" in source
    assert "self.rect" not in source
    assert "set_clip" in source
    assert "colliderect" in source


def test_legacy_industrial_assets_are_not_used_by_the_world_renderers():
    level_source = LEVEL_SOURCE.read_text(encoding="utf-8")
    assert "industrial_zone" not in level_source
    assert "draw_industrial_" not in level_source

def test_moving_platform_texture_moves_with_its_platform():
    source = RENDERER_SOURCE.read_text(encoding="utf-8")
    assert "first_x = world_rect.left + ((visible_left - world_rect.left) // TILE) * TILE" in source
    assert "tile_column = (world_x - world_rect.left) // TILE" in source
    assert "tile_row = (world_y - world_rect.top) // TILE" in source
    assert "if moving:" in source
