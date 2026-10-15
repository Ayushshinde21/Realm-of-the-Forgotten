import ast
from pathlib import Path
from types import SimpleNamespace


GAME_SOURCE = Path(__file__).resolve().parents[1] / "src" / "game.py"


def _load_should_hide_cursor():
    tree = ast.parse(GAME_SOURCE.read_text(encoding="utf-8"))
    game_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Game")
    method = next(node for node in game_class.body if isinstance(node, ast.FunctionDef) and node.name == "_should_hide_cursor")
    module = ast.Module(body=[method], type_ignores=[])
    namespace = {}
    exec(compile(ast.fix_missing_locations(module), str(GAME_SOURCE), "exec"), namespace)
    return namespace["_should_hide_cursor"]


def _state(**overrides):
    values = {
        "logged_in": True,
        "game_started": True,
        "level_selected": True,
        "level": object(),
        "paused": False,
        "game_over": False,
        "victory_screen": False,
        "settings_open": False,
        "controls_open": False,
        "credits_open": False,
        "achievements_screen": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_cursor_hidden_during_active_gameplay():
    should_hide = _load_should_hide_cursor()
    assert should_hide(_state()) is True


def test_cursor_visible_when_esc_opens_pause_menu():
    should_hide = _load_should_hide_cursor()
    assert should_hide(_state(paused=True)) is False


def test_cursor_visible_on_other_game_screens():
    should_hide = _load_should_hide_cursor()
    for flag in ("settings_open", "controls_open", "game_over", "victory_screen"):
        assert should_hide(_state(**{flag: True})) is False


def test_cursor_visible_outside_a_selected_level():
    should_hide = _load_should_hide_cursor()
    assert should_hide(_state(game_started=False, level_selected=False, level=None)) is False


def test_cursor_visibility_is_synced_before_each_screen_draw():
    tree = ast.parse(GAME_SOURCE.read_text(encoding="utf-8"))
    game_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Game")
    draw_method = next(node for node in game_class.body if isinstance(node, ast.FunctionDef) and node.name == "draw")
    first = draw_method.body[0]
    assert isinstance(first, ast.Expr)
    assert isinstance(first.value, ast.Call)
    assert isinstance(first.value.func, ast.Attribute)
    assert first.value.func.attr == "_sync_cursor_visibility"
