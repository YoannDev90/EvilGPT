"""_summary_."""

import asyncio
import json

import microsandbox

from utils.logger import get_logger

logger = get_logger()


async def sandbox_inspect(name: str) -> str:
    """_summary_.

    Parameters
    ----------
    name : str
        _description_

    Returns
    -------
    str
        _description_
    """
    try:
        handle = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        data = {
            "name": getattr(handle, "name", name),
            "status": getattr(handle, "status", None),
            "config": getattr(handle, "config_json", None)
            or getattr(handle, "configJson", None),
            "createdAt": getattr(handle, "created_at", None)
            or getattr(handle, "createdAt", None),
            "updatedAt": getattr(handle, "updated_at", None)
            or getattr(handle, "updatedAt", None),
        }
        return json.dumps(data, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_inspect failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
