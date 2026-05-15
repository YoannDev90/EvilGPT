"""_summary_."""
import time

import discord
from discord import app_commands

from cmds._shared import log_command_end, log_command_error, log_command_start
from utils.logger import get_logger

logger = get_logger()


async def setup(tree: app_commands.CommandTree, bot):
    """_summary_.

    Parameters
    ----------
    tree : app_commands.CommandTree
        _description_
    bot : _type_
        _description_
    """
    @tree.command(name="ping", description="Check bot latency and responsiveness")
    async def ping(interaction):
        """_summary_.

        Parameters
        ----------
        interaction : _type_
            _description_
        """
        start_time = time.perf_counter()
        log_command_start(logger, "ping", interaction)

        try:
            gateway_ms = round(bot.latency * 1000, 2)

            embed = discord.Embed(
                title="Pong!",
                color=discord.Color.blurple(),
                description="Bot is responsive.",
            )
            embed.add_field(
                name="Gateway Latency", value=f"{gateway_ms} ms", inline=True
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            log_command_end(logger, "ping", start_time)
        except Exception as exc:
            log_command_error(logger, "ping", exc)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Error while checking latency.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "Error while checking latency.", ephemeral=True
                )
