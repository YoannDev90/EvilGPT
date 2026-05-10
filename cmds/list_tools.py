import discord
from discord import app_commands

from core.tools import get_combined_tools


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(
        name="list-tools", description="List all tools available to the model"
    )
    async def list_tools(interaction):
        tools = get_combined_tools()

        if not tools:
            embed = discord.Embed(title="No tools available", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        # Group tools by category
        native_tools = [t for t in tools if not t["name"].startswith("mcp_")]
        mcp_tools = [t for t in tools if t["name"].startswith("mcp_")]

        embeds = []

        # Native tools embed
        if native_tools:
            embed = discord.Embed(
                title="🔧 Native Tools",
                color=discord.Color.blurple(),
                description="Built-in sandboxed execution tools",
            )
            for tool in native_tools:
                desc = tool.get("description", "No description")
                embed.add_field(name=f"`{tool['name']}`", value=desc, inline=False)
            embeds.append(embed)

        # MCP tools embed(s)
        if mcp_tools:
            current_embed = discord.Embed(
                title="🔌 MCP Tools",
                color=discord.Color.green(),
                description="Model Context Protocol tools",
            )
            field_count = 0

            for tool in mcp_tools:
                desc = tool.get("description", "No description")
                current_embed.add_field(
                    name=f"`{tool['name']}`", value=desc, inline=False
                )
                field_count += 1

                # Discord embeds have a max of 25 fields, create new embed if needed
                if field_count >= 25:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(
                        title="🔌 MCP Tools (continued)", color=discord.Color.green()
                    )
                    field_count = 0

            if field_count > 0:
                embeds.append(current_embed)

        # Send embeds
        await interaction.response.send_message(embeds=embeds[:10])
        for embed in embeds[10:]:
            await interaction.followup.send(embed=embed)
