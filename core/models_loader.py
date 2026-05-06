import json
import os
import time
from typing import Dict, List, Optional

from core.config import cfg
from utils.logger import get_logger

logger = get_logger(__name__)


class Provider:
    def __init__(self, provider: str, env_key: str, api_base: str):
        self.provider = provider
        self.env_key = env_key
        self.api_base = api_base
        self.api_key = os.getenv(env_key)
        logger.debug(
            "Provider %s initialized (api_key: %s)",
            provider,
            "Set" if self.api_key else "Missing",
        )


class Model:
    def __init__(self, model_id: str, provider: Provider):
        self.id = model_id
        self.litellm_id = f"openai/{model_id}"
        self.provider = provider
        self.api_base = provider.api_base
        self.api_key = provider.api_key


def get_model_catalog() -> List[Dict[str, str]]:
    providers = _load_providers()
    if not os.path.exists(cfg.MODELS_PATH):
        logger.error("Models file not found: %s", cfg.MODELS_PATH)
        return []

    with open(cfg.MODELS_PATH, "r", encoding="utf-8") as f:
        models_data = json.load(f)

    catalog = []
    for m_id in models_data:
        parts = m_id.split("/", 1)
        if len(parts) != 2:
            continue

        prov_name = parts[0].lower()
        model_name = parts[1]
        provider = providers.get(prov_name)

        catalog.append(
            {
                "provider": prov_name,
                "model": model_name,
                "litellm_id": f"openai/{model_name}",
                "api_base": provider.api_base if provider else "",
                "api_key_set": bool(provider and provider.api_key),
            }
        )

    return catalog


def _load_providers() -> Dict[str, Provider]:
    if not os.path.exists(cfg.PROVIDERS_PATH):
        logger.error("Providers file not found: %s", cfg.PROVIDERS_PATH)
        return {}

    with open(cfg.PROVIDERS_PATH, "r", encoding="utf-8") as f:
        providers_list = json.load(f)

    providers = {}
    for p in providers_list:
        name = p.get("provider", "").lower()
        if name:
            providers[name] = Provider(
                p.get("provider"), p.get("env_key"), p.get("api_base")
            )
    return providers


def get_models() -> List[Model]:
    providers = _load_providers()
    if not os.path.exists(cfg.MODELS_PATH):
        logger.error("Models file not found: %s", cfg.MODELS_PATH)
        return []

    with open(cfg.MODELS_PATH, "r", encoding="utf-8") as f:
        models_data = json.load(f)

    models = []
    for m_id in models_data:
        parts = m_id.split("/", 1)
        if len(parts) == 2:
            prov_name = parts[0].lower()
            model_name = parts[1]
            if prov_name in providers and providers[prov_name].api_key:
                models.append(Model(model_name, providers[prov_name]))

    logger.info("Loaded %d models with valid API keys", len(models))
    return models
