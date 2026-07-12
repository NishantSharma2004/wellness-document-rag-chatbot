import logging
import sys
from config.settings import settings

def setup_logging():
    if not settings.ENABLE_LOGGING:
        logging.getLogger().handlers = []
        logging.getLogger().addHandler(logging.NullHandler())
        return

    log_level = settings.LOG_LEVEL.upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger("wellness_chatbot")
