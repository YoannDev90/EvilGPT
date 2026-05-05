from dataclasses import dataclass
import os
from dotenv import load_dotenv
from typing import Optional


load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")
    GRATISFY_API_BASE: str = os.getenv("GRATISFY_API_BASE", "https://api.gratisfy.xyz/v1")
    GRATISFY_API_KEY: Optional[str] = os.getenv("GRATISFY_API_KEY")


cfg = Config()

# convenience alias used by existing code
BOT_TOKEN = cfg.BOT_TOKEN
import dotenv
import os

dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

API_BASE = "https://api.gratisfy.xyz/v1"
API_KEY = os.getenv("GRATISFY_API_KEY")