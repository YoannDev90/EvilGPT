import logging
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

def setup_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    logging.basicConfig(
        level=level,
        handlers=[handler]
    )

def get_logger(name):
    return logging.getLogger(name)
