import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Every test gets its own empty data folder, so tests never touch real
    accounts or saves."""
    monkeypatch.setenv("VEGGIEQUEST_DATA_DIR", str(tmp_path))
    from src.systems import account_system, session
    account_system._failed.clear()
    session.logout()
    return tmp_path
