import ccxt
import time
import requests
import os

# Load Binance API credentials securely
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Connect to Binance Futures
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# Get market trend (using moving averages)
def get_market_trend(symbol='BTC/USDT', timeframe='1h', limit=50):
    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    closes = [candle[4] for candle in candles]
    short_ma = sum(closes[-7:]) / 7
    long_ma = sum(closes[-25:]) / 25
    if short_ma > long_ma:
        return 'BUY'
    elif short_ma < long_ma:
        return 'SELL'
    else:
        return None

# Fetch basic sentiment from Fear & Greed Index
def get_news_sentiment():
    try:
        response = requests.get('https://api.alternative.me/fng/?limit=1&format=json')
        score = int(response.json()['data'][0]['value'])
        return 'POSITIVE' if score >= 50 else 'NEGATIVE'
    except:
        return 'NEUTRAL'

# Calculate position size based on balance
def calculate_position_size(balance_usdt, risk_percent=1):
    btc_price = exchange.fetch_ticker('BTC/USDT')['last']
    risk_amount = balance_usdt * (risk_percent / 100)
    return round(risk_amount / btc_price, 4)

# Place order with simple SL/TP logic
def place_order(symbol, side, amount, sl_pct=1.5, tp_pct=3.0):
    market_price = exchange.fetch_ticker(symbol)['last']
    sl_price = market_price * (1 - sl_pct / 100) if side == 'BUY' else market_price * (1 + sl_pct / 100)
    tp_price = market_price * (1 + tp_pct / 100) if side == 'BUY' else market_price * (1 - tp_pct / 100)

    order = exchange.create_market_order(symbol, side, amount)
    print(f"{side} order placed: {order['id']} at {market_price}")

    # (Optional) Log SL/TP targets (not live orders)
    print(f"Target TP: {tp_price:.2f}, SL: {sl_price:.2f}")
    return order

# Main loop
while True:
    try:
        balance = exchange.fetch_balance()['total']['USDT']
        sentiment = get_news_sentiment()
        trend = get_market_trend('BTC/USDT')

        print(f"Trend: {trend}, Sentiment: {sentiment}, Balance: ${balance:.2f}")

        if trend and sentiment == 'POSITIVE':
            side = trend
            amount = calculate_position_size(balance)
            place_order('BTC/USDT', side, amount)
        else:
            print("No trade conditions met.")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(60 * 60)  # Run once every hour
