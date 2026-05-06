import logging

from bot import run_bot
from core.config import logging_cfg
from core.models_loader import get_model_catalog
from utils.logger import get_logger, setup_logging

setup_logging(
    level=getattr(logging, str(logging_cfg.level).upper(), logging.INFO),
    config=logging_cfg,
)
logger = get_logger(__name__)


def print_model_catalog():
    catalog = get_model_catalog()
    print("\nAvailable models:")
    print("-" * 86)
    print(f"{'STATUS':<12} {'PROVIDER':<16} {'MODEL':<44} LITELLM")
    print("-" * 86)
    for entry in catalog:
        status = "READY" if entry["api_key_set"] else "NO_KEY"
        provider = entry["provider"].upper()
        model = entry["model"]
        litellm_id = entry["litellm_id"]
        print(f"{status:<12} {provider:<16} {model:<44} {litellm_id}")
    print("-" * 86)


if __name__ == "__main__":
    try:
        logger.info("Démarrage de l'application EvilGPT...")
        print_model_catalog()
        run_bot()
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur.")
    except Exception as e:
        logger.error("Erreur fatale: %s", e, exc_info=True)
