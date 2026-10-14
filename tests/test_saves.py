import json
from types import SimpleNamespace

from src import paths
from src.systems import save_system, session


class FakeCheckpoint:
    def __init__(self, cid):
        self.checkpoint_id = cid
        self.activated = False


def fake_level(number=1, difficulty="normal", stars=2, checkpoint=None):
    return SimpleNamespace(
        level_number=number, difficulty=difficulty, star_rating=stars,
        current_checkpoint=checkpoint, new_collectibles=5, damage_taken=False,
        elapsed_seconds=120, checkpoints=[],
    )


def test_no_user_means_no_save():
    save_system.save_game(fake_level())  # must not raise
    assert list(paths.save_dir().glob("*.json")) == []


def test_complete_level_unlocks_next_and_stores_stars():
    session.set_current_user("tester")
    save_system.save_game(fake_level(1, stars=3), unlock_next=True, completed=True)
    data = save_system.load_progress(difficulty="normal")
    cur = data["current"]
    assert cur["unlocked_levels"] == [1, 2]
    assert cur["level_stars"]["1"] == 3
    assert data["version"] == save_system.SAVE_VERSION


def test_difficulties_are_independent():
    session.set_current_user("tester")
    save_system.save_game(fake_level(1, "hard", 3), unlock_next=True, completed=True)
    assert save_system.load_progress(difficulty="easy")["current"]["unlocked_levels"] == [1]
    assert save_system.load_progress(difficulty="hard")["current"]["unlocked_levels"] == [1, 2]


def test_checkpoint_roundtrip():
    session.set_current_user("tester")
    saved_level = fake_level(2, checkpoint=FakeCheckpoint(3))
    saved_level.checkpoints = [FakeCheckpoint(1), saved_level.current_checkpoint]
    saved_level.checkpoints[0].activated = True
    saved_level.checkpoints[1].activated = True
    save_system.save_game(saved_level)

    level = fake_level(2)
    level.checkpoints = [FakeCheckpoint(1), FakeCheckpoint(3)]
    save_system.load_game(level)
    assert level.current_checkpoint.checkpoint_id == 3
    assert [c.activated for c in level.checkpoints] == [True, True]


def test_old_save_without_version_is_migrated():
    session.set_current_user("tester")
    path = paths.save_dir() / "tester.json"
    path.write_text(json.dumps({"total_collectibles": 7}))
    data = save_system.load_progress()
    assert data["version"] == save_system.SAVE_VERSION
    assert data["total_collectibles"] == 7
    assert data["difficulties"]["easy"]["unlocked_levels"] == [1]


def test_corrupted_save_falls_back_to_defaults():
    session.set_current_user("tester")
    (paths.save_dir() / "tester.json").write_text("garbage {{{")
    data = save_system.load_progress(difficulty="normal")
    assert data["current"]["unlocked_levels"] == [1]
    (paths.save_dir() / "tester.json").write_text("[1, 2, 3]")  # valid JSON, wrong shape
    assert save_system.load_progress()["difficulties"]["normal"]["unlocked_levels"] == [1]


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
