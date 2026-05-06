import re
from typing import Dict, List

from ddgs import DDGS

from utils.logger import get_logger

logger = get_logger(__name__)


def search_ddg(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Return list of search result dicts using ddgs.text: {title, body, href}.
    If ddgs not available, returns empty list.
    """
    if not DDGS:
        logger.error("ddgs library not installed; run pip install ddgs")
        return []

    try:
        with DDGS() as ddgs:
            items = list(ddgs.text(query, max_results=max_results))
            results = []
            for it in items:
                results.append(
                    {
                        "title": it.get("title", ""),
                        "body": it.get("body", ""),
                        "href": it.get("href", ""),
                    }
                )
            return results
    except Exception as e:
        logger.error("DDG Search error: %s", e)
        return []


def _extract_with_ddgs(url: str, fmt: str = "text_plain") -> str:
    """Use DDGS.extract to get content. Returns empty string on failure."""
    if not DDGS:
        return ""
    try:
        with DDGS() as ddgs:
            extracted = ddgs.extract(url, fmt=fmt)
            if isinstance(extracted, dict):
                content = extracted.get("content", "")
            else:
                content = extracted or ""
            content = re.sub(r"\s+", " ", content).strip()
            return content
    except Exception as e:
        logger.debug("ddgs.extract failed for %s: %s", url, e)
        return ""


def get_web_context(query: str, max_results: int = 3) -> str:
    """Perform search + extract each result using ddgs.extract and return formatted context string."""
    results = search_ddg(query, max_results=max_results)
    if not results:
        return "Aucun résultat trouvé sur le web (ou ddgs non installé)."

    ctx_lines = ["Résultats de recherche récents :"]
    for r in results:
        title = r.get("title") or "(no title)"
        href = r.get("href") or ""
        brief = r.get("body") or ""

        # Try ddgs.extract for better snippet
        if href:
            fetched = _extract_with_ddgs(href, fmt="text_plain")
            if fetched:
                brief = fetched

        line = f"- {title}: {brief} (Source: {href})"
        ctx_lines.append(line)

    return "\n".join(ctx_lines)
