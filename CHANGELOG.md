## Normal Difficulty — Movement and enemy-size fixes (October 21, 2026)

- Prevent Normal moving platforms from travelling above the playable player-height boundary, where the player could be pushed out of alignment and lose platform support.
- Preserve fractional horizontal movement for Normal zombies so speeds below 1 pixel per frame accumulate correctly instead of being truncated to zero.
- Increase Normal zombie sprite height by 25% and slightly increase run-animation cadence; Easy and Hard enemy sizing and movement paths remain unchanged.
- Added regression coverage for the moving-platform safe height and Normal zombie movement/scale.

## Normal Difficulty — Zombie Enemy Replacement (latest)

- Replaced Normal's worker, soldier, boxer, minebot, chopper, and hammerbot appearances with seven variants from the two supplied zombie sprite packs.
- Added cached spritesheet slicing for idle, walk/run, attack, hurt, and death animations, with frame aliases for each pack's naming conventions.
- Kept the existing Normal spawn distribution and platform placement approach, while giving zombie variants differentiated size, detection, attack reach, recovery, and movement speeds.
- Easy's slime/swordsman enemies and Hard's enemy roster remain on their existing paths.

## Normal Difficulty — Green Zone Environment (latest)

- Replaced the Normal-only Industrial Zone environment with the supplied Green Zone pack in `assets/tilesets/green_zone/`.
- Added cached loading for 96 individual 32px tiles, day/night background layers, tree and stone props, static fountains, and sliced Fountain/Money animation sheets.
- Rebuilt Normal ground and platforms with green turf, forest soil, rock ledges, grass-edged pits, and matching moving-platform visuals.
- Added deterministic non-colliding tree, stone, and animated fountain decorations. Levels 1–5 use day artwork and levels 6–10 use night artwork.
- Preserved Normal generation, collisions, level widths, checkpoints, collectibles, and progression. Easy and Hard render paths remain isolated from this replacement.

## Normal difficulty procedural generation reliability
- Clamp platform gap and width/height-change bounds so random ranges stay valid and generated gaps do not exceed the safe jump distance.
- Generate Normal moving platforms from the seeded layout, preferring pit/gap locations and rejecting any full movement sweep that intersects static terrain; preserve Easy/Hard placements.
- Retry nearby checkpoint platform candidates and guarantee a Normal checkpoint in levels wider than 3,000px.
- Reserve the intended finish area near `world_width - 200`, clear blocking geometry there, protect the initial Normal spawn corridor, and predict pit-ground collision using the next-frame bottom.
- Added Normal generation regression and 200-seed stress tests for levels 1–10.

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

## Normal Difficulty — Industrial Zone Environment

- Replaced the legacy Normal-only tilesheet dependency with the supplied Industrial Zone pack organized under `assets/tilesets/industrial_zone/`.
- Added cached loading for 81 individual 32px tiles, 6 background images/layers, 44 props, and 12 horizontally sliced animation sheets.
- Rebuilt Normal backgrounds with layered industrial silhouettes and parallax, steel ground/platform skins, conveyor-style moving-platform visuals, warning-striped pit lips, and vertical industrial structures.
- Added deterministic, non-colliding decorations on ground and wide static platforms, with animated screens and transporter machinery.
- Kept all industrial rendering calls under Normal-difficulty branches; Easy and Hard retain their prior environment rendering and gameplay geometry.
