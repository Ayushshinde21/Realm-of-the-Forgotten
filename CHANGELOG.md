## Vertical moving-platform ground clearance
- Vertical moving platforms now begin by rising and use an asymmetric movement range.
- Their lowest point remains at least 40px above the ground, preventing platforms from dipping into or touching the floor.
- Horizontal moving-platform motion is unchanged.

## Easy-only thorn hazards
- Replaced generated Easy-difficulty pits with animated thorn patches using the supplied eight-frame sprite strip; the ground remains solid.
- Thorn contact reduces player speed and jump strength by 5x and drains 2 hearts per second.
- Normal and Hard pit behavior remains unchanged.

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

## Moving-platform ride stability
- Carry grounded players with moving platforms before applying gravity and resolving collisions, preventing an extra downward step at the platform's lower reversal point.
- Landing checks now accept exact edge contact while still requiring horizontal overlap, so a player remains supported when vertical movement rounds to a zero-pixel step.
- Added a regression test for carry/collision update ordering.
