import asyncio
import json
import time
from typing import Any, Dict, Optional

import microsandbox

from utils.logger import get_logger

logger = get_logger()

# Default shell image
DEFAULT_SHELL_IMAGE = "ubuntu:22.04"


async def run_bash(code: str, timeout: int = 10, image: Optional[str] = None) -> str:
    """Execute bash commands in sandboxed environment using ephemeral sandbox."""
    name = f"run-bash-{int(time.time() * 1000)}"
    sandbox = None
    try:
        kwargs: Dict[str, Any] = {
            "memory_mib": 256,
            "cpus": 1,
            "image": image or DEFAULT_SHELL_IMAGE,
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
                "image": image or DEFAULT_SHELL_IMAGE,
            }
            sandbox = await asyncio.to_thread(microsandbox.Sandbox.create, cfg)

        result = await asyncio.wait_for(
            asyncio.to_thread(sandbox.run, code, "bash"), timeout=timeout
        )
        try:
            return json.dumps(result, ensure_ascii=True)
        except Exception:
            return str(result)
    except asyncio.TimeoutError:
        logger.error("Bash execution timeout after %ss", timeout)
        return f"Error: Execution timeout after {timeout} seconds"
    except Exception as e:
        logger.error("Bash execution error: %s", e, exc_info=True)
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
