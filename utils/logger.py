import logging
from logging import Handler
from typing import Optional

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

LOGGER_NAME = "EvilGPT"


class EvilGPTFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == LOGGER_NAME or record.name.startswith(f"{LOGGER_NAME}.")


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"


class DiscordWebhookHandler(Handler):
    def __init__(self, webhook_url: str, level: int = logging.INFO):
        super().__init__(level)
        self.webhook_url = webhook_url

    def emit(self, record: logging.LogRecord) -> None:
        try:
            import requests

            msg = self.format(record)
            data = {"content": msg}
            requests.post(self.webhook_url, json=data, timeout=5)
        except Exception:
            pass


def setup_logging(level: int = logging.INFO, config=None):
    """Set up logging.

    If `config` provided and has file/webhook settings, those will be used.
    """
    # stream handler
    handler = logging.StreamHandler()
    handler.setFormatter(
        ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    handler.addFilter(EvilGPTFilter())

    handlers = [handler]

    # optional file handler
    if config is not None and getattr(config, "enable_file_logging", False):
        try:
            fh = logging.FileHandler(getattr(config, "log_file", "logs/evilgpt.log"))
            fh.setFormatter(
                logging.Formatter(
                    getattr(
                        config,
                        "format",
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    )
                )
            )
            fh.addFilter(EvilGPTFilter())
            handlers.append(fh)
        except Exception:
            pass

    # optional discord webhook
    if (
        config is not None
        and getattr(config, "enable_discord_logging", False)
        and getattr(config, "discord_webhook", None)
    ):
        try:
            dh = DiscordWebhookHandler(getattr(config, "discord_webhook"))
            dh.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            handlers.append(dh)
        except Exception:
            pass

    logging.basicConfig(level=level, handlers=handlers, force=True)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or LOGGER_NAME)
