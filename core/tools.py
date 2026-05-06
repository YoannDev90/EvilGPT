import json
from utils.web_search import get_web_context
import microsandbox
from utils.logger import get_logger

logger = get_logger(__name__)

# Tools definition for LiteLLM / OpenAI format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search for information on the web via DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to perform."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute Python code in a secure sandbox environment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The Python code to execute."}
                },
                "required": ["code"]
            }
        }
    }
]

async def handle_tool_call(tool_name: str, args: dict) -> str:
    """Execute the requested tool and return the result as a string."""
    try:
        if tool_name == "web_search":
            query = args.get("query")
            logger.info(f"Tool Call: web_search -> {query}")
            return get_web_context(query)
        
        elif tool_name == "execute_python":
            code = args.get("code")
            logger.info(f"Tool Call: execute_python")
            
            # Using microsandbox (Standard API)
            # Use default python image
            sb = microsandbox.Sandbox(
                image=microsandbox.Image(name="python:3.12-slim")
            )
            
            # Install if missing (first time)
            if not microsandbox.is_installed():
                microsandbox.install()

            handle = sb.start()
            result = handle.exec(["python", "-c", code])
            
            output = []
            if result.stdout: output.append(f"STDOUT:\n{result.stdout.decode('utf-8', errors='replace')}")
            if result.stderr: output.append(f"STDERR:\n{result.stderr.decode('utf-8', errors='replace')}")
            if result.exit_status != 0: output.append(f"Exit Status: {result.exit_status}")
            
            handle.stop()
            return "\n".join(output) if output else "Code executed successfully (no output)."
            
    except Exception as e:
        logger.error(f"Error in tool {tool_name}: {e}")
        return f"Error during tool {tool_name} execution: {str(e)}"
    
    return "Unknown tool."
