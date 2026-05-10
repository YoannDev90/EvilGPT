import asyncio
import json
from typing import Any, Dict, List, Optional

import microsandbox

from utils.logger import get_logger

logger = get_logger()


async def sandbox_create(
    name: str,
    image: str,
    cpus: int = 1,
    memoryMib: int = 512,
    workdir: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    volumes: Optional[List[Dict[str, Any]]] = None,
    patches: Optional[List[Dict[str, Any]]] = None,
    entrypoint: Optional[List[str]] = None,
    hostname: Optional[str] = None,
    maxDuration: Optional[int] = None,
    idleTimeout: Optional[int] = None,
) -> str:
    try:
        kwargs: Dict[str, Any] = {
            "image": image,
            "cpus": cpus,
            "memory_mib": memoryMib,
        }
        if workdir:
            kwargs["workdir"] = workdir
        if env:
            kwargs["env"] = env
        if entrypoint:
            kwargs["entrypoint"] = entrypoint
        if hostname:
            kwargs["hostname"] = hostname
        if maxDuration is not None:
            kwargs["max_duration"] = maxDuration
        if idleTimeout is not None:
            kwargs["idle_timeout"] = idleTimeout
        if volumes:
            kwargs["volumes"] = volumes
        if patches:
            kwargs["patches"] = patches

        try:
            await asyncio.to_thread(microsandbox.Sandbox.create, name, **kwargs)
        except Exception:
            cfg = {
                "name": name,
                "image": image,
                "cpus": cpus,
                "memoryMib": memoryMib,
                "workdir": workdir,
                "env": env,
                "volumes": volumes,
                "patches": patches,
                "entrypoint": entrypoint,
                "hostname": hostname,
                "maxDuration": maxDuration,
                "idleTimeout": idleTimeout,
            }
            cfg = {k: v for k, v in cfg.items() if v is not None}
            await asyncio.to_thread(microsandbox.Sandbox.create, cfg)

        return json.dumps(
            {"name": name, "status": "running", "image": image},
            ensure_ascii=True,
            indent=2,
        )
    except Exception as exc:
        logger.error("sandbox_create failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
