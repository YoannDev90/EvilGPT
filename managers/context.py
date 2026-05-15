"""Helpers to gather and format Discord server context.

Provides utilities to collect basic server metadata and format it for
inclusion in system prompts or logs.
"""

import discord

from utils.logger import get_logger

logger = get_logger()


async def get_server_context(guild: discord.Guild):
    """Gather context about the given Discord guild.

    Parameters
    ----------
    guild : discord.Guild
        Guild object to inspect.

    Returns
    -------
    dict
        A dictionary containing summarized server metadata suitable for
        inclusion in prompts (name, member list, emojis, roles, etc.).
    """
    # Essayer de récupérer les membres si le cache est vide
    if not guild.chunked and guild.member_count < 1000:
        try:
            await guild.chunk()
        except Exception:
            pass

    context = {
        "server_name": guild.name,
        "member_count": guild.member_count,
        "members": [
            m.display_name for m in guild.members[:30]
        ],  # Limité pour éviter de saturer le prompt
        "emojis": [str(e) for e in guild.emojis[:20]],  # Limit to avoid bloat
        "roles": [
            r.name for r in guild.roles if not r.managed and r.name != "@everyone"
        ][:15],
    }
    return context


def format_context_for_prompt(context: dict):
    """Convert the server context dict into a human-readable string.

    Parameters
    ----------
    context : dict
        Context dictionary returned by `get_server_context`.

    Returns
    -------
    str
        Multi-line string summarizing the server for model prompts.
    """
    lines = [
        f"Information about the current Discord server '{context['server_name']}':"
    ]
    if context.get("members"):
        lines.append(
            f"- Members ({context['member_count']}): {', '.join(context['members'])}"
        )
    else:
        lines.append(f"- Total member count: {context['member_count']}")

    if context["emojis"]:
        lines.append(f"- Some available emojis: {' '.join(context['emojis'])}")
    if context["roles"]:
        lines.append(f"- Main roles: {', '.join(context['roles'])}")

    return "\n".join(lines)
