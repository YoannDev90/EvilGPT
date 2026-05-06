import time
from typing import List, Optional
import litellm
from core.models_loader import get_models, Model
from core.config import cfg
from utils.logger import get_logger

logger = get_logger(__name__)

class Answer:
    def __init__(self, content: str = ""):
        self.content = content
        self.model = None
        self.response_time = None

def _select_model(models: List[Model]) -> Optional[Model]:
    if not models:
        return None
    # Favor generic selection for now, or use first available
    return models[0]

def generate_answer(messages: list, retries: int = 2) -> Answer:
    models = get_models()
    if not models:
        return Answer("Désolé, aucune configuration d'IA disponible.")

    # Sort models or pick one that isn't known to be down
    chosen = _select_model(models)
    
    # LiteLLM needs the provider prefix precisely. 
    # For custom providers like 'paxsenix', 'mnn' etc., we use 'openai/' prefix 
    # because they follow OpenAI API format.
    fallbacks = [f"openai/{m.id}" if "/" not in m.id else m.id for m in models if m.id != chosen.id]

    # Remove duplicates and ensure format consistency
    fallbacks = list(dict.fromkeys(fallbacks))

    start_time = time.time()
    try:
        # LiteLLM: custom providers with non-standard IDs might need explicit naming
        model_name = f"openai/{chosen.id}" if "/" not in chosen.id else chosen.id
        
        resp = litellm.completion(
            model=model_name,
            base_url=chosen.api_base,
            api_key=chosen.api_key,
            messages=messages,
            fallbacks=fallbacks,
            timeout=15, # Reduced timeout for faster fallbacks
        )
        
        content = ""
        if hasattr(resp, "choices") and resp.choices:
            content = resp.choices[0].message.content
        
        ans = Answer(content)
        ans.model = chosen.id
        ans.response_time = time.time() - start_time
        return ans
    except Exception as e:
        logger.error("Error generating answer: %s", e)
        # Fallback to a very basic response if even LiteLLM fallbacks fail
        return Answer("Toutes mes sources de haine sont saturées. Réessaie plus tard.")
