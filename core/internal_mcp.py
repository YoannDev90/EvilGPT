import os
import sys

# Ensure the project root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import microsandbox
from fastmcp import FastMCP

from utils.logger import get_logger
from utils.web_search import get_web_context

logger = get_logger()

# Create a FastMCP server named "internal"
mcp = FastMCP("internal")

# --- Native Tools ---


@mcp.tool()
def web_search(query: str) -> str:
    """Search for information on the web via DuckDuckGo."""
    logger.info(f"MCP Tool: web_search -> {query}")
    return get_web_context(query)


# --- Sandboxed Tools ---


@mcp.tool()
async def execute_in_sandbox(command: str, image: str = "node:20-slim") -> str:
    """Execute a shell command inside a secure microsandbox VM.
    Use this to run Node.js/NPM tools (like npx) without installing them on the host.
    Default image has Node/NPM installed.
    """
    logger.info(f"MCP Tool: execute_in_sandbox -> {command}")

    sb = microsandbox.Sandbox(image=image, timeout=60)
    if not microsandbox.is_installed():
        microsandbox.install()

    handle = sb.start()
    # We use sh -c to allow complex commands and piping inside the VM
    result = handle.exec(["sh", "-c", command])

    output = []
    if result.stdout:
        output.append(result.stdout.decode("utf-8", errors="replace"))
    if result.stderr:
        output.append(result.stderr.decode("utf-8", errors="replace"))

    handle.stop()
    return "\n".join(output) if output else "Command executed successfully."


# --- Existing Tools ---


@mcp.tool()
def execute_python(code: str) -> str:
    """Execute Python code in a secure sandbox environment."""
    logger.info(f"MCP Tool: execute_python")

    # Using microsandbox
    sb = microsandbox.Sandbox(image="python:3.10-slim", timeout=10)

    if not microsandbox.is_installed():
        microsandbox.install()

    handle = sb.start()
    result = handle.exec(["python", "-c", code])

    output = []
    if result.stdout:
        output.append(f"STDOUT:\n{result.stdout.decode('utf-8', errors='replace')}")
    if result.stderr:
        output.append(f"STDERR:\n{result.stderr.decode('utf-8', errors='replace')}")
    if result.exit_status != 0:
        output.append(f"Exit Status: {result.exit_status}")

    handle.stop()
    return "\n".join(output) if output else "Code executed successfully (no output)."


if __name__ == "__main__":
    mcp.run()
