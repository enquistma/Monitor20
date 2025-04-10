import ccxt.async_support as ccxt
import asyncio
import pandas as pd
import random
from ta.trend import SMAIndicator
from email_helper import send_email
from telegram_helper import send_telegram_message
import os
from dotenv import load_dotenv

load_dotenv()

sem_mexc = asyncio.Semaphore(5)
sem_gate = asyncio.Semaphore(5)

async def check_ma(exchange, symbol, sem):
    async with sem:
        try:
            await asyncio.sleep(random.uniform(0.05, 0.15))  # 防止请求过快
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='5m', limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            if len(df) < 20:
                return
            ma20 = SMAIndicator(df['close'], window=20).sma_indicator()
            cur = df['close'].iloc[-1]
            ma = ma20.iloc[-1]
            if cur > ma * 1.10:
                msg = f"[{exchange.id.upper()} ALERT] {symbol} 超过 MA20 +10%：当前 {cur:.4f}，MA20 {ma:.4f}"
                print(msg, flush=True)
                send_email("MA20 Alert", msg)
                send_telegram_message(msg)
        except Exception as e:
            print(f"[{exchange.id.upper()} ERROR] {symbol}: {e}", flush=True)

async def monitor_all():
    exchange_mexc = ccxt.mexc({'options': {'defaultType': 'swap'}})
    exchange_gate = ccxt.gateio({'options': {'defaultType': 'swap'}})

    markets_mexc = await exchange_mexc.load_markets()
    markets_gate = await exchange_gate.load_markets()

    symbols_mexc = [s for s in markets_mexc if s.endswith('/USDT:USDT') and markets_mexc[s]['active']]
    symbols_gate = [s for s in markets_gate if s.endswith('/USDT:USDT') and markets_gate[s]['active']]

    print(f"MEXC 合约数: {len(symbols_mexc)}, Gate 合约数: {len(symbols_gate)}", flush=True)

    while True:
        tasks = []
        for s in symbols_mexc:
            tasks.append(check_ma(exchange_mexc, s, sem_mexc))
        for s in symbols_gate:
            tasks.append(check_ma(exchange_gate, s, sem_gate))

        print(f"🚀 本轮即将检查的交易对数量：{len(tasks)}", flush=True)

        await asyncio.gather(*tasks)
        print("✅ 本轮完成，等待30秒后继续", flush=True)
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor_all())
