"""Player preferences (volumes, fullscreen, key bindings) stored in
settings.json inside the per-user data folder."""
from __future__ import annotations

import json
import logging
import os

from src import paths

log = logging.getLogger("veggiequest.settings")

DEFAULTS = {
    "music_volume": 0.2,   # matches the old hard-coded value
    "sound_volume": 0.7,
    "fullscreen": False,
    "keys": {},            # action name -> pygame key code (only overrides)
}


def _clamp01(value, fallback):
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return fallback


def load() -> dict:
    data = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULTS.items()}
    path = paths.settings_file()
    if not path.exists():
        return data
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("settings file is not a JSON object")
    except (json.JSONDecodeError, OSError, ValueError):
        log.exception("Could not read %s - using defaults", path)
        return data

    data["music_volume"] = _clamp01(raw.get("music_volume"), DEFAULTS["music_volume"])
    data["sound_volume"] = _clamp01(raw.get("sound_volume"), DEFAULTS["sound_volume"])
    data["fullscreen"] = bool(raw.get("fullscreen", False))
    keys = raw.get("keys")
    if isinstance(keys, dict):
        data["keys"] = {str(a): int(k) for a, k in keys.items() if isinstance(k, int)}
    return data


def save(data: dict) -> None:
    path = paths.settings_file()
    try:
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp, path)
    except OSError:
        log.exception("Could not write %s", path)
