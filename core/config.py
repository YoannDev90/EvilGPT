import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

try:
    import tomllib as _toml
except Exception:
    try:
        import toml as _toml
    except Exception:
        _toml = None

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    print(
        "Warning: python-dotenv not installed, environment variables from .env will not be loaded."
    )

# base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "config.toml")


def _load_toml(path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    if _toml is None:
        return {}
    if os.path.exists(path):
        with open(
            path,
            "rb"
            if hasattr(_toml, "loads")
            and _toml is not None
            and hasattr(_toml, "__name__")
            and _toml.__name__ == "tomllib"
            else "r",
            encoding=None
            if hasattr(_toml, "loads")
            and _toml is not None
            and hasattr(_toml, "__name__")
            and _toml.__name__ == "tomllib"
            else "utf-8",
        ) as f:
            # tomllib expects bytes I/O in py3.11, toml package expects text
            if getattr(_toml, "__name__", "") == "tomllib":
                return _toml.load(f)
            else:
                return _toml.load(f)
    return {}


def read_from_toml_config(
    param: str, config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    cfg = config or _load_toml()
    return cfg.get(param, {}) if isinstance(cfg.get(param, {}), dict) else {}


@dataclass
class ConsoleLoggingConfig:
    enable: bool = True
    level: str = "INFO"
    console_format: str = "%(asctime)s - %(message)s"


@dataclass
class FileLoggingConfig:
    enable_file_logging: bool = True
    log_file: str = "logs/evilgpt.log"

    # file logs can keep more context; filename is more useful than logger name
    file_format: str = "%(asctime)s - %(filename)s - %(message)s"


@dataclass
class DiscordLoggingConfig:
    enable_discord_logging: bool = False
    discord_webhook: Optional[str] = None
    discord_format: str = "%(asctime)s - %(filename)s\n%(message)s"


@dataclass
class LoggingConfig:
    console: ConsoleLoggingConfig
    file: FileLoggingConfig
    discord: DiscordLoggingConfig

    @property
    def level(self) -> str:
        return self.console.level

    @property
    def enable_file_logging(self) -> bool:
        return self.file.enable_file_logging

    @property
    def log_file(self) -> str:
        return self.file.log_file

    @property
    def enable_discord_logging(self) -> bool:
        return self.discord.enable_discord_logging

    @property
    def discord_webhook(self) -> Optional[str]:
        return self.discord.discord_webhook

    @property
    def console_format(self) -> str:
        return self.console.console_format

    @property
    def file_format(self) -> str:
        return self.file.file_format

    @property
    def discord_format(self) -> str:
        return self.discord.discord_format


@dataclass
class Config:
    BOT_TOKEN: Optional[str] = None
    WEBHOOK_POSTURL: Optional[str] = None
    WEBHOOK_URL: Optional[str] = None

    # Path to system prompt and data
    BASE_DIR: str = BASE_DIR
    SYSTEM_PROMPT_PATH: str = os.path.join(BASE_DIR, "data", "system_prompt.txt")
    PROVIDERS_PATH: str = os.path.join(BASE_DIR, "data", "providers.json")
    MODELS_PATH: str = os.path.join(BASE_DIR, "data", "models.json")
    CONFIG_PATH: str = DEFAULT_CONFIG_PATH


def _first_table(items: Any) -> Dict[str, Any]:
    if isinstance(items, list) and items:
        return items[0] if isinstance(items[0], dict) else {}
    if isinstance(items, dict):
        return items
    return {}


def _normalize_webhook_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if "<URL>" in url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://discord.com/api/webhooks/{url.lstrip('/')}"


def load_config(config_path: Optional[str] = None) -> Tuple[Config, LoggingConfig]:
    toml_path = config_path or DEFAULT_CONFIG_PATH
    raw = _load_toml(toml_path)

    raw_logging = raw.get("logging", {}) if isinstance(raw, dict) else {}
    console_raw = _first_table(raw.get("console"))
    file_raw = _first_table(raw.get("file"))
    discord_raw = _first_table(raw.get("discord"))

    # Backward compatibility with previous flat schema if present under [logging]
    console_conf = ConsoleLoggingConfig(
        enable=console_raw.get("enable", raw_logging.get("enable", True)),
        level=console_raw.get("level", raw_logging.get("level", "INFO")),
        console_format=console_raw.get(
            "console_format",
            raw_logging.get("console_format", "%(asctime)s - %(message)s"),
        ),
    )
    file_conf = FileLoggingConfig(
        enable_file_logging=file_raw.get(
            "enable_file_logging", raw_logging.get("enable_file_logging", True)
        ),
        log_file=file_raw.get(
            "log_file", raw_logging.get("log_file", "logs/evilgpt.log")
        ),
        file_format=file_raw.get(
            "file_format",
            raw_logging.get("file_format", "%(asctime)s - %(filename)s - %(message)s"),
        ),
    )
    discord_conf = DiscordLoggingConfig(
        enable_discord_logging=discord_raw.get(
            "enable_discord_logging",
            raw_logging.get("enable_discord_logging", False),
        ),
        discord_webhook=_normalize_webhook_url(
            discord_raw.get("discord_webhook")
            or raw_logging.get("discord_webhook")
            or None
        ),
        discord_format=discord_raw.get(
            "discord_format",
            raw_logging.get(
                "discord_format", "%(asctime)s - %(filename)s\n%(message)s"
            ),
        ),
    )

    logging_conf = LoggingConfig(
        console=console_conf,
        file=file_conf,
        discord=discord_conf,
    )

    cfg = Config()
    cfg.BOT_TOKEN = os.getenv("BOT_TOKEN")
    cfg.WEBHOOK_POSTURL = os.getenv("WEBHOOK_URL") or os.getenv("WEBHOOK_POSTURL")

    env_webhook_url = _normalize_webhook_url(os.getenv("WEBHOOK_URL"))

    # Determine final webhook URL: priority - env WEBHOOK_URL, logging.discord_webhook, combine webhook_base + posturl
    if env_webhook_url:
        cfg.WEBHOOK_URL = env_webhook_url
    elif logging_conf.discord_webhook:
        cfg.WEBHOOK_URL = logging_conf.discord_webhook
    else:
        # combine base + posturl if present
        root_webhook_base = raw.get("webhook_base") or raw.get("webhook", {}).get(
            "base"
        )
        if root_webhook_base and cfg.WEBHOOK_POSTURL:
            cfg.WEBHOOK_URL = (
                root_webhook_base.rstrip("/") + "/" + cfg.WEBHOOK_POSTURL.lstrip("/")
            )

    cfg.CONFIG_PATH = toml_path
    return cfg, logging_conf


# load default config at import time
cfg, logging_cfg = load_config()


def read_system_prompt() -> Optional[str]:
    if os.path.exists(cfg.SYSTEM_PROMPT_PATH):
        with open(cfg.SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None
