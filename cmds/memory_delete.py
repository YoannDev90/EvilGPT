from discord import app_commands


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(name="memory_delete", description="Supprime un tour précis de l'historique")
    @app_commands.describe(turn_id="ID du tour à supprimer")
    async def memory_delete(interaction, turn_id: str):
        try:
            turn = bot.memory.get_turn(turn_id)
        except KeyError:
            await interaction.response.send_message("ID introuvable.", ephemeral=True)
            return

        if turn.user_id != interaction.user.id and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "Permission requise pour supprimer la mémoire d'un autre utilisateur.",
                ephemeral=True,
            )
            return

        deleted = await bot.memory.delete_turn_and_sync(turn.turn_id)
        await interaction.response.send_message(f"Tour `{deleted.turn_id[:8]}` supprimé.", ephemeral=True)
