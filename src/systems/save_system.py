import json
import logging
import os

from src import paths
from src.systems.achievements import evaluate, default_state
from src.settings import MAX_LEVELS
from src.systems import session

log = logging.getLogger("veggiequest.save")

# Bump this when the save layout changes and add a step to _migrate().
SAVE_VERSION = 1

DIFFICULTIES = ("easy", "normal", "hard")


def _default_difficulty_progress():
    """Progress is tracked separately per difficulty: each of easy/normal/
    hard has its own independent set of unlocked levels, stars, and
    in-progress checkpoints, so clearing Level 1 on one difficulty never
    unlocks or affects Level 1 on another difficulty."""
    return {
        "unlocked_levels": [1],
        "level_stars": {},
        # Per-level in-progress checkpoint, keyed by level number as a
        # string. This is what previously leaked between levels when it
        # was stored as a single global value.
        "checkpoints": {},
    }


def _default_data():
    return {
        "version": SAVE_VERSION,
        "difficulties": {d: _default_difficulty_progress() for d in DIFFICULTIES},
        "total_collectibles": 0,
        "achievements": default_state(),
    }


def _normalize_difficulty(difficulty):
    d = str(difficulty).lower()
    return d if d in DIFFICULTIES else "normal"


def _safe_filename(username):
    return "".join(c for c in username if c.isalnum() or c in ("-", "_")) or "player"


def _save_path(username=None):
    """Resolves the save file path for a username (defaults to the
    currently logged-in user). Returns None if no user is available,
    so callers can no-op instead of touching a shared file."""
    username = username or session.get_current_user()
    if not username:
        return None
    return str(paths.save_dir() / f"{_safe_filename(username)}.json")


def _migrate(data):
    """Upgrade an older save dict to SAVE_VERSION. Saves written before the
    version field existed count as version 0 and already have the current
    layout, so they only need the number stamped on them."""
    version = data.get("version", 0)
    if not isinstance(version, int):
        version = 0
    # Future upgrades go here, e.g.:  if version < 2: ...; version = 2
    data["version"] = SAVE_VERSION
    return data


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

    # Make sure every difficulty always has a complete progress dict, even
    # if the save file is from before this structure existed or is missing
    # a difficulty entry.
    diffs = merged.get("difficulties")
    if not isinstance(diffs, dict):
        diffs = {}
    for d in DIFFICULTIES:
        prog = dict(_default_difficulty_progress())
        prog.update(diffs.get(d) or {})
        diffs[d] = prog
    merged["difficulties"] = diffs
    return merged


def save_game(level, unlock_next=False, completed=False, username=None):
    path = _save_path(username)
    if not path:
        return  # no logged-in user - nothing to save to

    existing_data = _read(username)
    difficulty = _normalize_difficulty(getattr(level, "difficulty", "normal"))
    diffs = existing_data["difficulties"]
    prog = diffs[difficulty]

    unlocked_levels = prog.get("unlocked_levels", [1])
    if 1 not in unlocked_levels: unlocked_levels.insert(0, 1)
    if unlock_next and level.level_number < MAX_LEVELS:
        nxt = level.level_number + 1
        if nxt not in unlocked_levels: unlocked_levels.append(nxt)

    stars = prog.get("level_stars", {})
    if completed:
        stars[str(level.level_number)] = int(getattr(level, "star_rating", 1))

    checkpoints = prog.get("checkpoints", {})
    if level.current_checkpoint is not None and not completed:
        current_checkpoint_id = level.current_checkpoint.checkpoint_id
        activated_ids = {
            checkpoint.checkpoint_id
            for checkpoint in getattr(level, "checkpoints", [])
            if getattr(checkpoint, "activated", False)
        }
        # The currently saved checkpoint is known to be activated even when
        # a lightweight test/dummy level does not expose the checkpoint list.
        activated_ids.add(current_checkpoint_id)
        checkpoints[str(level.level_number)] = {
            "id": current_checkpoint_id,
            "activated_ids": sorted(activated_ids),
        }
    else:
        # Level finished (or has no active checkpoint): don't leave a
        # stale mid-level checkpoint behind for next time it's played.
        checkpoints.pop(str(level.level_number), None)

    prog["unlocked_levels"] = sorted(set(unlocked_levels))
    prog["level_stars"] = stars
    prog["checkpoints"] = checkpoints
    diffs[difficulty] = prog

    total_collectibles = (
        int(existing_data.get("total_collectibles", 0)) + int(getattr(level, "new_collectibles", 0))
        if completed else
        int(existing_data.get("total_collectibles", 0))
    )
    achievements = existing_data.get("achievements", default_state())

    eval_context = {
        "difficulties": diffs,
        "level_stars": stars,
        "total_collectibles": total_collectibles,
        "achievements": achievements,
    }
    new_achievements = evaluate(level, eval_context) if completed else achievements

    data = {
        "version": SAVE_VERSION,
        "difficulties": diffs,
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
    difficulty = _normalize_difficulty(getattr(level, "difficulty", "normal"))
    prog = data["difficulties"][difficulty]

    # Only restore a checkpoint that was saved for THIS level, on THIS
    # difficulty - this is what keeps checkpoints independent per level
    # instead of leaking into whichever level/difficulty loads next.
    checkpoint_data = prog.get("checkpoints", {}).get(str(level.level_number))
    if checkpoint_data is not None:
        saved_id = checkpoint_data.get("id")
        saved_activated_ids = checkpoint_data.get("activated_ids")
        if not isinstance(saved_activated_ids, list):
            # Backward compatibility with saves made before activated flag
            # states were stored; only the known saved checkpoint is green.
            saved_activated_ids = [saved_id] if saved_id is not None else []
        saved_activated_ids = set(saved_activated_ids)
        for checkpoint in level.checkpoints:
            if checkpoint.checkpoint_id in saved_activated_ids:
                checkpoint.activated = True
            if checkpoint.checkpoint_id == saved_id:
                level.current_checkpoint = checkpoint

    if level_select is not None:
        for n in prog.get("unlocked_levels", [1]): level_select.unlock_level(int(n))
        level_select.set_stars(prog.get("level_stars", {}))
    return True


def load_progress(username=None, difficulty=None):
    """Returns the full save data. If `difficulty` is given, also includes
    a convenience 'current' key with just that difficulty's progress."""
    data = _read(username)
    if difficulty is not None:
        data = dict(data)
        data["current"] = data["difficulties"][_normalize_difficulty(difficulty)]
    return data


def delete_save(username=None):
    """Deletes ONLY the given (or currently logged-in) user's save file."""
    path = _save_path(username)
    if path and os.path.exists(path):
        os.remove(path)
