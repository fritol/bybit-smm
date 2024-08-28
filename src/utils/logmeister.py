import asyncio
import logging
import logging.handlers
from src.utils.misc import datetime_now as dt_now

async def log_event(event_type: str, message: str):
    """Logs events asynchronously to avoid blocking the main trading loop."""
    try:
        logger = logging.getLogger('hft_logger')
        logger.setLevel(logging.INFO)

        # Rotating file handler for log management
        handler = logging.handlers.RotatingFileHandler(
            'hft_log.txt', maxBytes=10 * 1024 * 1024, backupCount=5
        ) 
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if event_type == 'FILL':
            logger.info(f"FILL - {dt_now()} - {message}")
        elif event_type == 'REJECTION':
            logger.warning(f"REJECTION - {dt_now()} - {message}")
        elif event_type == 'RUNTIME_ERROR':
            logger.error(f"RUNTIME_ERROR - {dt_now()} - {message}")
        elif event_type == 'API_ERROR':
            logger.error(f"API_ERROR - {dt_now()} - {message}")

    except Exception as e:
        print(f"Error during logging: {e}") #  Fallback to console if logging fails