# Veggie Quest: Rescue at Snackland

A 2D pixel-art platformer made with Python and pygame. Fight your way through
10 levels on three difficulties (easy, normal, hard), collect coins, rescue
Snackland and earn up to 3 stars per level.

Version: see `VERSION` in `src/settings.py` (also shown on the main menu).

<!-- Add a screenshot here:  ![Screenshot](docs/screenshot.png) -->

## Controls

| Action | Default key |
|---|---|
| Move | `A` / `D` or the arrow keys |
| Jump | `Space` |
| Attack | Left or right mouse button |
| Talk / interact | `E` |
| Pause | `Esc` |
| Fullscreen | `F11` |

Move, jump and interact can be rebound in **Settings > Controls**. Settings
also has music and sound volume sliders and a fullscreen toggle.

## Install and run

You need Python 3.10 or newer.

```
pip install -r requirements.txt
python main.py
```

## Where your data is saved

Accounts, saves and settings are stored in your user folder, not next to the
game, so updating the game never overwrites them:

* Windows: `%APPDATA%\VeggieQuest`
* macOS: `~/Library/Application Support/VeggieQuest`
* Linux: `~/.local/share/VeggieQuest`

Progress is saved at every checkpoint, when a level is completed, when you
return to the main menu and when you quit. Errors are written to
`veggiequest.log` in the same folder. Saves from older versions (the
`accounts.json` and `save_data/` next to the game) are copied over automatically
the first time you start the game.

## Development

```
pip install -r requirements-dev.txt
pytest            # automated tests (accounts, saves, settings, scoring)
black .           # format
ruff check .      # lint
```

## Build a .exe for friends (Windows)

```
pip install -r requirements-dev.txt
pyinstaller VeggieQuest.spec
```

Zip the `dist/VeggieQuest` folder and share it; no Python is needed to run it.

## Project layout

* `main.py` - entry point
* `src/game.py` - main loop and screen flow
* `src/world/` - levels, platform generation, camera
* `src/entities/` - player, enemies, items
* `src/systems/` - accounts, saves, achievements, session
* `src/ui/` - menus and screens
* `src/paths.py` - every file location in one place
* `tests/` - automated tests


## Animated Slime Enemies

The Green, Blue, and Red Slime sprite sheets are integrated as animated enemies. Their idle, run, attack, hurt, and death frames are stored under `assets/enemies/`. Easy uses only these three slime variants, with Green most common, slightly enlarged sprites, and no rocks or bushes. Hard retains its existing enemy and obstacle generation; Normal keeps its industrial robot enemy roster.

The source sprite package also contains jump, walk, and run-attack sheets; the current integration uses the five gameplay states needed by the existing enemy AI.

## Easy-only fighter character

Easy difficulty uses the fighter sprite sheets in `assets/fighter/` for idle,
run, jump, attack, and death animations. Normal and Hard continue to use the
original player sprites under `assets/player/`.

### Difficulty-specific terrain

Easy difficulty uses the Adventure tileset bundled in `assets/tilesets/adventure_easy/`. Normal keeps the industrial tileset and Hard keeps its existing terrain rendering.

Easy also replaces generated pits with animated thorn patches. Thorn contact slows movement and jumping by 5x and deals 2 hearts of damage per second while contact continues; Normal and Hard retain their existing pit behavior.
