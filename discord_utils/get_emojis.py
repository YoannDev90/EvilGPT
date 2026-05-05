import discord


async def get_all_emojis(guild: discord.Guild):
    return list(await guild.fetch_emojis())
