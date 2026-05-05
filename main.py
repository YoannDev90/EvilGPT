import asyncio
import logging

from bot import run_bot

def init_logging(level=logging.INFO):
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    init_logging(level=logging.INFO)
    loop.run_until_complete(run_bot())