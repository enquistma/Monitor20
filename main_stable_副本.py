import requests
import os

# 推荐使用环境变量，但你也可以直接粘贴 token：
token = os.getenv("TELEGRAM_BOT_TOKEN") or "在这里粘贴你的BOT_TOKEN"

url = f"https://api.telegram.org/bot{token}/getUpdates"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("获取到的更新内容如下：")
    print(data)
    print("\n请查找其中的 'chat': { 'id': xxx } 部分，即为 chat_id。")
else:
    print("请求失败，请检查 TOKEN 是否正确。")
