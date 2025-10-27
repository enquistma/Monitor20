import asyncio
import ccxt.async_support as ccxt
import time
import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("🚫 TELEGRAM 配置缺失，无法发送消息")
        return

    chat_ids = [cid.strip() for cid in TELEGRAM_CHAT_ID.split(',') if cid.strip()]
    for cid in chat_ids:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": cid, "text": text}
        try:
            response = requests.post(url, data=data, timeout=10)
            if not response.ok:
                print(f"⚠️ 发送到 {cid} 失败: {response.text}")
        except Exception as e:
            print(f"❌ Telegram 发送失败: {e}")

semaphore = asyncio.Semaphore(8)
sem_mexc = asyncio.Semaphore(8)
sem_gate = asyncio.Semaphore(8)

def load_custom_tokens(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

async def fetch_symbols(exchange, custom_path):
    markets = await exchange.load_markets()
    symbols = [s for s in markets if s.endswith('/USDT:USDT')]
    extra = load_custom_tokens(custom_path)
    combined = list(set(symbols + extra))
    return combined

async def fetch_ohlcv_safe(exchange, symbol):
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='5m', limit=21)
        return ohlcv
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {symbol}: {e}")

async def check_ma(exchange, symbol, sem, failure_list):
    async with sem:
        try:
            ohlcv = await fetch_ohlcv_safe(exchange, symbol)
            if len(ohlcv) < 21:
                raise ValueError("Not enough data")

            closes = [x[4] for x in ohlcv]
            ma20 = sum(closes[-21:-1]) / 20
            last = closes[-1]

            if last > ma20 * 1.10:
                msg = f"📈 {exchange.id.upper()} {symbol}\n价格高出 MA20 超过 10%\n当前价：{last:.4f}\nMA20+20%：{ma20*1.2:.4f}"
                print(msg, flush=True)
                send_telegram_message(msg)

        except Exception as e:
            failure_list.append((exchange.id.upper(), symbol, str(e)))

async def main():
    send_telegram_message("✅ Render 上部署成功，启动通知测试")

    exchange_mexc = ccxt.mexc()
    exchange_gate = ccxt.gate()

    while True:
        start_time = time.time()

        symbols_mexc = await fetch_symbols(exchange_mexc, 'custom_mexc.txt')
        symbols_gate = await fetch_symbols(exchange_gate, 'custom_gate.txt')

        print(f"🛠️ MEXC 合约数: {len(symbols_mexc)}, Gate 合约数: {len(symbols_gate)}")

        tasks = []
        failure_list = []

        for s in symbols_mexc:
            tasks.append(check_ma(exchange_mexc, s, sem_mexc, failure_list))
        for s in symbols_gate:
            tasks.append(check_ma(exchange_gate, s, sem_gate, failure_list))

        print(f"🚀 本轮即将检查的交易对数量：{len(tasks)}")

        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time
        print(f"✅ 本轮检查完成，用时 {elapsed:.2f} 秒")

        if failure_list:
            with open("failed_tokens.txt", "a", encoding='utf-8') as f:
                for exch, symbol, err in failure_list:
                    f.write(f"{exch},{symbol},{err}\n")
            print(f"⚠️ 本轮失败交易对数量：{len(failure_list)}")

        print("⏳ 等待30秒后继续...")
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
