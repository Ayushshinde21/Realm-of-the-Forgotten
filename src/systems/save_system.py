import json
import logging
import os

from src import paths
from src.settings import MAX_LEVELS, WORLD_LEVEL_COUNT
from src.systems.achievements import evaluate, default_state
from src.systems import session

log = logging.getLogger("veggiequest.save")

# Save version 2 replaces independent difficulty progress with one campaign
# progress track covering all twenty levels.
SAVE_VERSION = 2


def _default_progress():
    return {
        "unlocked_levels": [1],
        "level_stars": {},
        "checkpoints": {},
    }


def _default_data():
    return {
        "version": SAVE_VERSION,
        "progress": _default_progress(),
        "total_collectibles": 0,
        "achievements": default_state(),
    }


def _safe_filename(username):
    return "".join(c for c in username if c.isalnum() or c in ("-", "_")) or "player"


def _save_path(username=None):
    """Resolve the current user's save path, or return None when logged out."""
    username = username or session.get_current_user()
    if not username:
        return None
    return str(paths.save_dir() / f"{_safe_filename(username)}.json")


def _valid_level_number(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= MAX_LEVELS else None


def _copy_legacy_world(progress, legacy, offset, skip_default_only=False):
    """Copy one legacy 1-10 difficulty track into the unified 20-level track."""
    if not isinstance(legacy, dict):
        return

    unlocked = legacy.get("unlocked_levels", [1])
    stars = legacy.get("level_stars", {})
    checkpoints = legacy.get("checkpoints", {})
    if not isinstance(unlocked, list):
        unlocked = [1]
    if not isinstance(stars, dict):
        stars = {}
    if not isinstance(checkpoints, dict):
        checkpoints = {}

    has_real_progress = (
        any(_valid_level_number(value) not in (None, 1) for value in unlocked)
        or bool(stars)
        or bool(checkpoints)
    )
    if skip_default_only and not has_real_progress:
        return

    for value in unlocked:
        local_level = _valid_level_number(value)
        if local_level is not None and local_level <= WORLD_LEVEL_COUNT:
            progress["unlocked_levels"].append(local_level + offset)

    for key, value in stars.items():
        local_level = _valid_level_number(key)
        if local_level is not None and local_level <= WORLD_LEVEL_COUNT:
            progress["level_stars"][str(local_level + offset)] = max(0, min(3, int(value)))

    for key, value in checkpoints.items():
        local_level = _valid_level_number(key)
        if local_level is not None and local_level <= WORLD_LEVEL_COUNT:
            progress["checkpoints"][str(local_level + offset)] = value


def _migrate(data):
    """Upgrade legacy per-difficulty saves to the two-world campaign format."""
    if not isinstance(data, dict):
        data = {}

    version = data.get("version", 0)
    if not isinstance(version, int):
        version = 0

    progress = data.get("progress")
    if version < 2 or not isinstance(progress, dict):
        legacy_difficulties = data.get("difficulties", {})
        if not isinstance(legacy_difficulties, dict):
            legacy_difficulties = {}

        progress = _default_progress()
        # Former Easy progress becomes World 1 (global levels 1-10).
        _copy_legacy_world(progress, legacy_difficulties.get("easy"), 0)
        # Former Normal progress becomes World 2 (global levels 11-20).
        # A never-played default [1] entry does not prematurely unlock World 2.
        _copy_legacy_world(
            progress,
            legacy_difficulties.get("normal"),
            WORLD_LEVEL_COUNT,
            skip_default_only=True,
        )

    unlocked = progress.get("unlocked_levels", [1])
    stars = progress.get("level_stars", {})
    checkpoints = progress.get("checkpoints", {})
    if not isinstance(unlocked, list):
        unlocked = [1]
    if not isinstance(stars, dict):
        stars = {}
    if not isinstance(checkpoints, dict):
        checkpoints = {}

    clean_unlocked = {1}
    for value in unlocked:
        number = _valid_level_number(value)
        if number is not None:
            clean_unlocked.add(number)

    clean_stars = {}
    for key, value in stars.items():
        number = _valid_level_number(key)
        if number is None:
            continue
        try:
            clean_stars[str(number)] = max(0, min(3, int(value)))
        except (TypeError, ValueError):
            continue

    clean_checkpoints = {}
    for key, value in checkpoints.items():
        number = _valid_level_number(key)
        if number is not None and isinstance(value, dict):
            clean_checkpoints[str(number)] = value

    migrated = dict(data)
    migrated["version"] = SAVE_VERSION
    migrated["progress"] = {
        "unlocked_levels": sorted(clean_unlocked),
        "level_stars": clean_stars,
        "checkpoints": clean_checkpoints,
    }
    migrated.pop("difficulties", None)
    return migrated


def _read(username=None):
    path = _save_path(username)
    if not path or not os.path.exists(path):
        return _default_data()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("save file is not a JSON object")
    except (json.JSONDecodeError, OSError, ValueError):
        log.exception("Could not read save file %s - using defaults", path)
        return _default_data()

    merged = _default_data()
    merged.update(_migrate(data))
    return merged


def save_game(level, unlock_next=False, completed=False, username=None):
    path = _save_path(username)
    if not path:
        return

    existing_data = _read(username)
    progress = existing_data["progress"]

    unlocked_levels = set(progress.get("unlocked_levels", [1]))
    unlocked_levels.add(1)
    level_number = _valid_level_number(getattr(level, "level_number", 1)) or 1
    if unlock_next and level_number < MAX_LEVELS:
        unlocked_levels.add(level_number + 1)

    stars = dict(progress.get("level_stars", {}))
    if completed:
        stars[str(level_number)] = max(1, min(3, int(getattr(level, "star_rating", 1))))

    checkpoints = dict(progress.get("checkpoints", {}))
    if level.current_checkpoint is not None and not completed:
        current_checkpoint_id = level.current_checkpoint.checkpoint_id
        activated_ids = {
            checkpoint.checkpoint_id
            for checkpoint in getattr(level, "checkpoints", [])
            if getattr(checkpoint, "activated", False)
        }
        activated_ids.add(current_checkpoint_id)
        checkpoints[str(level_number)] = {
            "id": current_checkpoint_id,
            "activated_ids": sorted(activated_ids),
        }
    else:
        checkpoints.pop(str(level_number), None)

    progress["unlocked_levels"] = sorted(unlocked_levels)
    progress["level_stars"] = stars
    progress["checkpoints"] = checkpoints

    total_collectibles = (
        int(existing_data.get("total_collectibles", 0)) + int(getattr(level, "new_collectibles", 0))
        if completed else int(existing_data.get("total_collectibles", 0))
    )
    achievements = existing_data.get("achievements", default_state())
    eval_context = {
        "level_stars": stars,
        "total_collectibles": total_collectibles,
        "achievements": achievements,
    }
    new_achievements = evaluate(level, eval_context) if completed else achievements

    data = {
        "version": SAVE_VERSION,
        "progress": progress,
        "total_collectibles": total_collectibles,
        "achievements": new_achievements,
    }
    try:
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_path, path)
    except OSError:
        log.exception("Could not write save file %s", path)


def load_game(level, level_select=None, username=None):
    data = _read(username)
    progress = data["progress"]

    checkpoint_data = progress.get("checkpoints", {}).get(str(level.level_number))
    if checkpoint_data is not None:
        saved_id = checkpoint_data.get("id")
        saved_activated_ids = checkpoint_data.get("activated_ids")
        if not isinstance(saved_activated_ids, list):
            saved_activated_ids = [saved_id] if saved_id is not None else []
        saved_activated_ids = set(saved_activated_ids)
        for checkpoint in level.checkpoints:
            if checkpoint.checkpoint_id in saved_activated_ids:
                checkpoint.activated = True
            if checkpoint.checkpoint_id == saved_id:
                level.current_checkpoint = checkpoint

    if level_select is not None:
        for number in progress.get("unlocked_levels", [1]):
            level_select.unlock_level(int(number))
        level_select.set_stars(progress.get("level_stars", {}))
    return True


def load_progress(username=None):
    """Return the unified campaign progress for levels 1 through 20."""
    return _read(username)


def delete_save(username=None):
    """Delete only the given user's save file."""
    path = _save_path(username)
    if path and os.path.exists(path):
        os.remove(path)
