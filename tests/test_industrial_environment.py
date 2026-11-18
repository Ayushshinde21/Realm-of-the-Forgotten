import ast
import struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = PROJECT_ROOT / "assets" / "tilesets" / "industrial_zone"
TILESET_SOURCE = PROJECT_ROOT / "src" / "world" / "industrial_tileset.py"
RENDERER_SOURCE = PROJECT_ROOT / "src" / "world" / "industrial_renderer.py"
LEVEL_SOURCE = PROJECT_ROOT / "src" / "world" / "level.py"


def _constant(name):
    tree = ast.parse(TILESET_SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError(f"Missing constant {name}")


def test_industrial_pack_is_organized_into_all_four_categories():
    assert len(list((ASSET_ROOT / "tiles").glob("IndustrialTile_*.png"))) == 81
    assert len(list((ASSET_ROOT / "backgrounds").glob("*.png"))) == 6
    assert len(list((ASSET_ROOT / "objects").glob("*.png"))) == 44
    assert len(list((ASSET_ROOT / "animated_objects").glob("*.png"))) == 12


def test_tileset_uses_project_relative_asset_paths_not_legacy_sheet():
    source = TILESET_SOURCE.read_text(encoding="utf-8")
    assert "from src.paths import ASSETS_DIR" in source
    assert "IndustrialTile_*.png" in source
    assert "normal_tileset.png" not in source
    assert "TILE_SIZE = 32" in source


def test_all_declared_animation_strips_have_valid_horizontal_frame_layouts():
    layouts = _constant("_ANIMATION_LAYOUT")
    for name, frame_size in layouts.items():
        path = ASSET_ROOT / "animated_objects" / f"{name}.png"
        assert path.is_file(), name
        header = path.read_bytes()[:24]
        assert header[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", header[16:24])
        frame_width, frame_height = frame_size
        assert frame_width > 0 and frame_height > 0
        assert width % frame_width == 0, name
        assert width // frame_width >= 2, name
        assert height >= frame_height, name


def test_every_referenced_tile_and_decoration_asset_exists():
    source = RENDERER_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    tile_id_names = {"_PLATFORM_TOP_IDS", "_PLATFORM_BODY_IDS", "_BACKGROUND_PANEL_IDS", "_HAZARD_TOP_IDS", "_PIT_BODY_IDS"}
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in tile_id_names:
                    constants[target.id] = ast.literal_eval(node.value)
    tile_ids = set().union(*(set(constants[name]) for name in tile_id_names))
    present_ids = {
        int(path.stem.rsplit("_", 1)[1])
        for path in (ASSET_ROOT / "tiles").glob("IndustrialTile_*.png")
    }
    assert tile_ids <= present_ids

    object_names = set()
    renderer_tree = ast.parse(source)
    for node in renderer_tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"_GROUND_OBJECTS", "_SMALL_PLATFORM_OBJECTS"}:
                    object_names.update(ast.literal_eval(node.value))
    object_stems = {path.stem for path in (ASSET_ROOT / "objects").glob("*.png")}
    assert object_names <= object_stems


def test_twenty_level_campaign_keeps_world_two_slots_defined():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.settings import MAX_LEVELS
    from src.world.level_data import LEVELS

    assert MAX_LEVELS == 20
    assert tuple(LEVELS["normal"]) == tuple(range(1, 11))
    assert all(level["world_number"] == 2 for level in LEVELS["normal"].values())
    assert all(level["difficulty"] == "Normal" for level in LEVELS["normal"].values())

def test_legacy_industrial_renderer_is_not_active_in_the_two_world_campaign():
    source = LEVEL_SOURCE.read_text(encoding="utf-8")
    assert "draw_industrial_" not in source
    assert "draw_green_zone_background" in source
    assert "draw_green_zone_decorations" in source
    assert 'elif self.difficulty == "normal":\n            draw_green_zone_background' in source
    assert 'elif self.difficulty == "easy":\n            draw_easy_ground' in source


def test_renderer_is_visual_only_and_uses_deterministic_level_seed():
    source = RENDERER_SOURCE.read_text(encoding="utf-8")
    assert "random.Random((int(seed) ^ (int(level_number) * 0x9E3779B9))" in source
    assert "self.rect" not in source
    assert "colliderect" in source
    assert "background_layer(name, BACKGROUND_SCALE)" in source
