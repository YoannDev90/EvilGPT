import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

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
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(message)s"
    enable_file_logging: bool = True
    log_file: str = "logs/evilgpt.log"
    enable_discord_logging: bool = False
    discord_webhook: Optional[str] = None


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


def load_config(config_path: Optional[str] = None) -> (Config, LoggingConfig):
    toml_path = config_path or DEFAULT_CONFIG_PATH
    raw = _load_toml(toml_path)

    # Logging
    raw_logging = raw.get("logging", {}) if isinstance(raw, dict) else {}
    logging_conf = LoggingConfig(
        level=raw_logging.get("level", "INFO"),
        format=raw_logging.get("format", "%(asctime)s - %(name)s - %(message)s"),
        enable_file_logging=raw_logging.get("enable_file_logging", True),
        log_file=raw_logging.get("log_file", "logs/evilgpt.log"),
        enable_discord_logging=raw_logging.get("enable_discord_logging", False),
        discord_webhook=raw_logging.get("discord_webhook") or None,
    )

    cfg = Config()
    cfg.BOT_TOKEN = os.getenv("BOT_TOKEN")
    cfg.WEBHOOK_POSTURL = os.getenv("WEBHOOK_URL") or os.getenv("WEBHOOK_POSTURL")

    # Determine final webhook URL: priority - env WEBHOOK_URL, logging.discord_webhook, combine webhook_base + posturl
    if os.getenv("WEBHOOK_URL"):
        cfg.WEBHOOK_URL = os.getenv("WEBHOOK_URL")
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
