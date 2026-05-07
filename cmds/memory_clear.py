from discord import app_commands


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(name="memory_clear", description="Vide l'historique d'un utilisateur ou le tien")
    @app_commands.describe(user="Utilisateur cible optionnel")
    async def memory_clear(interaction, user=None):
        target_user = user or interaction.user
        if target_user.id != interaction.user.id and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "Permission requise pour vider la mémoire d'un autre utilisateur.", ephemeral=True
            )
            return

        removed = await bot.memory.clear_history_and_sync(target_user.id)
        await interaction.response.send_message(
            f"{removed} tour(s) supprimé(s) pour {target_user.display_name}.", ephemeral=True
        )
