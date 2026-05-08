import logging
import os
import sys

# Trigger imports for all modules that might register loggers
import bot
from core import model, models_loader, tools
# Import everything to ensure all loggers are registered before setup_logging
from core.config import logging_cfg
from managers import context, mcp, memory
from utils import web_search
from utils.handlers import codeblock, latex, messages, table
from utils.logger import get_logger, setup_logging

setup_logging(
    level=getattr(logging, str(logging_cfg.level).upper(), logging.INFO),
    config=logging_cfg,
)
logger = get_logger()

if __name__ == "__main__":
    try:
        logger.info("Démarrage de l'application EvilGPT...")
        bot.run_bot()
    except KeyboardInterrupt:
        print("\n")  # New line for cleaner exit
        logger.info("Arrêt demandé par l'utilisateur (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        logger.error("Erreur fatale: %s", e, exc_info=True)
        sys.exit(1)
