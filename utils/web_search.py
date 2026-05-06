import requests
from utils.logger import get_logger

logger = get_logger(__name__)

def search_ddg(query: str, max_results: int = 3) -> str:
    """
    Recherche simple via DuckDuckGo (version HTML/Lite sans API key).
    """
    try:
        # On utilise l'URL 'lite' de DDG qui est plus facile à scraper sans JS
        url = "https://duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        params = {"q": query}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Note: Pour un vrai bot on utiliserait BeautifulSoup, mais on va faire une extraction 
        # minimaliste ou suggérer d'installer duckduckgo-search pour plus de fiabilité.
        # Ici on va simuler une réponse si le scraping échoue ou est trop complexe sans BS4.
        
        return f"[Recherche Web pour: {query}] - Erreur de parsing HTML (besoin de duckduckgo-search)"
    except Exception as e:
        logger.error(f"DDG Search error: {e}")
        return "Impossible de fouiller le web pour le moment."

def get_web_context(query: str) -> str:
    # Pour l'instant on prépare la structure, l'idéal est d'installer duckduckgo-search
    # qui est gratuit et sans clé.
    from duckduckgo_search import DDGS
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "Aucun résultat trouvé sur le web."
            
            ctx = "Résultats de recherche récents :\n"
            for r in results:
                ctx += f"- {r['title']}: {r['body']} (Source: {r['href']})\n"
            return ctx
    except Exception as e:
        logger.error(f"Search Web Error: {e}")
        return "Erreur lors de la recherche DuckDuckGo."
