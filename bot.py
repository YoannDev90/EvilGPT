import asyncio
import logging
from typing import Set

import discord
from discord import Message

from config import BOT_TOKEN
from ai_utils.ai_model import generate_answer

logger = logging.getLogger(__name__)

# minimal intents
intents = discord.Intents.default()
intents.message_content = True


class MinimalBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self._processing: Set[int] = set()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: Message):
        import time
        msg_recv_ts = time.time()
        
        # ignore bots and DMs
        if message.author.bot or message.guild is None:
            logger.debug("Ignoring bot/DM message")
            return

        uid = message.author.id
        if uid in self._processing:
            logger.warning("User %s already processing, ignoring message", uid)
            return

        self._processing.add(uid)
        try:
            logger.info("[%.3f] Message received from %s: %s", msg_recv_ts, message.author, message.content[:50])

            # build simple messages payload for litellm-style API
            messages = [{"role": "user", "content": message.content}]
            logger.debug("[%.3f] Payload built", time.time())

            # run generate_answer in thread to avoid blocking event loop
            loop = asyncio.get_running_loop()
            logger.info("[%.3f] Submitting to thread pool", time.time())
            ans = await loop.run_in_executor(None, generate_answer, messages)
            exec_ts = time.time()
            logger.info("[%.3f] AI response received after %.2fs", exec_ts, exec_ts - msg_recv_ts)

            # send reply
            if ans and ans.content:
                logger.debug("[%.3f] Sending reply (%d chars)", time.time(), len(ans.content))
                await message.channel.send(ans.content)
                logger.info("[%.3f] Reply sent after %.2fs total", time.time(), time.time() - msg_recv_ts)
            else:
                logger.warning("[%.3f] Empty response", time.time())
                await message.channel.send("(no answer)")

        except Exception as exc:
            logger.exception("[%.3f] Error handling message: %s", time.time(), exc)
            try:
                await message.channel.send("Erreur interne lors du traitement du message.")
            except Exception:
                pass
        finally:
            self._processing.discard(uid)
            logger.debug("[%.3f] Message processing complete for user %s", time.time(), uid)


client = MinimalBot(intents=intents)


def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set in environment")
    client.run(BOT_TOKEN)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_bot()
