import logging
import sys

from bot import run_bot


def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


if __name__ == "__main__":
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting EvilGPT Discord bot...")
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)
