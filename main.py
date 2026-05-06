from bot import run_bot
from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Démarrage de l'application EvilGPT...")
        run_bot()
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur.")
    except Exception as e:
        logger.error("Erreur fatale: %s", e, exc_info=True)
