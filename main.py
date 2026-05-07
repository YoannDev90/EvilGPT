import logging

from bot import run_bot
from core.config import logging_cfg
from utils.logger import get_logger, setup_logging

setup_logging(
    level=getattr(logging, str(logging_cfg.level).upper(), logging.INFO),
    config=logging_cfg,
)
logger = get_logger()

if __name__ == "__main__":
    try:
        logger.info("Démarrage de l'application EvilGPT...")
        run_bot()
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur.")
    except Exception as e:
        logger.error("Erreur fatale: %s", e, exc_info=True)
