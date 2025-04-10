import ccxt
import pandas as pd
import time
from ta.trend import SMAIndicator
from email_helper import send_email
from telegram_helper import send_telegram_message

import os
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.mexc({'options': {'defaultType': 'swap'}})

def get_symbols():
    markets = exchange.load_markets()
    return [s for s in markets if s.endswith('/USDT:USDT') and markets[s]['active']]

def check_ma(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        ma20 = SMAIndicator(df['close'], window=20).sma_indicator()
        cur = df['close'].iloc[-1]
        ma = ma20.iloc[-1]
        if cur > ma * 1.05:
            msg = f"[MEXC ALERT] {symbol} 超过 MA20 +10%：当前价格 {cur:.4f}, MA20 {ma:.4f}"
            print(msg)
            send_email("MEXC MA20 Alert", msg)
            send_telegram_message(msg)
    except Exception as e:
        print(f"[ERROR] {symbol}: {e}")

def main():
symbols = get_symbols()
print(f"监控 {len(symbols)} 个交易对")
while True:
    start = time.time()
    for s in symbols:
        check_ma(s)
        time.sleep(0.3)  # 更快地遍历币种
    print("=== 本轮完成，休息直到30秒满 ===")
    elapsed = time.time() - start
    time.sleep(max(0, 30 - elapsed))

if __name__ == "__main__":
    main()
