import logging
import os

from src import paths
from src.logging_setup import setup_logging

# Always run from the folder that holds the assets.
os.chdir(paths.BASE_DIR)
setup_logging()
paths.migrate_legacy_data()

from src.game import Game  # noqa: E402  (must come after chdir/logging setup)

log = logging.getLogger("veggiequest.main")


def main():
    game = Game()
    try:
        game.run()
    except Exception:
        log.exception("Unhandled error - game crashed")
        raise


if __name__ == "__main__":
    main()
