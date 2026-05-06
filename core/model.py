import time
from typing import List, Optional
import litellm

# Disable LiteLLM logging worker to prevent "Task was destroyed but it is pending" noise
litellm.suppress_logging_worker_warnings = True
# Optional: suppress standard LiteLLM stdout logging if desired
# litellm.set_verbose = False 

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

async def generate_answer(messages: list, stream: bool = False):
    models = get_models()
    if not models:
        return Answer("Désolé, aucune configuration d'IA disponible.")

    # Sort models or pick one that isn't known to be down
    chosen = _select_model(models)
    
    # Prépare les fallbacks sans inclure le modèle principal
    # Important : LiteLLM a besoin que chaque fallback ait sa propre api_base/api_key
    # On va donc passer une liste de dictionnaires pour les fallbacks
    fallbacks_configs = []
    for m in models:
        if m.id == chosen.id:
            continue
        fallbacks_configs.append({
            "model": f"openai/{m.id}" if "/" not in m.id else m.id,
            "api_base": m.api_base,
            "api_key": m.api_key
        })

    start_time = time.time()
    try:
        # LiteLLM: custom providers with non-standard IDs might need explicit naming
        model_name = f"openai/{chosen.id}" if "/" not in chosen.id else chosen.id
        
        resp = await litellm.acompletion(
            model=model_name,
            base_url=chosen.api_base,
            api_key=chosen.api_key,
            messages=messages,
            fallbacks=fallbacks_configs, # Utilise la liste de configs complète
            timeout=10,
            max_tokens=2000,
            stream=stream
        )
        
        if stream:
            return resp

        content = ""
        if hasattr(resp, "choices") and resp.choices:
            content = resp.choices[0].message.content
        
        ans = Answer(content)
        ans.model = chosen.id
        ans.response_time = time.time() - start_time
        return ans
    except Exception as e:
        logger.error("Error generating answer: %s", e)
        return Answer("Toutes mes sources de haine sont saturées. Réessaie plus tard.")
