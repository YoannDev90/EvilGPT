import json
from utils.web_search import get_web_context
from microsandbox.python import PythonSandbox
from utils.logger import get_logger

logger = get_logger(__name__)

# Définition des outils pour LiteLLM / OpenAI format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Recherche des informations sur le web via DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "La recherche à effectuer."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Exécute du code Python dans un environnement sécurisé (sandbox).",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Le code Python à exécuter."}
                },
                "required": ["code"]
            }
        }
    }
]

async def handle_tool_call(tool_name: str, args: dict) -> str:
    """Exécute l'outil demandé et retourne le résultat sous forme de string."""
    try:
        if tool_name == "web_search":
            query = args.get("query")
            logger.info(f"Tool Call: web_search -> {query}")
            return get_web_context(query)
        
        elif tool_name == "execute_python":
            code = args.get("code")
            logger.info(f"Tool Call: execute_python")
            # Utilisation de microsandbox
            sb = PythonSandbox()
            result = sb.run(code)
            
            output = []
            if result.stdout: output.append(f"STDOUT:\n{result.stdout}")
            if result.stderr: output.append(f"STDERR:\n{result.stderr}")
            if result.exit_code != 0: output.append(f"Exit Code: {result.exit_code}")
            
            return "\n".join(output) if output else "Code exécuté avec succès (pas d'output)."
            
    except Exception as e:
        logger.error(f"Error in tool {tool_name}: {e}")
        return f"Erreur lors de l'exécution de l'outil {tool_name}: {str(e)}"
    
    return "Outil inconnu."
