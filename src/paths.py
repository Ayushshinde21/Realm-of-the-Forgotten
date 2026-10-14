"""Central place for every file-system location the game uses.

* ``BASE_DIR`` is the folder that holds ``assets/`` (the project folder, or
  the PyInstaller bundle folder when the game is packaged).
* ``data_dir()`` is the per-user folder for accounts, saves and settings, so
  updating or re-downloading the game never overwrites a player's progress.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_FOLDER_NAME = "VeggieQuest"

if getattr(sys, "frozen", False):  # running from a PyInstaller bundle
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "assets"


def data_dir() -> Path:
    """Per-user data folder (created on demand).

    Set the ``VEGGIEQUEST_DATA_DIR`` environment variable to override it
    (the automated tests do this).
    """
    override = os.environ.get("VEGGIEQUEST_DATA_DIR")
    if override:
        path = Path(override)
    elif sys.platform.startswith("win"):
        root = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        path = Path(root) / APP_FOLDER_NAME
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_FOLDER_NAME
    else:
        root = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        path = Path(root) / APP_FOLDER_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def accounts_file() -> Path:
    return data_dir() / "accounts.json"


def save_dir() -> Path:
    path = data_dir() / "save_data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_file() -> Path:
    return data_dir() / "settings.json"


def log_file() -> Path:
    return data_dir() / "veggiequest.log"


def migrate_legacy_data() -> None:
    """Copy accounts/saves that older versions kept next to the game into the
    per-user folder. Copies (never moves or overwrites), so it is safe to run
    on every start."""
    legacy_accounts = BASE_DIR / "accounts.json"
    if legacy_accounts.exists() and not accounts_file().exists():
        shutil.copy2(legacy_accounts, accounts_file())

    legacy_saves = BASE_DIR / "save_data"
    if legacy_saves.is_dir():
        for src in legacy_saves.glob("*.json"):
            dest = save_dir() / src.name
            if not dest.exists():
                shutil.copy2(src, dest)
