import json
import os
import time
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env variables
load_dotenv()


class Provider:
    """API Provider configuration"""
    def __init__(self, provider: str, env_key: str, api_base: str):
        self.provider = provider
        self.env_key = env_key
        self.api_base = api_base
        self.api_key = os.getenv(env_key)
        logger.debug("[%.3f] Provider %s initialized (has_key: %s)", time.time(), provider, bool(self.api_key))


class Model:
    """Mistral model with provider context"""
    def __init__(self, id: str, provider: Provider):
        self.id = id
        self.litellm_id = f"openai/{id}"
        self.provider = provider
        self.api_base = provider.api_base
        self.api_key = provider.api_key


def _load_providers() -> Dict[str, Provider]:
    """Load provider configurations from providers.json"""
    t0 = time.time()
    logger.debug("[%.3f] Loading providers.json", t0)
    
    with open("providers.json", "r", encoding="utf-8") as f:
        providers_list = json.load(f)
    
    providers = {}
    for p in providers_list:
        provider_name = p.get("provider", "").lower()
        if not provider_name:
            logger.warning("[%.3f] Provider entry missing 'provider' field", time.time())
            continue
        
        prov = Provider(
            provider=p.get("provider"),
            env_key=p.get("env_key"),
            api_base=p.get("api_base")
        )
        providers[provider_name] = prov
    
    logger.info("[%.3f] Loaded %d providers in %.3fs", time.time(), len(providers), time.time() - t0)
    return providers


def get_models() -> List[Model]:
    """Load models from models.json and assign providers"""
    t0 = time.time()
    logger.debug("[%.3f] get_models() called", t0)
    
    # Load providers first
    providers = _load_providers()
    logger.debug("[%.3f] Providers ready", time.time())
    
    # Load models
    logger.debug("[%.3f] Loading models.json", time.time())
    with open("models.json", "r", encoding="utf-8") as f:
        models_data = json.load(f)
    
    logger.debug("[%.3f] JSON loaded: %d model entries", time.time(), len(models_data))
    
    models = []
    for model_str in models_data:
        # Extract provider from "provider/model:variant"
        parts = model_str.split("/")
        if len(parts) < 2:
            logger.warning("[%.3f] Invalid model format: %s (no provider/model split)", time.time(), model_str)
            continue
        
        provider_name = parts[0].lower()
        if provider_name not in providers:
            logger.warning("[%.3f] Provider '%s' not found for model %s", time.time(), provider_name, model_str)
            continue
        
        provider = providers[provider_name]
        if not provider.api_key:
            logger.warning("[%.3f] Provider %s missing API key (env var: %s)", time.time(), provider_name, provider.env_key)
        
        model = Model(id=model_str, provider=provider)
        models.append(model)
        logger.debug("[%.3f] Loaded model: %s (provider: %s, base: %s)", time.time(), model_str, provider_name, provider.api_base)
    
    logger.info("[%.3f] get_models() complete: %d models from %d providers in %.3fs", time.time(), len(models), len(providers), time.time() - t0)
    return models


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    models = get_models()
    for m in models:
        print(f"{m.id:50} → {m.provider.provider:12} @ {m.api_base}")

