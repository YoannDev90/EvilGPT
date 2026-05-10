from discord import app_commands


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(
        name="memory_delete", description="Delete a specific turn from conversation history"
    )
    @app_commands.describe(turn_id="Turn ID to delete")
    async def memory_delete(interaction, turn_id: str):
        try:
            turn = bot.memory.get_turn(turn_id)
        except KeyError:
            await interaction.response.send_message("Turn ID not found.", ephemeral=True)
            return

        if (
            turn.user_id != interaction.user.id
            and not interaction.user.guild_permissions.manage_messages
        ):
            await interaction.response.send_message(
                "You don't have permission to delete another user's memory.",
                ephemeral=True,
            )
            return

        deleted = await bot.memory.delete_turn_and_sync(turn.turn_id)
        await interaction.response.send_message(
            f"Turn `{deleted.turn_id[:8]}` deleted.", ephemeral=True
        )
