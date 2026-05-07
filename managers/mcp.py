import asyncio
import json
import os
from typing import Any, Dict, List

from fastmcp import FastMCP

from core.config import cfg
from utils.logger import get_logger

logger = get_logger()


class MCPManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.clients: Dict[str, FastMCP] = {}
        self.tools_metadata: List[Dict[str, Any]] = []

    def load_config(self):
        if not os.path.exists(self.config_path):
            logger.warning(f"MCP config not found at {self.config_path}")
            return {}
        with open(self.config_path, "r") as f:
            return json.load(f)

    async def initialize(self):
        config = self.load_config()
        servers = config.get("mcpServers", {})

        for name, srv_config in servers.items():
            try:
                logger.info(f"Initializing MCP server: {name}")
                # FastMCP acts as a client when connecting to a server command
                client = FastMCP(
                    name, command=srv_config["command"], args=srv_config.get("args", [])
                )
                self.clients[name] = client

                # Fetch tools from the server
                # In fastmcp, we can iterate over the tools exposed
                for tool in client.tools:
                    # Map to OpenAI/LiteLLM function format
                    self.tools_metadata.append(
                        {
                            "type": "function",
                            "function": {
                                "name": f"mcp_{name}_{tool.name}",
                                "description": tool.description,
                                "parameters": tool.parameters,  # fastmcp tool parameters are already JSON schemas
                            },
                        }
                    )
                logger.info(f"Loaded {len(client.tools)} tools from {name}")
            except Exception as e:
                logger.error(f"Failed to initialize MCP server {name}: {e}")

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        client = self.clients.get(server_name)
        if not client:
            return f"Error: MCP server {server_name} not found."

        try:
            # call_tool in fastmcp
            result = await client.call_tool(tool_name, arguments)
            return str(result)
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name} on {server_name}: {e}")
            return f"Error: {str(e)}"


# Singleton instance
MCP_CONFIG_PATH = os.path.join(cfg.BASE_DIR, "data", "mcp.json")
mcp_manager = MCPManager(MCP_CONFIG_PATH)
