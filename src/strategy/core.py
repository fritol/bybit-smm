import asyncio
from src.utils.misc import datetime_now as dt_now
from src.strategy.ws_feeds.bybitmarketdata import BybitMarketData
from src.strategy.ws_feeds.binancemarketdata import BinanceMarketData
from src.strategy.ws_feeds.bybitprivatedata import BybitPrivateData
from src.strategy.marketmaker import MarketMaker
from src.strategy.oms import OMS
from src.sharedstate import SharedState


import logging
import logging.handlers
from src.utils.misc import datetime_now as dt_now
from src.strategy.ws_feeds.bybitprivatedata import log_event 


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

class DataFeeds:
    """
    Initializes and manages WebSocket data feeds for market and private data from Bybit and Binance.
    """

    def __init__(self, ss: SharedState) -> None:
        """
        Initializes the DataFeeds with shared application state.

        Parameters
        ----------
        ss : SharedState
            An instance of SharedState containing shared application data.
        """
        self.ss = ss

    async def start_feeds(self) -> None:
        """
        Starts the WebSocket data feeds asynchronously.
        """
        tasks = [
            asyncio.create_task(BybitMarketData(self.ss).start_feed()),
            asyncio.create_task(BybitPrivateData(self.ss).start_feed())
        ]

        if self.ss.primary_data_feed == "BINANCE":
            tasks.append(asyncio.create_task(BinanceMarketData(self.ss).start_feed()))

        await asyncio.gather(*tasks)


class Strategy:
    """
    Defines and executes the trading strategy using market data and order management systems.
    """

    def __init__(self, ss: SharedState) -> None:
        """
        Initializes the Strategy with shared application state.

        Parameters
        ----------
        ss : SharedState
            An instance of SharedState containing shared application data.
        """
        self.ss = ss

    async def _wait_for_ws_confirmation_(self) -> None:
        """
        Waits for confirmation that the WebSocket connections are established.
        """
        while True: 
            await asyncio.sleep(1)  # Check every second

            if not self.ss.bybit_ws_connected:
                continue

            if self.ss.primary_data_feed == "BINANCE" and not self.ss.binance_ws_connected:
                continue

            break

    async def primary_loop(self) -> None:
        """
        The primary loop of the strategy, executing continuously after WebSocket confirmations.
        """
        print(f"{dt_now()}: Starting data feeds...")
        await self._wait_for_ws_confirmation_()
        print(f"{dt_now()}: Starting strategy...")

        while True:
            await asyncio.sleep(1)  # Strategy iteration delay
            new_orders, spread = MarketMaker(self.ss).generate_quotes(debug=False)
            await OMS(self.ss).run(new_orders, spread)

    async def run(self) -> None:
        """
        Runs the strategy by starting data feeds and entering the primary strategy loop.
        """
        await asyncio.gather(
            DataFeeds(self.ss).start_feeds(),
            self.primary_loop()
        )