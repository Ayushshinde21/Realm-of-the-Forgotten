import hashlib
import hmac
import json
import logging
import os
import time

from src import paths

log = logging.getLogger("veggiequest.accounts")

MIN_USERNAME_LENGTH = 3
MIN_PASSWORD_LENGTH = 6

# Login lockout: after MAX_FAILED_ATTEMPTS wrong passwords in a row for one
# username, further attempts are refused for LOCKOUT_SECONDS. Kept in memory
# (it resets when the game restarts), which is enough to slow down guessing.
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 30

_failed = {}  # normalized username -> [failed_count, locked_until_monotonic]


def _now():
    return time.monotonic()


def _read():
    path = paths.accounts_file()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        log.exception("Could not read accounts file %s", path)
        return {}


def _write(accounts):
    path = paths.accounts_file()
    try:
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=4)
        os.replace(tmp, path)
        return True
    except OSError:
        log.exception("Could not write accounts file %s", path)
        return False


def _hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return salt.hex() + "$" + digest.hex()


def _verify_password(password, stored):
    if "$" not in stored:  # old unsalted SHA-256 hash: existing accounts keep working
        old = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(old, stored)
    salt_hex, digest_hex = stored.split("$", 1)
    new = _hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
    return hmac.compare_digest(new, digest_hex)


def _normalize(username):
    return (username or "").strip().lower()


def username_exists(username):
    """Case-insensitive check for whether a username is already registered."""
    return _normalize(username) in _read()


def register_account(username, password, confirm_password=None):
    """Create a new account with a unique, case-insensitive username.

    Returns (success: bool, message: str).
    """
    raw_username = (username or "").strip()
    key = _normalize(raw_username)

    if not raw_username:
        return False, "Username cannot be empty."
    if len(raw_username) < MIN_USERNAME_LENGTH:
        return False, f"Username must be at least {MIN_USERNAME_LENGTH} characters."
    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match."
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."

    accounts = _read()
    if key in accounts:
        return False, "Username already exists. Please choose another username."

    accounts[key] = {
        "display_name": raw_username,
        "password_hash": _hash_password(password),
    }
    if not _write(accounts):
        return False, "Could not save account. Try again."
    return True, "Account created successfully!"


def authenticate(username, password):
    """Verify login credentials.

    Returns (success: bool, display_name: str | None, message: str).
    Does not reveal whether the username or the password was the
    incorrect part.
    """
    key = _normalize(username)

    count, locked_until = _failed.get(key, (0, 0.0))
    remaining = locked_until - _now()
    if remaining > 0:
        return False, None, f"Too many attempts. Try again in {int(remaining) + 1}s."

    accounts = _read()
    account = accounts.get(key)
    if account is None or not _verify_password(password or "", account.get("password_hash", "")):
        count += 1
        if count >= MAX_FAILED_ATTEMPTS:
            _failed[key] = [0, _now() + LOCKOUT_SECONDS]
            log.warning("Login locked for %d seconds after repeated failures", LOCKOUT_SECONDS)
            return False, None, f"Too many attempts. Try again in {LOCKOUT_SECONDS}s."
        _failed[key] = [count, 0.0]
        return False, None, "Invalid username or password."

    _failed.pop(key, None)
    return True, account.get("display_name", key), "Login successful!"
