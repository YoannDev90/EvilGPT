import json

import microsandbox

from managers.mcp import mcp_manager
from utils.logger import get_logger
from utils.web_search import get_web_context

logger = get_logger()

# Tools definition for LiteLLM / OpenAI format
BASE_TOOLS = []


def get_combined_tools():
    """Returns the list of base tools plus dynamically loaded MCP tools."""
    return BASE_TOOLS + mcp_manager.tools_metadata


async def handle_tool_call(tool_name: str, args: dict) -> str:
    """Execute the requested tool and return the result as a string."""
    try:
        # Check if it's an MCP tool (format: mcp_SERVERNAME_TOOLNAME)
        if tool_name.startswith("mcp_"):
            parts = tool_name.split("_", 2)
            if len(parts) >= 3:
                server_name = parts[1]
                actual_tool_name = parts[2]
                return await mcp_manager.call_tool(server_name, actual_tool_name, args)

        return "Unknown tool."

    except Exception as e:
        logger.error(f"Error in tool {tool_name}: {e}")
        return f"Error during tool {tool_name} execution: {str(e)}"
