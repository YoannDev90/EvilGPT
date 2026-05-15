"""_summary_."""

import asyncio
import json

import microsandbox

from utils.logger import get_logger

logger = get_logger()


async def sandbox_stop(name: str, force: bool = False) -> str:
    """_summary_.

    Parameters
    ----------
    name : str
        _description_
    force : bool
        _description_ (Default value = False)

    Returns
    -------
    str
        _description_
    """
    try:
        handle = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        if force:
            await asyncio.to_thread(handle.kill)
        else:
            await asyncio.to_thread(handle.stop)
        return json.dumps(
            {"name": name, "status": "stopped"}, ensure_ascii=True, indent=2
        )
    except Exception as exc:
        logger.error("sandbox_stop failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
