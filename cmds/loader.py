import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any

from discord import app_commands


def _iter_command_modules(base_path: Path):
    pkg_path = str(base_path)
    for finder, name, ispkg in pkgutil.iter_modules([pkg_path]):
        if name.startswith("__"):
            continue
        yield name


async def load_commands(bot: Any, tree: app_commands.CommandTree, cmds_path: Path):
    """Recursively import modules from `cmds_path` and call `setup(tree, bot)` if present."""
    # Top-level modules
    for finder, modname, ispkg in pkgutil.walk_packages([str(cmds_path)], prefix=""):
        if modname.split(".")[-1].startswith("__"):
            continue
        rel = modname.replace("/", ".")
        # Convert filesystem path style to module-like import path
        # We'll import via importlib by path: convert file path to module spec
        try:
            spec = importlib.util.spec_from_file_location(
                modname, str(cmds_path / (modname + ".py"))
            )
            if spec is None:
                # maybe a package
                # try import by package name relative to project
                module = importlib.import_module(f"cmds.{modname}")
            else:
                module = importlib.util.module_from_spec(spec)
                loader = spec.loader
                assert loader is not None
                loader.exec_module(module)
        except Exception:
            # fallback: try import as package module
            try:
                module = importlib.import_module(f"cmds.{modname}")
            except Exception:
                continue

        # If module defines setup function, call it
        setup_fn = getattr(module, "setup", None)
        if callable(setup_fn):
            try:
                maybe_coro = setup_fn(tree, bot)
                if inspect.isawaitable(maybe_coro):
                    await maybe_coro
            except Exception:
                # ignore failing command modules to avoid crashing startup
                continue
