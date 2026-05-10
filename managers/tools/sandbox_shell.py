import asyncio
import json
from typing import Any, Dict, Optional

import microsandbox

from utils.logger import get_logger

logger = get_logger()


def _extract_exec_result(result: Any) -> Dict[str, Any]:
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


async def sandbox_shell(
    name: str, command: str, timeout: Optional[float] = None
) -> str:
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        if timeout is not None:
            result = await asyncio.to_thread(
                sandbox.exec,
                "sh",
                {"args": ["-c", command], "timeout": int(timeout * 1000)},
            )
        else:
            result = await asyncio.to_thread(sandbox.shell, command)
        return json.dumps(_extract_exec_result(result), ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_shell failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
