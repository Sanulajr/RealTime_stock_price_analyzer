import asyncio
import websockets
import json
from collections import deque
import time

# Polygon.io WebSocket URL (example)
POLYGON_WS = "wss://socket.polygon.io/stocks"

API_KEY = "qYz45UAKUFYKnYNubhg3006dnYoCNz9x"

# Sliding window size (e.g. 60 seconds)
WINDOW_SIZE = 60

class StockDataProcessor:
    def __init__(self):
        self.prices = deque()  # store (timestamp, price) tuples

    def add_price(self, timestamp, price):
        self.prices.append((timestamp, price))
        self.cleanup(timestamp)

    def cleanup(self, current_timestamp):
        # Remove prices older than WINDOW_SIZE seconds
        while self.prices and (current_timestamp - self.prices[0][0]) > WINDOW_SIZE:
            self.prices.popleft()

    def moving_average(self):
        if not self.prices:
            return 0
        return sum(price for _, price in self.prices) / len(self.prices)

async def listen():
    processor = StockDataProcessor()

    async with websockets.connect(POLYGON_WS) as ws:
        # Authenticate
        await ws.send(json.dumps({"action": "auth", "params": API_KEY}))

        # Subscribe to a symbol's trades, e.g. AAPL
        await ws.send(json.dumps({"action": "subscribe", "params": "T.AAPL"}))

        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            for event in data:
                # Example event: {'ev': 'T', 'sym': 'AAPL', 'p': 123.45, 't': 1636564834000}
                if event['ev'] == 'T':  # Trade event
                    timestamp = event['t'] / 1000  # convert ms to seconds
                    price = event['p']

                    processor.add_price(timestamp, price)
                    ma = processor.moving_average()
                    print(f"Current Moving Average (last {WINDOW_SIZE}s): {ma:.2f}")

asyncio.run(listen())
