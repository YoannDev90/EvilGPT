from discord import app_commands


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(name="set_mood", description="Change l'humeur de l'EvilGPT")
    @app_commands.describe(mood="L'humeur souhaitée")
    @app_commands.choices(
        mood=[
            app_commands.Choice(name="Sarcastic", value="sarcastic"),
            app_commands.Choice(name="Aggressive", value="aggressive"),
            app_commands.Choice(name="Evil Mastermind", value="mastermind"),
            app_commands.Choice(name="Nihilist", value="nihilist"),
            app_commands.Choice(name="Chaotic Jester", value="jester"),
        ]
    )
    async def set_mood(interaction, mood: str):
        await bot.memory.set_metadata_and_sync(interaction.user.id, "mood", mood)
        mood_names = {
            "sarcastic": "Sarcastic",
            "aggressive": "Aggressive",
            "mastermind": "Evil Mastermind",
            "nihilist": "Nihilist",
            "jester": "Chaotic Jester",
        }
        await interaction.response.send_message(f"Humeur changée en : **{mood_names[mood]}**. Prépare-toi à souffrir.")
