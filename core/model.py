import logging
import time
from typing import List, Optional

import litellm

# Disable LiteLLM logging worker to prevent "Task was destroyed but it is pending" noise
litellm.suppress_logging_worker_warnings = True
# Optional: suppress standard LiteLLM stdout logging if desired
# litellm.set_verbose = False
try:
    # Prefer explicit debug off API if available
    if hasattr(litellm, "_turn_off_debug"):
        litellm._turn_off_debug()
    else:
        # Fallback: set verbose flag if present
        setattr(litellm, "set_verbose", False)
except Exception:
    pass

# Reduce Python logging noise from litellm internals
for _n in ("LiteLLM", "litellm"):
    logging.getLogger(_n).setLevel(logging.WARNING)

from core.config import cfg
from core.models_loader import Model, get_models
from core.tools import get_combined_tools, handle_tool_call
from utils.logger import get_logger

logger = get_logger()


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
    logger.debug(f"Selected model: {chosen.id} (base: {chosen.api_base})")

    # Prépare les fallbacks sans inclure le modèle principal
    fallbacks_configs = []
    for m in models:
        if m.id == chosen.id:
            continue
        model_name = f"openai/{m.id}"
        fallbacks_configs.append(
            {"model": model_name, "base_url": m.api_base, "api_key": m.api_key}
        )

    start_time = time.time()
    try:
        # Forcer le préfixe 'openai/' pour chaque endpoint OpenAI-compatible.
        model_name = f"openai/{chosen.id}"

        # Premier appel pour voir si l'IA veut appeler un outil
        resp = await litellm.acompletion(
            model=model_name,
            base_url=chosen.api_base,
            api_key=chosen.api_key,
            messages=messages,
            tools=get_combined_tools(),
            tool_choice="auto",
            fallbacks=fallbacks_configs,
            timeout=25,
        )

        message = resp.choices[0].message

        # Si tool_calls est présent, on les exécute
        if hasattr(message, "tool_calls") and message.tool_calls:
            logger.info(
                f"LLM wants to use {len(message.tool_calls)} tools: {[tc.function.name for tc in message.tool_calls]}"
            )
            assistant_message = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": getattr(tool_call, "type", "function"),
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ]

            messages.append(assistant_message)

            for tool_call in message.tool_calls:
                import json

                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                result = await handle_tool_call(function_name, arguments)

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": result,
                    }
                )

            # Deuxième appel après avoir ajouté les résultats des outils
            # Pour la réponse finale au tool calling, on peut streamer si demandé
            resp = await litellm.acompletion(
                model=model_name,
                base_url=chosen.api_base,
                api_key=chosen.api_key,
                messages=messages,
                fallbacks=fallbacks_configs,
                timeout=25,
                stream=stream,
            )

            if stream:
                return resp
        else:
            # Si on voulait du stream dès le début et qu'aucun outil n'est appelé,
            # il faut relancer avec stream=True (LiteLLM ne permet pas de streamer le tool calling facilement en un coup)
            if stream:
                return await litellm.acompletion(
                    model=model_name,
                    base_url=chosen.api_base,
                    api_key=chosen.api_key,
                    messages=messages,
                    fallbacks=fallbacks_configs,
                    timeout=25,
                    stream=True,
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
        return Answer(
            "Toutes mes sources de haine sont saturées (ou une erreur d'outil est survenue)."
        )
