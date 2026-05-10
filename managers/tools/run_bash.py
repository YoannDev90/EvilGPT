import asyncio
from typing import Any, Dict

import microsandbox

from utils.logger import get_logger

logger = get_logger()


async def run_bash(code: str, timeout: int = 10) -> str:
    """Execute bash commands in sandboxed environment."""
    try:
        sandbox = microsandbox.Sandbox()
        result = await asyncio.wait_for(
            asyncio.to_thread(sandbox.run, code, "bash"), timeout=timeout
        )
        return str(result)
    except asyncio.TimeoutError:
        logger.error(f"Bash execution timeout after {timeout}s")
        return f"Error: Execution timeout after {timeout} seconds"
    except Exception as e:
        logger.error(f"Bash execution error: {e}")
        return f"Error: {str(e)}"
