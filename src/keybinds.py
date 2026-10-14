"""Rebindable keyboard controls.

Arrow keys always work for moving left/right in addition to the bound key,
so a player can never lock themselves out by rebinding.
"""
from __future__ import annotations

import pygame

from src import user_settings

ACTIONS = ("left", "right", "jump", "interact")

ACTION_LABELS = {
    "left": "Move left",
    "right": "Move right",
    "jump": "Jump",
    "interact": "Talk / interact",
}

DEFAULTS = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "jump": pygame.K_SPACE,
    "interact": pygame.K_e,
}

# Keys that may not be assigned (used by menus).
RESERVED = {pygame.K_ESCAPE, pygame.K_F11, pygame.K_RETURN, pygame.K_TAB}

_bindings = dict(DEFAULTS)


def load_from_settings(settings: dict) -> None:
    _bindings.clear()
    _bindings.update(DEFAULTS)
    for action, key in settings.get("keys", {}).items():
        if action in DEFAULTS:
            _bindings[action] = key


def get(action: str) -> int:
    return _bindings[action]


def key_name(action: str) -> str:
    return pygame.key.name(_bindings[action]).upper() or "?"


def rebind(action: str, key: int) -> bool:
    """Bind `key` to `action`. Returns False if the key is reserved. If the key
    was used by another action the two actions swap keys."""
    if action not in DEFAULTS or key in RESERVED:
        return False
    for other, bound in _bindings.items():
        if other != action and bound == key:
            _bindings[other] = _bindings[action]
    _bindings[action] = key
    _persist()
    return True


def reset_defaults() -> None:
    _bindings.clear()
    _bindings.update(DEFAULTS)
    _persist()


def _persist() -> None:
    data = user_settings.load()
    data["keys"] = {a: k for a, k in _bindings.items() if k != DEFAULTS[a]}
    user_settings.save(data)
