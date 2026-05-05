import discord


async def get_all_members(guild: discord.Guild):
    return list(guild.fetch_members(limit=None))
