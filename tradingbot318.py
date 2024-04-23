import websocket
import json
from binance.client import Client
import numpy as np

# Binance API credentials (for trading)
API_KEY = '3852LQ47LLWACtpo00Bt3XGD8kf02z8JzK9pPIO4HeRAoPJKmedHXblf0sF8fwvH'
API_SECRET = 'VKNNkIvvWDKg5uVWqlMCMF4pm06a4iOvtJ8OIGDV21UoIV16tso9wvXQng2bBKH6'
client = Client(API_KEY, API_SECRET, testnet=True)  # Set testnet=True for Binance Spot Testnet

# Define the symbol and interval
symbol = 'BTCUSDT'
interval = '1d'  # Daily interval

# Initialize variables
is_in_position = False
entry_price = 0.0
total_profit = 0.0

# Define the WebSocket callback function
def on_message(ws, message):
    global is_in_position, entry_price, total_profit

    msg = json.loads(message)
    candle = msg['k']
    candle_close = float(candle['c'])
    candle_low = float(candle['l'])
    candle_high = float(candle['h'])
    candle_time = pd.to_datetime(candle['t'], unit='ms')

    # Fetch historical data for the last 7 days including today
    historical_data = client.get_historical_klines(symbol, interval, '8 days ago UTC', limit=7)
    historical_data = np.array(historical_data, dtype=np.float64)

    # Extract low prices from historical data
    lows = historical_data[:, 3]

    # Calculate IBS (Internal Bar Strength)
    ibs = (candle_close - candle_low) / (candle_high - candle_low)

    # Check trading conditions
    if ibs >= 0.6 and candle_low < np.min(lows[:-1]) and candle_close < float(historical_data[-2][4]):
        # Buy signal
        if not is_in_position:
            # Place buy order
            order = client.create_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=0.001  # Example quantity, adjust as needed
            )
            print("Buy Order Placed:", order)
            is_in_position = True
            entry_price = candle_close
    elif is_in_position and candle_close > float(historical_data[-2][2]):
        # Sell signal
        # Place sell order
        order = client.create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=0.001  # Example quantity, adjust as needed
        )
        print("Sell Order Placed:", order)
        is_in_position = False
        profit = candle_close - entry_price
        total_profit += profit
        print(f'Profit: {profit}, Total Profit: {total_profit}')

# Define the WebSocket connection URL for the Binance Spot Testnet
ws_url = f"wss://testnet.binance.vision/ws/{symbol.lower()}@kline_{interval}"
ws = websocket.WebSocketApp(ws_url, on_message=on_message)

# Start the WebSocket connection
ws.run_forever()
