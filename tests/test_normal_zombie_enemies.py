import ast
import hashlib
import os
import struct
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENEMY_SPRITES_SOURCE = PROJECT_ROOT / "src" / "entities" / "enemy_sprites.py"
LEVEL_SOURCE = PROJECT_ROOT / "src" / "world" / "level.py"
ASSET_ROOT = PROJECT_ROOT / "assets" / "enemies" / "zombie_sheets"
FRAME_ROOT = ASSET_ROOT / "frames"


def _top_level_assignments(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assignments = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        assignments[target.id] = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        pass
    return assignments


def _png_size(path):
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", header[16:24])


def test_normal_enemy_roster_maps_only_to_zombie_variants():
    sprite_constants = _top_level_assignments(ENEMY_SPRITES_SOURCE)
    level_constants = _top_level_assignments(LEVEL_SOURCE)
    zombie_types = set(sprite_constants["NORMAL_ZOMBIE_TYPES"])
    role_map = level_constants["NORMAL_ZOMBIES_BY_ROLE"]

    assert len(zombie_types) == 7
    assert set(role_map) == {"slime", "fast", "jumper", "flyer", "heavy"}
    assert all(set(variants) <= zombie_types for variants in role_map.values())
    assert set().union(*map(set, role_map.values())) == zombie_types

    source = LEVEL_SOURCE.read_text(encoding="utf-8")
    assert "legacy_to_sprite" not in source
    assert "sprite_key = random.choice(\n                    NORMAL_ZOMBIES_BY_ROLE.get" in source


def test_all_zombie_sheet_animation_aliases_exist_and_can_be_sliced():
    constants = _top_level_assignments(ENEMY_SPRITES_SOURCE)
    zombie_types = set(constants["NORMAL_ZOMBIE_TYPES"])
    sheet_config = constants["_ZOMBIE_SHEET_CONFIG"]
    expected_animations = {"idle", "run", "attack", "hurt", "death"}

    assert set(sheet_config) == zombie_types
    total_animation_sheets = 0
    for sprite_key, (folder, animation_files) in sheet_config.items():
        assert set(animation_files) == expected_animations
        for filename in animation_files.values():
            path = ASSET_ROOT / folder / filename
            assert path.is_file(), f"Missing source sheet: {sprite_key}/{filename}"
            width, height = _png_size(path)
            assert height > 0
            assert width >= height
            assert width % height == 0, f"Sheet frames are not square-aligned: {path}"
            total_animation_sheets += 1

    assert total_animation_sheets == 35


def test_zombie_sheets_include_both_uploaded_packs_and_extra_animations():
    urban_root = ASSET_ROOT / "urban_pack"
    variety_root = ASSET_ROOT / "variety_pack"
    assert len(list(urban_root.rglob("*.png"))) == 20
    assert len(list(variety_root.rglob("*.png"))) == 30
    assert (variety_root / "Zombie Man" / "Bite.png").is_file()
    assert (variety_root / "Zombie Man" / "Attack_3.png").is_file()
    assert (variety_root / "Zombie Woman" / "Scream.png").is_file()


def test_zombie_animation_loader_uses_explicit_frames_and_keeps_sheet_fallback():
    source = ENEMY_SPRITES_SOURCE.read_text(encoding="utf-8")
    assert "_load_zombie_sheet_animations" in source
    assert 'frame_dir = os.path.join(_ZOMBIE_FRAME_ROOT, folder, frame_action)' in source
    assert 'name.startswith("frame_") and name.endswith(".png")' in source
    assert "frame_size = sheet.get_height()" in source
    assert "sheet.subsurface(frame_rect).copy()" in source
    assert "frame.get_bounding_rect(min_alpha=16)" in source
    assert "_ENEMY_FRAME_CACHE[cache_key] = animations" in source


def test_every_zombie_action_has_individual_unique_frame_images():
    source_sheets = list((ASSET_ROOT / "urban_pack").rglob("*.png"))
    source_sheets += list((ASSET_ROOT / "variety_pack").rglob("*.png"))
    assert len(source_sheets) == 50

    total_frames = 0
    for sheet in source_sheets:
        relative = sheet.relative_to(ASSET_ROOT)
        action_dir = FRAME_ROOT / relative.parent / sheet.stem
        frames = sorted(action_dir.glob("frame_*.png"))
        assert frames, f"Missing extracted frames for {relative}"

        hashes = [hashlib.sha256(frame.read_bytes()).hexdigest() for frame in frames]
        assert len(hashes) == len(set(hashes)), f"Duplicate frame images in {action_dir}"
        total_frames += len(frames)

    assert total_frames == 301
    assert (FRAME_ROOT / "README.txt").is_file()


def test_zombie_locomotion_animation_loops_while_action_animations_stay_one_shot():
    source = (PROJECT_ROOT / "src" / "entities" / "enemy.py").read_text(encoding="utf-8")
    assert "def _advance_animation(self, loop=False):" in source
    assert "self.anim_frame = (self.anim_frame + 1) % len(frames)" in source
    assert 'self._advance_animation(loop=is_normal_zombie)' in source


def test_easy_and_hard_enemy_selection_paths_remain_separate():
    source = LEVEL_SOURCE.read_text(encoding="utf-8")
    assert 'if self.difficulty == "easy":\n                enemy_type = "slime"' in source
    assert 'if enemy_type == "slime" and self.difficulty in ("easy", "hard"):' in source
    assert 'if self.difficulty == "normal":\n                # Normal\'s roster is replaced completely by animated zombies.' in source


def test_zombie_attack_hit_frames_fit_their_attack_sheets():
    constants = _top_level_assignments(ENEMY_SPRITES_SOURCE)
    sprite_configs = constants["SPRITE_ENEMY_CONFIG"]
    sheet_config = constants["_ZOMBIE_SHEET_CONFIG"]
    for sprite_key, (folder, animation_files) in sheet_config.items():
        attack_path = ASSET_ROOT / folder / animation_files["attack"]
        width, height = _png_size(attack_path)
        frame_count = width // height
        enemy_config = sprite_configs[sprite_key]
        assert enemy_config["style"] == "melee"
        assert 0 <= enemy_config["hit_frame"] < frame_count
        assert enemy_config["target_h"] >= 55


def test_normal_zombies_use_fractional_movement_and_larger_scale():
    source = LEVEL_SOURCE.read_text(encoding="utf-8")
    enemy_source = (PROJECT_ROOT / "src" / "entities" / "enemy.py").read_text(encoding="utf-8")

    assert "NORMAL_ZOMBIE_SIZE_MULTIPLIER = 1.25" in source
    assert "float(self.speed) * self.direction" in enemy_source
    assert "self._normal_zombie_x + float(self.speed) * self.facing" in enemy_source
    assert "self.anim_speed = 6 if self.sprite_key in NORMAL_ZOMBIE_TYPES else 7" in enemy_source


def test_normal_zombie_subpixel_movement_and_size_at_runtime():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame = pytest.importorskip("pygame")
    pygame.init()
    pygame.display.set_mode((640, 480))
    try:
        from src.entities.enemy import Enemy

        enemy = Enemy(
            100, 200, 50, 450, speed=0.9,
            enemy_type="slime", sprite_key="zombie_1", sprite_scale=1.25,
        )
        initial_x = enemy.rect.x
        assert enemy.rect.height == round(62 * 1.25)

        for _ in range(30):
            enemy.update()

        assert enemy.rect.x - initial_x >= 20
        assert enemy.rect.left >= enemy.left_limit
        assert enemy.rect.right <= enemy.right_limit
    finally:
        pygame.quit()
