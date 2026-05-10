import asyncio
from typing import Any, Dict

import microsandbox

from utils.logger import get_logger

logger = get_logger()


async def run_python(code: str, timeout: int = 10) -> str:
    """Execute Python code in sandboxed environment."""
    try:
        sandbox = microsandbox.Sandbox()
        result = await asyncio.wait_for(
            asyncio.to_thread(sandbox.run, code, "python"), timeout=timeout
        )
        return str(result)
    except asyncio.TimeoutError:
        logger.error(f"Python execution timeout after {timeout}s")
        return f"Error: Execution timeout after {timeout} seconds"
    except Exception as e:
        logger.error(f"Python execution error: {e}")
        return f"Error: {str(e)}"
