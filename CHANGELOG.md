## 1.1.0
- Easy difficulty now uses the supplied Adventure tileset for ground, static platforms, and moving platforms.
- The Adventure tiles and silhouettes are bundled under `assets/tilesets/adventure_easy/`.
- Normal and Hard terrain renderers remain unchanged.

# Changelog

## 1.0.0
- Single attack path for mouse clicks (no double attack on right-click).
- Player animation frames are cached; no Level is built at startup.
- Settings screen (music/sound volume, fullscreen), controls screen with key rebinding.
- Hurt feedback: screen shake, red flash, invincibility blink. Level 1 tutorial hints.
- Credits screen after the last level.
- Password minimum 6 characters, login lockout after 5 wrong tries; passwords show as `*`.
- Autosave on checkpoint, quit and returning to menu; save files have a version number.
- Accounts, saves and settings live in the per-user app-data folder (old data is migrated).
- Enemies far from the player are no longer updated or drawn.
- Logging to `veggiequest.log`; difficulty passed explicitly instead of a global.
- Tests, `.gitignore`, `pyproject.toml`, PyInstaller spec, new README.
