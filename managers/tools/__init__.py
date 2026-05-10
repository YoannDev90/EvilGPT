import json
import os
from typing import Any, Dict, List

from utils.logger import get_logger

logger = get_logger()


class ToolsLoader:
    def __init__(self, tools_dir: str):
        self.tools_dir = tools_dir
        self.tools_metadata: List[Dict[str, Any]] = []
        self.tools_handlers: Dict[str, Any] = {}
        self._load_tools()

    def _load_tools(self):
        """Load all tool definitions from JSON files."""
        if not os.path.exists(self.tools_dir):
            logger.warning(f"Tools directory not found: {self.tools_dir}")
            return

        for filename in os.listdir(self.tools_dir):
            if not filename.endswith(".json"):
                continue

            tool_name = filename[:-5]  # Remove .json
            json_path = os.path.join(self.tools_dir, filename)

            try:
                with open(json_path, "r") as f:
                    metadata = json.load(f)
                self.tools_metadata.append(metadata)

                # Dynamically import handler
                try:
                    module = __import__(
                        f"managers.tools.{tool_name}", fromlist=[tool_name]
                    )
                    handler = getattr(module, tool_name)
                    self.tools_handlers[tool_name] = handler
                    logger.info(f"Loaded tool: {tool_name}")
                except ImportError as e:
                    logger.error(f"Failed to import handler for {tool_name}: {e}")

            except Exception as e:
                logger.error(f"Failed to load tool {tool_name}: {e}")

    async def call_tool(self, tool_name: str, args: dict) -> str:
        """Call a tool handler with the given arguments."""
        if tool_name not in self.tools_handlers:
            return f"Unknown tool: {tool_name}"

        try:
            handler = self.tools_handlers[tool_name]
            result = await handler(**args)
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return f"Error: {str(e)}"
