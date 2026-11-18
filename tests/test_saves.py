import json
from types import SimpleNamespace

from src import paths
from src.systems import save_system, session


class FakeCheckpoint:
    def __init__(self, cid):
        self.checkpoint_id = cid
        self.activated = False


def fake_level(number=1, stars=2, checkpoint=None):
    return SimpleNamespace(
        level_number=number, star_rating=stars,
        current_checkpoint=checkpoint, new_collectibles=5, damage_taken=False,
        elapsed_seconds=120, checkpoints=[],
    )


def test_no_user_means_no_save():
    save_system.save_game(fake_level())
    assert list(paths.save_dir().glob("*.json")) == []


def test_completing_world_one_final_level_unlocks_world_two_level_one():
    session.set_current_user("tester")
    save_system.save_game(fake_level(10, stars=3), unlock_next=True, completed=True)
    data = save_system.load_progress()
    progress = data["progress"]
    assert progress["unlocked_levels"] == [1, 11]
    assert progress["level_stars"]["10"] == 3
    assert data["version"] == save_system.SAVE_VERSION


def test_progress_is_one_continuous_campaign():
    session.set_current_user("tester")
    save_system.save_game(fake_level(10, stars=3), unlock_next=True, completed=True)
    save_system.save_game(fake_level(11, stars=2), unlock_next=True, completed=True)
    progress = save_system.load_progress()["progress"]
    assert progress["unlocked_levels"] == [1, 11, 12]
    assert progress["level_stars"] == {"10": 3, "11": 2}


def test_checkpoint_roundtrip_uses_global_level_number():
    session.set_current_user("tester")
    saved_level = fake_level(12, checkpoint=FakeCheckpoint(3))
    saved_level.checkpoints = [FakeCheckpoint(1), saved_level.current_checkpoint]
    saved_level.checkpoints[0].activated = True
    saved_level.checkpoints[1].activated = True
    save_system.save_game(saved_level)

    level = fake_level(12)
    level.checkpoints = [FakeCheckpoint(1), FakeCheckpoint(3)]
    save_system.load_game(level)
    assert level.current_checkpoint.checkpoint_id == 3
    assert [checkpoint.activated for checkpoint in level.checkpoints] == [True, True]


def test_legacy_easy_and_normal_progress_migrates_into_worlds():
    session.set_current_user("tester")
    path = paths.save_dir() / "tester.json"
    path.write_text(json.dumps({
        "difficulties": {
            "easy": {
                "unlocked_levels": [1, 2, 3],
                "level_stars": {"1": 3, "2": 2},
                "checkpoints": {"3": {"id": 7, "activated_ids": [7]}},
            },
            "normal": {
                "unlocked_levels": [1, 2],
                "level_stars": {"1": 2},
                "checkpoints": {},
            },
            "hard": {"unlocked_levels": [1, 5], "level_stars": {"5": 3}},
        },
        "total_collectibles": 7,
    }))

    data = save_system.load_progress()
    progress = data["progress"]
    assert progress["unlocked_levels"] == [1, 2, 3, 11, 12]
    assert progress["level_stars"] == {"1": 3, "2": 2, "11": 2}
    assert progress["checkpoints"]["3"]["id"] == 7
    assert "difficulties" not in data
    assert data["version"] == save_system.SAVE_VERSION


def test_legacy_unused_normal_track_does_not_unlock_world_two():
    session.set_current_user("tester")
    path = paths.save_dir() / "tester.json"
    path.write_text(json.dumps({
        "difficulties": {
            "easy": {"unlocked_levels": [1], "level_stars": {}, "checkpoints": {}},
            "normal": {"unlocked_levels": [1], "level_stars": {}, "checkpoints": {}},
        }
    }))
    assert save_system.load_progress()["progress"]["unlocked_levels"] == [1]


def test_corrupted_save_falls_back_to_defaults():
    session.set_current_user("tester")
    path = paths.save_dir() / "tester.json"
    path.write_text("garbage {{{")
    assert save_system.load_progress()["progress"]["unlocked_levels"] == [1]
    path.write_text("[1, 2, 3]")
    assert save_system.load_progress()["progress"]["unlocked_levels"] == [1]


def test_legacy_data_is_copied_not_moved(tmp_path, monkeypatch):
    legacy_root = tmp_path / "game"
    (legacy_root / "save_data").mkdir(parents=True)
    (legacy_root / "save_data" / "ayush.json").write_text("{}")
    (legacy_root / "accounts.json").write_text("{}")
    monkeypatch.setattr(paths, "BASE_DIR", legacy_root)
    paths.migrate_legacy_data()
    assert (paths.save_dir() / "ayush.json").exists()
    assert paths.accounts_file().exists()
    assert (legacy_root / "save_data" / "ayush.json").exists()
