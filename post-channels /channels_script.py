import json
from ez_telegram import EzClient

# خواندن لیست کانال‌ها
with open('post-channels/channels_name.json', 'r', encoding='utf-8') as f:
    channels = json.load(f)
    channels = [ch.lstrip('@') for ch in channels]

client = EzClient()
all_results = {}

for ch in channels:
    try:
        messages = client.get_messages(ch)   # دریافت همه پیام‌ها
        messages = messages[:10]             # فقط 10 تای آخر
        posts = []
        for msg in messages:
            if msg and msg.strip():
                words = msg.strip().split()
                short_text = ' '.join(words[:5]) + ('...' if len(words) > 5 else '')
                posts.append({
                    "text": msg.strip(),
                    "short_text": short_text,
                    "link": f"https://t.me/{ch}",
                    "date": "نامشخص"
                })
        all_results[ch] = posts
        print(f"✅ {ch}: {len(posts)} posts")
    except Exception as e:
        print(f"❌ {ch}: {e}")
        all_results[ch] = []

with open('post-channels/posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print("channels_script.py finished.")
