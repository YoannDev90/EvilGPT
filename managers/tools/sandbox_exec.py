"""_summary_."""

import asyncio
import json
from typing import Any, Dict, List, Optional

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


async def sandbox_exec(
    name: str,
    command: str,
    args: Optional[List[str]] = None,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
) -> str:
    """_summary_.

    Parameters
    ----------
    name : str
        _description_
    command : str
        _description_
    args : Optional[List[str]]
        _description_ (Default value = None)
    cwd : Optional[str]
        _description_ (Default value = None)
    env : Optional[Dict[str, str]]
        _description_ (Default value = None)
    timeout : Optional[float]
        _description_ (Default value = None)

    Returns
    -------
    str
        _description_
    """
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)

        options: Dict[str, Any] = {}
        if args:
            options["args"] = args
        if cwd:
            options["cwd"] = cwd
        if env:
            options["env"] = env
        if timeout is not None:
            options["timeout"] = int(timeout * 1000)

        if options:
            result = await asyncio.to_thread(sandbox.exec, command, options)
        elif args:
            result = await asyncio.to_thread(sandbox.exec, command, args)
        else:
            result = await asyncio.to_thread(sandbox.exec, command)

        return json.dumps(_extract_exec_result(result), ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_exec failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
