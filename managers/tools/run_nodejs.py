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
            # Create in the current event-loop/thread; some SDK builds require a running loop
            sandbox = microsandbox.Sandbox.create(name, **kwargs)
        except Exception:
            cfg = {
                "name": name,
                "memoryMib": 256,
                "cpus": 1,
                "image": image or DEFAULT_NODE_IMAGE,
            }
            sandbox = microsandbox.Sandbox.create(cfg)

        # Some SDK builds return a coroutine/Future from create(); await if so
        if asyncio.iscoroutine(sandbox) or isinstance(sandbox, asyncio.Future):
            sandbox = await sandbox

        def _extract_exec_result(result: Any) -> Dict[str, Any]:
            # Support multiple SDK result shapes (ExecOutput, simple namespaces)
            stdout = None
            stderr = None
            codev = None
            success = None

            # Common field names
            for attr in ("stdout_text", "stdout", "stdout_bytes"):
                if hasattr(result, attr):
                    stdout = getattr(result, attr)
                    break
            for attr in ("stderr_text", "stderr", "stderr_bytes"):
                if hasattr(result, attr):
                    stderr = getattr(result, attr)
                    break
            for attr in ("exit_code", "code"):
                if hasattr(result, attr):
                    codev = getattr(result, attr)
                    break
            if hasattr(result, "success"):
                success = getattr(result, "success")

            if callable(stdout):
                stdout = stdout()
            if callable(stderr):
                stderr = stderr()
            if callable(success):
                success = success()

            # If bytes provided, try to decode
            if isinstance(stdout, (bytes, bytearray)):
                try:
                    stdout = stdout.decode("utf-8", errors="replace")
                except Exception:
                    pass
            if isinstance(stderr, (bytes, bytearray)):
                try:
                    stderr = stderr.decode("utf-8", errors="replace")
                except Exception:
                    pass

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exitCode": codev,
                "success": success,
            }

        if hasattr(sandbox, "exec"):
            try:
                maybe = sandbox.exec("node", ["-e", code])

                # If exec returned a coroutine/awaitable, await it; otherwise run in thread
                if asyncio.iscoroutine(maybe) or isinstance(maybe, asyncio.Future):
                    raw = await asyncio.wait_for(maybe, timeout=timeout)
                else:
                    raw = await asyncio.wait_for(
                        asyncio.to_thread(sandbox.exec, "node", ["-e", code]),
                        timeout=timeout,
                    )

                # If raw is an ExecHandle (streaming), try to collect its output
                collect = getattr(raw, "collect", None)
                if collect is not None:
                    if asyncio.iscoroutinefunction(collect):
                        out = await asyncio.wait_for(raw.collect(), timeout=timeout)
                    else:
                        out = await asyncio.wait_for(
                            asyncio.to_thread(raw.collect), timeout=timeout
                        )
                    result = _extract_exec_result(out)
                else:
                    result = _extract_exec_result(raw)
            except Exception:
                raise
        else:
            raise RuntimeError("sandbox.exec not available")

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
