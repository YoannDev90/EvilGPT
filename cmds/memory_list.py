import time
from discord import app_commands


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(name="memory_list", description="Liste les derniers tours en mémoire")
    @app_commands.describe(limit="Nombre de tours à afficher", user="Utilisateur cible optionnel")
    async def memory_list(interaction, limit: int = 10, user=None):
        target_user = user or interaction.user
        if target_user.id != interaction.user.id and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "Permission requise pour voir la mémoire d'un autre utilisateur.", ephemeral=True
            )
            return

        turns = bot.memory.list_turns(target_user.id, limit=max(1, min(limit, 20)))
        if not turns:
            await interaction.response.send_message("Aucun tour en mémoire pour ce compte.", ephemeral=True)
            return

        def _format_turn(turn):
            created = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(turn.created_at))
            user_snippet = turn.user_content.replace("\n", " ")[:120]
            assistant_snippet = (turn.assistant_content or "").replace("\n", " ")[:120]
            lines = [
                f"{turn.turn_id[:8]} | {created} | {turn.user_name} ({turn.user_id})",
                f"  user: {user_snippet}",
            ]
            if assistant_snippet:
                lines.append(f"  bot : {assistant_snippet}")
            return "\n".join(lines)

        content = "\n\n".join(_format_turn(turn) for turn in turns)
        if len(content) > 1900:
            content = content[:1900] + "\n..."
        await interaction.response.send_message(f"```text\n{content}\n```", ephemeral=True)
