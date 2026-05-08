import asyncio
import json
import os
from typing import Any, Dict, List

from fastmcp.client import Client

from core.config import cfg
from utils.logger import get_logger

logger = get_logger()


class MCPManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.clients: Dict[str, Client] = {}
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

        tasks = []
        for name, srv_config in servers.items():
            tasks.append(self._initialize_server(name, srv_config))

        if tasks:
            await asyncio.gather(*tasks)

    async def _initialize_server(self, name: str, srv_config: Dict[str, Any]):
        try:
            logger.info(f"Initializing MCP server: {name}")

            # Check for SSE URL (for search.parallel.ai/mcp)
            if "url" in srv_config:
                client_config = {
                    "mcpServers": {
                        name: {
                            "url": srv_config["url"],
                            "headers": srv_config.get("headers", {}),
                        }
                    }
                }
            else:
                # Stdio config
                client_config = {
                    "mcpServers": {
                        name: {
                            "command": srv_config["command"],
                            "args": srv_config.get("args", []),
                            "env": srv_config.get("env", os.environ.copy()),
                        }
                    }
                }

            client = Client(client_config)
            self.clients[name] = client

            # Connection must be established via context manager to allow list_tools()
            async with client:
                tools = await client.list_tools()
                for tool in tools:
                    # Map to OpenAI/LiteLLM function format
                    # In fastmcp Client, tool parameters are in inputSchema or input_schema
                    params = getattr(
                        tool, "inputSchema", getattr(tool, "parameters", {})
                    )
                    if hasattr(params, "model_dump"):
                        params = params.model_dump()

                    self.tools_metadata.append(
                        {
                            "type": "function",
                            "function": {
                                "name": f"mcp_{name}_{tool.name}",
                                "description": tool.description,
                                "parameters": params,
                            },
                        }
                    )
                logger.info(f"Loaded {len(tools)} tools from {name}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP server {name}: {e}")

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        client = self.clients.get(server_name)
        if not client:
            return f"Error: MCP server {server_name} not found."

        try:
            # call_tool in fastmcp requires an active connection
            async with client:
                result = await client.call_tool(tool_name, arguments)
                return str(result)
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name} on {server_name}: {e}")
            return f"Error: {str(e)}"


# Singleton instance
MCP_CONFIG_PATH = os.path.join(cfg.BASE_DIR, "data", "mcp.json")
mcp_manager = MCPManager(MCP_CONFIG_PATH)
