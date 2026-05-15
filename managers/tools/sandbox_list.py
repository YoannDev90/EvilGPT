"""_summary_."""
import asyncio
import json

import microsandbox

from utils.logger import get_logger

logger = get_logger()


async def sandbox_list() -> str:
    """_summary_.

    Returns
    -------
    str
        _description_
    """
    try:
        handles = await asyncio.to_thread(microsandbox.Sandbox.list)
        results = []
        for handle in handles:
            results.append(
                {
                    "name": getattr(handle, "name", None),
                    "status": getattr(handle, "status", None),
                    "createdAt": getattr(handle, "created_at", None)
                    or getattr(handle, "createdAt", None),
                }
            )
        return json.dumps(results, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_list failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
