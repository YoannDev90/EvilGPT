from discord import app_commands


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(
        name="memory_clear", description="Clear the conversation history for a user"
    )
    @app_commands.describe(user="Target user (optional)")
    async def memory_clear(interaction, user=None):
        target_user = user or interaction.user
        if (
            target_user.id != interaction.user.id
            and not interaction.user.guild_permissions.manage_messages
        ):
            await interaction.response.send_message(
                "You don't have permission to clear another user's memory.",
                ephemeral=True,
            )
            return

        removed = await bot.memory.clear_history_and_sync(target_user.id)
        await interaction.response.send_message(
            f"{removed} turn(s) deleted for {target_user.display_name}.",
            ephemeral=True,
        )
