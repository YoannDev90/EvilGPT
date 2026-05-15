"""_summary_."""

import asyncio
import json
import shlex
from typing import Any, Dict

import microsandbox

from utils.logger import get_logger

logger = get_logger()


def _extract_exec_result(result: Any) -> Dict[str, Any]:
    """_summary_.

    Parameters
    ----------
    result : Any
        _description_

    Returns
    -------
    Dict[str, Any]
        _description_
    """
    stdout = getattr(result, "stdout", None)
    stderr = getattr(result, "stderr", None)
    code = getattr(result, "code", None)
    success = getattr(result, "success", None)

    if callable(stdout):
        stdout = stdout()
    if callable(stderr):
        stderr = stderr()
    if callable(success):
        success = success()

    return {
        "stdout": stdout,
        "stderr": stderr,
        "exitCode": code,
        "success": success,
    }


async def sandbox_fs_remove(name: str, path: str) -> str:
    """_summary_.

    Parameters
    ----------
    name : str
        _description_
    path : str
        _description_

    Returns
    -------
    str
        _description_
    """
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        cmd = f"rm -rf {shlex.quote(path)}"
        result = await asyncio.to_thread(sandbox.shell, cmd)
        out = _extract_exec_result(result)
        if not out.get("success"):
            return json.dumps(out, ensure_ascii=True, indent=2)
        return json.dumps({"path": path, "removed": True}, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_fs_remove failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
