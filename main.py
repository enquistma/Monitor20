import ccxt
import pandas as pd
from ta.trend import SMAIndicator
import time

exchange = ccxt.binance({
    'options': {'defaultType': 'future'}
})

def check_price(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        ma20 = SMAIndicator(df['close'], window=20).sma_indicator()
        current = df['close'].iloc[-1]
        ma_value = ma20.iloc[-1]
        if current > ma_value * 1.15:
            print(f"[ALERT] {symbol} 超过 MA20 +15%：当前价格 {current:.2f}, MA20 {ma_value:.2f}")
    except Exception as e:
        print(f"[ERROR] {symbol}: {e}")

def main():
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']  # 可以扩展成所有合约
    while True:
        for s in symbols:
            check_price(s)
            time.sleep(1)
        time.sleep(300)  # 每5分钟检查一次

if __name__ == "__main__":
    main()
