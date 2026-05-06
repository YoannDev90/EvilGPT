import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")
    GRATISFY_API_BASE: str = os.getenv(
        "GRATISFY_API_BASE", "https://api.gratisfy.xyz/v1"
    )
    GRATISFY_API_KEY: Optional[str] = os.getenv("GRATISFY_API_KEY")

    # Path to system prompt and data
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SYSTEM_PROMPT_PATH: str = os.path.join(BASE_DIR, "data", "system_prompt.txt")
    PROVIDERS_PATH: str = os.path.join(BASE_DIR, "data", "providers.json")
    MODELS_PATH: str = os.path.join(BASE_DIR, "data", "models.json")


cfg = Config()


def read_system_prompt() -> str:
    try:
        if os.path.exists(cfg.SYSTEM_PROMPT_PATH):
            with open(cfg.SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return "Tu es EvilGPT, une IA sarcastique et provocatrice sur Discord."
