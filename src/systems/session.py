"""Tracks the single currently logged-in user for this game session."""

_current_user = None       # normalized (lowercase) username, used for save file lookup
_display_name = None       # username as originally typed at registration


def set_current_user(username, display_name=None):
    global _current_user, _display_name
    if not username:
        _current_user = None
        _display_name = None
        return
    _current_user = username.strip().lower()
    _display_name = (display_name or username).strip()


def get_current_user():
    """Returns the normalized (lowercase) username, or None if logged out."""
    return _current_user


def get_display_name():
    """Returns the username in its original casing, or None if logged out."""
    return _display_name


def is_logged_in():
    return _current_user is not None


def logout():
    global _current_user, _display_name
    _current_user = None
    _display_name = None
