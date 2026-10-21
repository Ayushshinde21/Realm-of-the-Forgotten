"""Build Normal levels 1-10 across many seeds and verify generation invariants.

Run from the project root with Pygame installed:
    python scripts/validate_normal_generation.py --seeds 200

All save/settings output is redirected to a temporary directory so real user
progress is never read or overwritten by this validation run.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=200)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be at least 1")

    with tempfile.TemporaryDirectory(prefix="vegquest-normal-validation-") as data_dir:
        os.environ["VEGGIEQUEST_DATA_DIR"] = data_dir
        import pygame

        pygame.init()
        pygame.display.set_mode((1280, 720))

        from src.settings import MAX_LEVELS, WORLD_HEIGHT
        from src.world.level import Level
        from src.world.level_data import LEVELS
        from src.world.platform_generator import PlatformGenerator

        worlds_checked = 0
        moving_platforms_checked = 0
        checkpoints_checked = 0
        try:
            for level_number in range(1, MAX_LEVELS + 1):
                width = LEVELS["normal"][level_number]["world_width"]
                progress = (level_number - 1) / max(1, MAX_LEVELS - 1)

                for seed in range(args.seeds):
                    random.seed(seed)
                    generator = PlatformGenerator(width, world_height=WORLD_HEIGHT)
                    generator.platform_size_multiplier = 2.0
                    generator.base_difficulty = 0.8 + progress * 1.4
                    generated = generator.generate()
                    if not generated:
                        raise AssertionError(f"No platforms: level={level_number}, seed={seed}")

                    # Adjacent generated gaps must remain within the player's
                    # safe horizontal jump distance.
                    for left, right in zip(generated, generated[1:]):
                        gap = right.rect.left - left.rect.right
                        if gap > generator.max_jump_distance:
                            raise AssertionError(
                                f"Unsafe gap {gap}: level={level_number}, seed={seed}"
                            )

                    level = Level(seed=seed, level_number=level_number, difficulty="normal")
                    if abs(level.finish_x - (level.width - 200)) > 400:
                        raise AssertionError(f"Finish drift: level={level_number}, seed={seed}")
                    if level.width > 3000 and not level.checkpoints:
                        raise AssertionError(f"Missing checkpoint: level={level_number}, seed={seed}")
                    if level_number == 1 and len(level.moving_platforms) < 2:
                        raise AssertionError(f"Level 1 has fewer than 2 moving platforms: seed={seed}")

                    for moving in level.moving_platforms:
                        sweep, max_down = level._normal_moving_platform_sweep(
                            moving.start_x,
                            moving.start_y,
                            moving.rect.width,
                            moving.rect.height,
                            moving.movement_type,
                            abs(int(moving.movement_distance)),
                        )
                        if any(sweep.colliderect(static.rect) for static in level.platforms):
                            raise AssertionError(
                                f"Moving-platform sweep intersects static terrain: level={level_number}, seed={seed}"
                            )
                        if moving.movement_type == "vertical":
                            if moving.start_y > level.ground.rect.top - 80:
                                raise AssertionError("Vertical platform starts too close to ground")
                            if moving.start_y + max_down + moving.rect.height > level.ground.rect.top - 40:
                                raise AssertionError("Vertical platform descends too close to ground")
                        moving_platforms_checked += 1
                    checkpoints_checked += len(level.checkpoints)
                    worlds_checked += 1

            print(
                f"PASS: {worlds_checked} Normal level builds ({args.seeds} seeds x {MAX_LEVELS} levels); "
                f"{moving_platforms_checked} moving platforms checked; "
                f"{checkpoints_checked} checkpoints checked."
            )
            return 0
        finally:
            pygame.quit()


if __name__ == "__main__":
    raise SystemExit(main())
