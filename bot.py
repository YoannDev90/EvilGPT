import asyncio
import logging

import discord
from discord.ext import commands

from config import BOT_TOKEN

intents = discord.Intents.default()
# Enable specific privileged intents required by this bot.
# NOTE: These must also be enabled in the Discord Developer Portal
# for your application (Bot -> Privileged Gateway Intents).
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
logger = logging.getLogger()


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

@bot.event
async def on_guild_join(guild):
    logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")


@bot.event
async def on_guild_remove(guild):
    logger.info(f"Removed from guild: {guild.name} (ID: {guild.id})")

@bot.event
async def on_user_install(user):
    logger.info(f"Bot installed by user: {user} (ID: {user.id})")


async def run_bot():
    try:
        logger.info("Logging in...")
        await bot.start(BOT_TOKEN)
    except Exception as exc:
        logger.error(f"Bot failed: {type(exc).__name__}: {exc}")
    finally:
        if not bot.is_closed():
            await bot.close()
        logger.info("Bot stopped")
