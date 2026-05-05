import time
import logging
from typing import List, Optional

import litellm
from ai_utils.get_models import get_models, Model
from config import API_BASE, API_KEY

logger = logging.getLogger(__name__)


class Answer:
    def __init__(self, content: str = ""):
        self.content = content
        self.model = None
        self.input_tokens = None
        self.output_tokens = None
        self.total_tokens = None
        self.response_time = None
        self.raw = None


def _select_model(models: List[Model], required_inputs: Optional[List[str]] = None, required_params: Optional[List[str]] = None) -> Optional[Model]:
    t0 = time.time()
    required_inputs = required_inputs or ["text"]
    required_params = required_params or ["messages"]
    
    logger.debug("[%.3f] Selecting model from %d candidates", t0, len(models))

    # prefer models that support required inputs and params
    for m in models:
        try:
            if m.supports_modalities(required_inputs, []) and m.supports_parameters(required_params):
                logger.debug("[%.3f] Selected %s (supports required modalities/params)", time.time(), m.id)
                return m
        except Exception as e:
            logger.warning("[%.3f] Error checking %s: %s", time.time(), m.id, e)
            continue

    # fallback: any model
    chosen = models[0] if models else None
    logger.warning("[%.3f] No exact match, using fallback: %s", time.time(), chosen.id if chosen else "None")
    return chosen


def generate_answer(messages: list, required_inputs: Optional[List[str]] = None, required_params: Optional[List[str]] = None, retries: int = 3, backoff: float = 1.0) -> Answer:
    t0 = time.time()
    logger.info("[%.3f] generate_answer() called", t0)
    
    models = get_models()
    logger.info("[%.3f] Loaded %d models", time.time(), len(models))
    if not models:
        raise RuntimeError("No models available")

    chosen = _select_model(models, required_inputs, required_params)
    if not chosen:
        chosen = models[0]
    logger.info("[%.3f] Selected model: %s", time.time(), chosen.id)

    fallbacks = [f"openai/{m.id}" for m in models if m.id != chosen.id]
    logger.debug("[%.3f] Fallbacks (%d): %s", time.time(), len(fallbacks), fallbacks[:2])

    attempt = 0
    last_exc = None
    while attempt < retries:
        attempt += 1
        start = time.time()
        logger.info("[%.3f] Attempt %d/%d with model %s", start, attempt, retries, chosen.id)
        try:
            logger.debug("[%.3f] Calling litellm.completion()...", time.time())
            resp = litellm.completion(
                model=f"openai/{chosen.id}",
                base_url = API_BASE,
                api_key = API_KEY,
                messages=messages,
                fallbacks=fallbacks,
                timeout=30,
            )
            resp_ts = time.time()
            logger.info("[%.3f] LiteLLM response received after %.2fs", resp_ts, resp_ts - start)

            ans = Answer()
            ans.raw = resp
            ans.response_time = time.time() - start
            ans.model = chosen.id
            logger.debug("[%.3f] Response time: %.2fs", time.time(), ans.response_time)

            # try extract content
            try:
                # handle different response shapes
                if hasattr(resp, "choices") and resp.choices:
                    c = resp.choices[0]
                    content = getattr(getattr(c, "message", None), "content", None) or getattr(c, "text", None)
                    logger.debug("[%.3f] Extracted content from choices[0]", time.time())
                else:
                    content = getattr(resp, "text", None) or ""
                    logger.debug("[%.3f] Extracted content from text attr", time.time())
            except Exception as e:
                logger.warning("[%.3f] Failed to extract content: %s", time.time(), e)
                content = ""

            ans.content = content or ""
            logger.info("[%.3f] Content extracted: %d chars", time.time(), len(ans.content))

            # try extract token usage if present
            try:
                usage = getattr(resp, "usage", None) or resp.get("usage") if isinstance(resp, dict) else None
                if usage:
                    ans.input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
                    ans.output_tokens = usage.get("completion_tokens") or usage.get("output_tokens")
                    ans.total_tokens = usage.get("total_tokens")
                    logger.info("[%.3f] Tokens - Input: %s, Output: %s", time.time(), ans.input_tokens, ans.output_tokens)
            except Exception as e:
                logger.debug("[%.3f] Failed to extract tokens: %s", time.time(), e)

            logger.info("[%.3f] generate_answer() complete (%.2fs total)", time.time(), time.time() - t0)
            return ans

        except Exception as e:
            last_exc = e
            logger.error("[%.3f] Attempt %d failed: %s", time.time(), attempt, e, exc_info=False)
            if attempt < retries:
                sleep_time = backoff * attempt
                logger.warning("[%.3f] Retrying in %.2fs...", time.time(), sleep_time)
                time.sleep(sleep_time)

    # all retries failed
    logger.error("[%.3f] All %d attempts failed for %s", time.time(), retries, chosen.id)
    raise RuntimeError(f"All attempts failed: {last_exc}")