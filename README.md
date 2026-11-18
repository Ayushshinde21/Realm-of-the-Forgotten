# Veggie Quest: Rescue at Snackland

A 2D pixel-art platformer made with Python and pygame. Fight your way through
one 20-level campaign split across two worlds, collect coins, rescue Snackland,
and earn up to 3 stars per level. World 1 is **Snackland Meadows** (levels 1-10);
World 2 is **Greenwild Frontier** (levels 11-20). Challenge increases as the
player progresses, and the active world is selected automatically by level.

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


## World 1 — Snackland Meadows

World 1 uses the Adventure tileset in `assets/tilesets/adventure_easy/`, the
fighter sprite sheets in `assets/fighter/`, animated thorn hazards, and the
slime/swordsman enemy roster. Thorn contact slows movement and jumping by 5x
and deals 2 hearts of damage per second while contact continues.

## World 2 — Greenwild Frontier

World 2 uses the Green Zone pack under `assets/tilesets/green_zone/`, the
Gangsters_2 player sprite sheets under `assets/gangster/`, animated coins, and
seven animated zombie variants. Its layered forest backgrounds transition
from daylight to the night palette during the second half of the world.
Decorative placements are deterministic for a given level seed and do not add
collisions or change gameplay geometry.

## Campaign progression

The level-select screen shows both worlds and all 20 global level numbers.
World 1 contains levels 1-10; completing level 10 unlocks World 2 level 11.
The game automatically chooses the correct world content and gradually raises
platform and enemy pressure as the campaign level increases. Save files from
the former Easy and Normal campaigns are migrated into the unified progression.

