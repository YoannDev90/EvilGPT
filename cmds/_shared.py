import time


def interaction_context(interaction) -> str:
    guild_name = interaction.guild.name if interaction.guild is not None else "DM"
    channel_name = getattr(interaction.channel, "name", None)
    channel_id = getattr(interaction.channel, "id", None)
    if channel_name is None:
        channel_name = f"#{channel_id}" if channel_id is not None else "unknown"

    return (
        f"user={interaction.user} (id={interaction.user.id}), "
        f"guild={guild_name}, channel={channel_name}"
    )


def log_command_start(logger, command_name: str, interaction, **extra) -> None:
    details = interaction_context(interaction)
    if extra:
        details = f"{details}, extra={extra}"
    logger.info("Command /%s invoked (%s)", command_name, details)


def log_command_end(
    logger, command_name: str, start_time: float, status: str = "ok"
) -> None:
    duration = time.perf_counter() - start_time
    logger.info("Command /%s completed in %.2fs (%s)", command_name, duration, status)


def log_command_error(logger, command_name: str, exc: Exception) -> None:
    logger.error("Error in /%s: %s", command_name, exc, exc_info=True)


async def defer_interaction(interaction, *, ephemeral: bool = True) -> bool:
    if interaction.response.is_done():
        return False

    await interaction.response.defer(ephemeral=ephemeral)
    return True


async def send_interaction(
    interaction, *, content=None, embed=None, embeds=None, ephemeral: bool = True
):
    # Build kwargs without passing both `embed` and `embeds` (discord forbids mixing)
    kwargs = {}
    if content is not None:
        kwargs["content"] = content
    if embeds is not None:
        kwargs["embeds"] = embeds
    elif embed is not None:
        kwargs["embed"] = embed
    kwargs["ephemeral"] = ephemeral

    if interaction.response.is_done():
        return await interaction.followup.send(**kwargs)

    return await interaction.response.send_message(**kwargs)
