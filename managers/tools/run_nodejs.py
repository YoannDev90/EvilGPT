import asyncio
import json
import time
from typing import Any, Dict, Optional

import microsandbox

from utils.logger import get_logger

logger = get_logger()

# Default Node.js image
DEFAULT_NODE_IMAGE = "node:22-slim"


async def run_nodejs(code: str, timeout: int = 10, image: Optional[str] = None) -> str:
    """Execute Node.js code in sandboxed environment using ephemeral sandbox.

    Mirrors the approach used by `run_python` to avoid direct Sandbox constructor calls.
    """
    name = f"run-nodejs-{int(time.time() * 1000)}"
    sandbox = None
    try:
        kwargs: Dict[str, Any] = {
            "memory_mib": 256,
            "cpus": 1,
            "image": image or DEFAULT_NODE_IMAGE,
        }

        try:
            sandbox = await asyncio.to_thread(
                microsandbox.Sandbox.create, name, **kwargs
            )
        except Exception:
            cfg = {
                "name": name,
                "memoryMib": 256,
                "cpus": 1,
                "image": image or DEFAULT_NODE_IMAGE,
            }
            sandbox = await asyncio.to_thread(microsandbox.Sandbox.create, cfg)

        result = await asyncio.wait_for(
            asyncio.to_thread(sandbox.run, code, "nodejs"), timeout=timeout
        )
        try:
            return json.dumps(result, ensure_ascii=True)
        except Exception:
            return str(result)
    except asyncio.TimeoutError:
        logger.error("Node.js execution timeout after %ss", timeout)
        return f"Error: Execution timeout after {timeout} seconds"
    except Exception as e:
        logger.error("Node.js execution error: %s", e, exc_info=True)
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
