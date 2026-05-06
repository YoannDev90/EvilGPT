import discord
from utils.logger import get_logger

logger = get_logger(__name__)

async def get_server_context(guild: discord.Guild):
    """Gather context about the current server."""
    # Essayer de récupérer les membres si le cache est vide
    if not guild.chunked and guild.member_count < 1000:
        try:
            await guild.chunk()
        except Exception:
            pass

    context = {
        "server_name": guild.name,
        "member_count": guild.member_count,
        "members": [m.display_name for m in guild.members[:30]], # Limité pour éviter de saturer le prompt
        "emojis": [str(e) for e in guild.emojis[:20]], # Limit to avoid bloat
        "roles": [r.name for r in guild.roles if not r.managed and r.name != "@everyone"][:15],
    }
    return context

def format_context_for_prompt(context: dict):
    """Format the gathered context into a string for the system prompt."""
    lines = [f"Informations sur le serveur Discord actuel '{context['server_name']}':"]
    if context.get('members'):
        lines.append(f"- Membres ({context['member_count']}): {', '.join(context['members'])}")
    else:
        lines.append(f"- Nombre total de membres: {context['member_count']}")
        
    if context['emojis']:
        lines.append(f"- Quelques émojis disponibles: {' '.join(context['emojis'])}")
    if context['roles']:
        lines.append(f"- Rôles principaux: {', '.join(context['roles'])}")
    
    return "\n".join(lines)
