from typing import List
from src.sharedstate import SharedState
from src.utils.logmeister import log_event # Import the logging function
import asyncio
import logging
import logging.handlers
from src.utils.misc import datetime_now as dt_now

class BybitExecutionHandler:
    def __init__(self, ss: SharedState) -> None:
        self.ss = ss
        self.symbol = self.ss.bybit_symbol

    def process(self, data: List) -> None:
        for execution in data:
            if execution["symbol"] != self.symbol:
                continue
            order_id = execution["orderId"]
            # Log fill events 
            if execution['execType'] == 'Trade': 
                message = f"Order ID: {order_id}, Side: {execution['side']}, " \
                          f"Price: {float(execution['execPrice'])}, " \
                          f"Qty: {float(execution['execQty'])}"
                asyncio.create_task(log_event('FILL', message))

            # Log rejections
            elif execution['execType'] == 'Rejected': 
                message = f"Order ID: {order_id}, Reason: {execution.get('rejectReason', 'Unknown')}"
                asyncio.create_task(log_event('REJECTION', message))