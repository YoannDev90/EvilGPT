import asyncio
import json
import time
from typing import Any, Dict, Optional

import microsandbox

from utils.logger import get_logger

logger = get_logger()

# Default OCI image to use for ephemeral Python sandboxes when none provided
DEFAULT_PYTHON_IMAGE = "python:3.12-slim"


async def run_python(code: str, timeout: int = 10, image: Optional[str] = None) -> str:
    """Execute Python code in sandboxed environment.

    Uses an ephemeral sandbox created for this run to avoid requiring a direct
    `Sandbox()` constructor.
    """
    name = f"run-python-{int(time.time() * 1000)}"
    sandbox = None
    try:
        kwargs: Dict[str, Any] = {"memory_mib": 256, "cpus": 1}
        # Ensure an image or snapshot is provided for microsandbox
        kwargs["image"] = image or DEFAULT_PYTHON_IMAGE

        try:
            sandbox = await asyncio.to_thread(
                microsandbox.Sandbox.create, name, **kwargs
            )
        except Exception:
            cfg = {
                "name": name,
                "memoryMib": 256,
                "cpus": 1,
                "image": image or DEFAULT_PYTHON_IMAGE,
            }
            sandbox = await asyncio.to_thread(microsandbox.Sandbox.create, cfg)

        result = await asyncio.wait_for(
            asyncio.to_thread(sandbox.run, code, "python"), timeout=timeout
        )
        # Prefer JSON string if result is structured
        try:
            return json.dumps(result, ensure_ascii=True)
        except Exception:
            return str(result)
    except asyncio.TimeoutError:
        logger.error("Python execution timeout after %ss", timeout)
        return f"Error: Execution timeout after {timeout} seconds"
    except Exception as e:
        logger.error("Python execution error: %s", e, exc_info=True)
        return f"Error: {str(e)}"
    finally:
        if sandbox is not None:
            try:
                await asyncio.to_thread(sandbox.stop)
            except Exception:
                pass
            try:
                await asyncio.to_thread(microsandbox.Sandbox.remove, name)
            except Exception:
                pass
