import asyncio
import time

import discord
from discord import app_commands

from core.config import cfg, read_system_prompt
from core.model import Answer, generate_answer
from managers.context import format_context_for_prompt, get_server_context
from managers.memory import MemoryManager
from utils.handlers.messages import MessageSender
from utils.logger import get_logger, setup_logging
from utils.web_search import get_web_context

setup_logging()
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
        # Setup commands and sync tree
        await self.setup_commands()
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

            # Prepare prompt
            system_base = read_system_prompt()
            system_payload = (
                f"{system_base}\n\n"
                f"PERSONNALITÉ ACTUELLE : {mood_instructions.get(user_mood)}\n\n"
                f"INSTRUCTIONS OUTILS :\nTu as accès à une recherche web et à une sandbox Python. "
                f"Utilise-les si nécessaire pour répondre de manière précise et méchante.\n\n"
                f"Contexte actuel :\n{ctx_str}\n\n"
                f"L'utilisateur s'appelle {message.author.display_name}."
            )

            # Handle history
            history = self.memory.get_history(uid, limit=self.memory.max_history)

            messages = [{"role": "system", "content": system_payload}]
            for h in history:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": message.content})

            # Activation de l'indicateur "typing" de Discord
            async with message.channel.typing():
                # Start streaming
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
                    channel_id=message.channel.id if hasattr(message.channel, "id") else None,
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
        memory_group = app_commands.Group(name="memory", description="Gère la mémoire persistante")

        self.tree.add_command(memory_group)

        def _format_turn(turn) -> str:
            created = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(turn.created_at))
            user_snippet = turn.user_content.replace("\n", " ")[:120]
            assistant_snippet = (turn.assistant_content or "").replace("\n", " ")[:120]
            lines = [
                f"{turn.turn_id[:8]} | {created} | {turn.user_name} ({turn.user_id})",
                f"  user: {user_snippet}",
            ]
            if assistant_snippet:
                lines.append(f"  bot : {assistant_snippet}")
            return "\n".join(lines)

        @memory_group.command(name="list", description="Liste les derniers tours en mémoire")
        @app_commands.describe(limit="Nombre de tours à afficher", user="Utilisateur cible optionnel")
        async def memory_list(
            interaction: discord.Interaction,
            limit: int = 10,
            user: discord.Member | None = None,
        ):
            target_user = user or interaction.user
            if target_user.id != interaction.user.id and not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    "Permission requise pour voir la mémoire d'un autre utilisateur.",
                    ephemeral=True,
                )
                return

            turns = self.memory.list_turns(target_user.id, limit=max(1, min(limit, 20)))
            if not turns:
                await interaction.response.send_message(
                    "Aucun tour en mémoire pour ce compte.", ephemeral=True
                )
                return

            content = "\n\n".join(_format_turn(turn) for turn in turns)
            if len(content) > 1900:
                content = content[:1900] + "\n..."
            await interaction.response.send_message(f"```text\n{content}\n```", ephemeral=True)

        @memory_group.command(name="delete", description="Supprime un tour précis de l'historique")
        @app_commands.describe(turn_id="ID du tour à supprimer")
        async def memory_delete(interaction: discord.Interaction, turn_id: str):
            try:
                turn = self.memory.get_turn(turn_id)
            except KeyError:
                await interaction.response.send_message(
                    "ID introuvable.", ephemeral=True
                )
                return

            if turn.user_id != interaction.user.id and not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    "Permission requise pour supprimer la mémoire d'un autre utilisateur.",
                    ephemeral=True,
                )
                return

            deleted = await self.memory.delete_turn_and_sync(turn.turn_id)
            await interaction.response.send_message(
                f"Tour `{deleted.turn_id[:8]}` supprimé.", ephemeral=True
            )

        @memory_group.command(name="clear", description="Vide l'historique d'un utilisateur ou le tien")
        @app_commands.describe(user="Utilisateur cible optionnel")
        async def memory_clear(
            interaction: discord.Interaction,
            user: discord.Member | None = None,
        ):
            target_user = user or interaction.user
            if target_user.id != interaction.user.id and not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    "Permission requise pour vider la mémoire d'un autre utilisateur.",
                    ephemeral=True,
                )
                return

            removed = await self.memory.clear_history_and_sync(target_user.id)
            await interaction.response.send_message(
                f"{removed} tour(s) supprimé(s) pour {target_user.display_name}.",
                ephemeral=True,
            )

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
    client.run(cfg.BOT_TOKEN)
