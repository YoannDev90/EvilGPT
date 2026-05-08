import logging
import time
from logging import Handler
from typing import Optional

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

LOGGER_NAME = "EvilGPT"


class EvilGPTFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == LOGGER_NAME


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


class DiscordAnsiFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: "\x1b[36m",
        logging.INFO: "\x1b[32m",
        logging.WARNING: "\x1b[33m",
        logging.ERROR: "\x1b[31m",
        logging.CRITICAL: "\x1b[1;31m",
    }

    RESET = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = self.LEVEL_COLORS.get(record.levelno, "\x1b[37m")
        return f"```ansi\n{color}{message}{self.RESET}\n```"


class DiscordWebhookHandler(Handler):
    def __init__(self, webhook_url: str, level: int = logging.INFO):
        super().__init__(level)
        self.webhook_url = webhook_url

    @staticmethod
    def _level_color(levelno: int) -> int:
        palette = {
            logging.DEBUG: 0x3498DB,
            logging.INFO: 0x2ECC71,
            logging.WARNING: 0xF1C40F,
            logging.ERROR: 0xE74C3C,
            logging.CRITICAL: 0x992D22,
        }
        return palette.get(levelno, 0x95A5A6)

    def _build_payload(self, record: logging.LogRecord) -> dict:
        message = self.format(record)
        payload = {
            "username": "EvilGPT",
            "allowed_mentions": {"parse": []},
        }

        payload["content"] = message
        return payload

    @staticmethod
    def _split_payload_chunks(message: str, limit: int = 1900) -> list[str]:
        if len(message) <= limit:
            return [message]

        chunks: list[str] = []
        start = 0
        while start < len(message):
            end = min(start + limit, len(message))
            if end < len(message):
                newline = message.rfind("\n", start, end)
                if newline > start:
                    end = newline + 1
            chunks.append(message[start:end])
            start = end
        return chunks

    def emit(self, record: logging.LogRecord) -> None:
        try:
            import requests

            payload = self._build_payload(record)
            headers = {"Content-Type": "application/json"}
            # Retry on transient network/rate-limit failures.
            chunks = self._split_payload_chunks(payload["content"])
            for index, chunk in enumerate(chunks, start=1):
                chunk_payload = dict(payload)
                chunk_payload["content"] = chunk
                if len(chunks) > 1:
                    chunk_payload["content"] = (
                        f"{chunk_payload['content']}\n\n[{index}/{len(chunks)}]"
                    )

                for attempt in range(3):
                    response = requests.post(
                        self.webhook_url,
                        json=chunk_payload,
                        headers=headers,
                        timeout=8,
                    )
                    if response.status_code == 429:
                        retry_after = response.json().get("retry_after", 1)
                        time.sleep(float(retry_after))
                        continue
                    response.raise_for_status()
                    break
        except Exception as exc:
            print(f"Failed to send log to Discord webhook: {exc}")
            try:
                # Use discord-webhook package for sending
                from discord_webhook import DiscordEmbed, DiscordWebhook

                message = self.format(record)

                # If message short enough, send as content; otherwise use embed description
                if len(message) <= 1900:
                    webhook = DiscordWebhook(url=self.webhook_url, content=message)
                    webhook.execute()
                    return

                embed = DiscordEmbed(
                    title=f"{record.filename}",
                    description=message[:4096],
                    color=self._level_color(record.levelno),
                )
                webhook = DiscordWebhook(url=self.webhook_url)
                webhook.add_embed(embed)
                webhook.execute()
            except Exception as exc:
                # Do not attempt fallback; just print error for debugging
                print(f"Failed to send log to Discord webhook (discord-webhook): {exc}")


def _is_real_webhook_url(url: Optional[str]) -> bool:
    return bool(url) and "<URL>" not in url


def setup_logging(level: int = logging.INFO, config=None):
    """Set up logging.

    If `config` provided and has file/webhook settings, those will be used.
    """
    console_format = getattr(config, "console_format")
    file_format = getattr(config, "file_format")
    discord_format = getattr(config, "discord_format")

    handlers = []

    # stream handler
    if (
        config is None
        or getattr(config, "console", None) is None
        or getattr(config.console, "enable", True)
    ):
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter(console_format))
        handler.addFilter(EvilGPTFilter())
        handlers.append(handler)

    # optional file handler
    if config is not None and getattr(config, "enable_file_logging", False):
        try:
            fh = logging.FileHandler(getattr(config, "log_file", "logs/evilgpt.log"))
            fh.setFormatter(logging.Formatter(file_format))
            fh.addFilter(EvilGPTFilter())
            handlers.append(fh)
        except Exception:
            pass

    # optional discord webhook
    if (
        config is not None
        and getattr(config, "enable_discord_logging", False)
        and _is_real_webhook_url(getattr(config, "discord_webhook", None))
    ):
        try:
            dh = DiscordWebhookHandler(getattr(config, "discord_webhook"))
            dh.setFormatter(DiscordAnsiFormatter(discord_format))
            handlers.append(dh)
        except Exception:
            pass

    logging.basicConfig(level=level, handlers=handlers, force=True)

    # Dynamically silence all loggers except our own
    for name in list(logging.root.manager.loggerDict.keys()):
        if name == LOGGER_NAME or name.startswith(f"{LOGGER_NAME}."):
            continue
        lib_logger = logging.getLogger(name)
        lib_logger.setLevel(logging.CRITICAL)
        lib_logger.propagate = False
        # Still attach our handlers to catch CRITICAL errors in files/discord
        for handler in handlers:
            if handler not in lib_logger.handlers:
                lib_logger.addHandler(handler)


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)
