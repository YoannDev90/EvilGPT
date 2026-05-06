import asyncio
from core.config import cfg, read_system_prompt
from core.model import generate_answer
from managers.memory import MemoryManager
from managers.context import get_server_context, format_context_for_prompt
from utils.logger import get_logger, setup_logging
import discord

setup_logging()
logger = get_logger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class EvilBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = MemoryManager(max_history=15)
        self._processing = set()

    async def on_ready(self):
        logger.info("EvilGPT est en ligne ! Connecté en tant que %s (ID: %s)", self.user, self.user.id)

    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        # Trigger on mention OR if it's a direct message (DMs aren't guilds, but handled above)
        # However, to respond to ALL messages in a channel without mention:
        # Just remove the mentioned_in check.
        
        uid = message.author.id
        if uid in self._processing:
            return

        self._processing.add(uid)
        try:
            async with message.channel.typing():
                # 1. Gather context
                server_ctx = await get_server_context(message.guild)
                ctx_str = format_context_for_prompt(server_ctx)
                
                # 2. Prepare prompt
                system_base = read_system_prompt()
                system_payload = f"{system_base}\n\nContexte actuel :\n{ctx_str}\n\nL'utilisateur s'appelle {message.author.display_name}."
                
                # 3. Handle history
                history = self.memory.get_history(uid)
                
                messages = [{"role": "system", "content": system_payload}]
                for h in history:
                    messages.append({"role": h["role"], "content": h["content"]})
                messages.append({"role": "user", "content": message.content})

                # 4. Generate Answer
                loop = asyncio.get_running_loop()
                ans = await loop.run_in_executor(None, generate_answer, messages)

                if ans and ans.content:
                    self.memory.add_message(uid, "user", message.content)
                    self.memory.add_message(uid, "assistant", ans.content)
                    await message.reply(ans.content)
                    logger.info("Réponse envoyée à %s | Modèle: %s | Temps: %.2fs", message.author, ans.model, ans.response_time or 0)
                else:
                    await message.reply("Je n'ai rien à te dire pour le moment.")

        except Exception as e:
            logger.error("Erreur lors du traitement du message: %s", e, exc_info=True)
            await message.channel.send("Une erreur interne m'empêche de répondre.")
        finally:
            self._processing.discard(uid)

def run_bot():
    if not cfg.BOT_TOKEN:
        logger.error("BOT_TOKEN est manquant dans l'environnement !")
        return
    client = EvilBot(intents=intents)
    client.run(cfg.BOT_TOKEN)
