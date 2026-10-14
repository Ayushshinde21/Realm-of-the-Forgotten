import hashlib
import json

from src import paths
from src.systems import account_system as acc


def test_register_and_login():
    ok, _ = acc.register_account("Alice", "secret1", "secret1")
    assert ok
    ok, name, _ = acc.authenticate("alice", "secret1")
    assert ok and name == "Alice"


def test_username_unique_case_insensitive():
    acc.register_account("Alice", "secret1")
    ok, msg = acc.register_account("ALICE", "another1")
    assert not ok and "exists" in msg


def test_password_rules():
    ok, _ = acc.register_account("Bob", "12345")  # 5 < minimum of 6
    assert not ok
    ok, _ = acc.register_account("Bob", "abcdef", "abcdeg")
    assert not ok
    ok, _ = acc.register_account("Bob", "abcdef", "abcdef")
    assert ok


def test_wrong_password_and_lockout():
    acc.register_account("Carol", "secret1")
    for _ in range(acc.MAX_FAILED_ATTEMPTS - 1):
        ok, _, msg = acc.authenticate("carol", "nope")
        assert not ok and msg == "Invalid username or password."
    ok, _, msg = acc.authenticate("carol", "nope")
    assert not ok and "Too many attempts" in msg
    # Even the right password is refused while locked out.
    ok, _, msg = acc.authenticate("carol", "secret1")
    assert not ok and "Too many attempts" in msg


def test_lockout_expires(monkeypatch):
    acc.register_account("Dave", "secret1")
    for _ in range(acc.MAX_FAILED_ATTEMPTS):
        acc.authenticate("dave", "bad")
    t = acc._now()
    monkeypatch.setattr(acc, "_now", lambda: t + acc.LOCKOUT_SECONDS + 1)
    ok, _, _ = acc.authenticate("dave", "secret1")
    assert ok


def test_legacy_sha256_hash_still_works():
    legacy = hashlib.sha256(b"oldpass").hexdigest()
    paths.accounts_file().write_text(
        json.dumps({"old": {"display_name": "Old", "password_hash": legacy}})
    )
    ok, name, _ = acc.authenticate("old", "oldpass")
    assert ok and name == "Old"


def test_corrupted_accounts_file_does_not_crash():
    paths.accounts_file().write_text("{ not json")
    ok, _, _ = acc.authenticate("anyone", "x")
    assert not ok
    ok, _ = acc.register_account("Eve", "secret1")
    assert ok
