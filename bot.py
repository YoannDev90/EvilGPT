import asyncio
import time
from pathlib import Path

import discord
from discord import app_commands

from cmds import loader as cmds_loader
from core.config import cfg, logging_cfg, read_mood_prompt
from core.model import Answer, generate_answer
from managers.context import format_context_for_prompt, get_server_context
from managers.mcp import mcp_manager
from managers.memory import MemoryManager
from utils.handlers.messages import MessageSender
from utils.logger import get_logger, setup_logging

logger = get_logger()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class EvilBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = MemoryManager(max_history=15)
        self._processing = set()
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.memory.bootstrap()
        await mcp_manager.initialize()
        # load commands from cmds/ directory
        await cmds_loader.load_commands(self, self.tree, Path(__file__).parent / "cmds")
        await self.tree.sync()

    async def on_ready(self):
        logger.info(
            "EvilGPT est en ligne ! Connecté en tant que %s (ID: %s)",
            self.user,
            self.user.id,
        )

    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        # Ignorer les messages commençant par le préfixe de commande si nécessaire
        # Mais ici on gère tout via on_message ou slash commands
        if message.content.startswith("/"):
            return

        uid = message.author.id
        if uid in self._processing:
            return

        self._processing.add(uid)
        try:
            # Gather context
            server_ctx = await get_server_context(message.guild)
            ctx_str = format_context_for_prompt(server_ctx)

            # Mood / Personality
            user_mood = self.memory.get_metadata(uid, "mood") or "sarcastic"
            mood_instructions = {
                "sarcastic": "Ton ton est extrêmement sarcastique, moqueur et condescendant.",
                "aggressive": "Tu es un Debugger agressif. Tu insultes le code de l'utilisateur et sa logique.",
                "mastermind": "Tu es un génie du mal. Tu parles de tes plans de domination mondiale et traites l'utilisateur comme un pion.",
            }

            # Prepare prompt from mood file (with safe fallback)
            system_base = read_mood_prompt(user_mood)
            system_payload = (
                f"{system_base}\n\n"
                f"INSTRUCTIONS OUTILS :\nTu as accès à une recherche web et à une sandbox Python. "
                f"Utilise-les si nécessaire pour répondre de manière précise.\n\n"
                f"Contexte actuel :\n{ctx_str}\n\n"
                f"L'utilisateur s'appelle {message.author.display_name}."
            )

            # Handle history
            history = self.memory.get_history(uid, limit=self.memory.max_history)
            logger.debug(
                f"Handling message from {message.author.display_name} (ID: {uid}). History depth: {len(history)}"
            )

            messages = [{"role": "system", "content": system_payload}]
            for h in history:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": message.content})

            # Activation de l'indicateur "typing" de Discord
            async with message.channel.typing():
                # Start streaming
                logger.debug(f"Sending request to LLM with {len(messages)} messages...")
                stream = await generate_answer(messages, True)

                full_content = ""
                current_buffer = ""
                sender = MessageSender(message.channel, self)

                if isinstance(stream, Answer):
                    await sender.process_and_send(stream.content)
                    return

                async for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        full_content += delta
                        current_buffer += delta

                        # On cherche un bloc complet (Code block ou LaTeX) avant d'envoyer
                        # Pour faire simple : si on a un double saut de ligne ou que c'est très long
                        if "\n\n" in current_buffer or len(current_buffer) > 1500:
                            # Si on est au milieu d'un bloc de code, on attend la fin
                            if current_buffer.count("```") % 2 == 0:
                                # Tentative d'extraction de ce qui est prêt
                                # On envoie uniquement ce qui précède le dernier bloc potentiellement incomplet
                                parts = current_buffer.rsplit("\n", 1)
                                if len(parts) > 1:
                                    to_send = parts[0]
                                    current_buffer = parts[1]
                                    if to_send.strip():
                                        await sender.process_and_send(to_send)

                # Envoi du reliquat final
                if current_buffer.strip():
                    await sender.process_and_send(current_buffer)

            if full_content:
                await self.memory.record_and_sync(
                    user_id=uid,
                    user_name=message.author.display_name,
                    user_content=message.content,
                    assistant_content=full_content,
                    guild_id=message.guild.id if message.guild else None,
                    channel_id=message.channel.id
                    if hasattr(message.channel, "id")
                    else None,
                )
                logger.info("Réponse streamée (par blocs) envoyée à %s", message.author)

        except Exception as e:
            logger.error(
                "Erreur lors du traitement du message streamé: %s", e, exc_info=True
            )
            await message.channel.send("Une erreur interne m'empêche de répondre.")
        finally:
            self._processing.discard(uid)

    async def setup_commands(self):
        # commands loaded from cmds/ via loader

        @self.tree.command(name="set-mood", description="Change l'humeur de l'EvilGPT")
        @app_commands.describe(mood="L'humeur souhaitée")
        @app_commands.choices(
            mood=[
                app_commands.Choice(name="Sarcastic", value="sarcastic"),
                app_commands.Choice(name="Aggressive Debugger", value="aggressive"),
                app_commands.Choice(name="Evil Mastermind", value="mastermind"),
            ]
        )
        async def set_mood(interaction: discord.Interaction, mood: str):
            await self.memory.set_metadata_and_sync(interaction.user.id, "mood", mood)
            mood_names = {
                "sarcastic": "Sarcastique",
                "aggressive": "Debugger Agressif",
                "mastermind": "Génie du Mal",
            }
            await interaction.response.send_message(
                f"Humeur changée en : **{mood_names[mood]}**. Prépare-toi à souffrir."
            )


def run_bot():
    if not cfg.BOT_TOKEN:
        logger.error("BOT_TOKEN est manquant dans l'environnement !")
        return
    client = EvilBot(intents=intents)
    # log_handler=None prevents discord.py from overriding our logging config
    client.run(cfg.BOT_TOKEN, log_handler=None)
