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

    chosen = _select_model(models)
    
    # LiteLLM needs the provider prefix for fallbacks too if they are custom
    fallbacks = [f"openai/{m.id}" if "/" in m.id else m.id for m in models if m.id != chosen.id]

    start_time = time.time()
    try:
        resp = litellm.completion(
            model=f"openai/{chosen.id}",
            base_url=chosen.api_base,
            api_key=chosen.api_key,
            messages=messages,
            fallbacks=fallbacks,
            timeout=30,
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
        return Answer("Une erreur s'est produite lors de la génération de la réponse.")
