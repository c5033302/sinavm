import json
import html
from ez_telegram import EzClient

# خواندن لیست کانال‌ها از فایل JSON
try:
    with open('post-channels/channels_name.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)
        # حذف @ از ابتدا اگر باشد
        channels = [ch.lstrip('@') for ch in channels]
    print(f"✅ Loaded {len(channels)} channels: {channels}")
except Exception as e:
    print(f"❌ Error reading channels_name.json: {e}")
    channels = []

if not channels:
    print("No channels to process. Exiting.")
    exit(0)

# ایجاد کلاینت ez-telegram
client = EzClient()
all_results = {}

for ch in channels:
    try:
        # دریافت همه پیام‌ها (بدون limit) و سپس برش دستی
        all_messages = client.get_messages(ch)
        # محدود کردن به 10 پیام آخر (اختیاری، می‌توانید عدد را تغییر دهید)
        messages = all_messages[:10] if len(all_messages) > 10 else all_messages
        
        posts = []
        for msg in messages:
            if msg and msg.strip():
                # خلاصه ۵ کلمه اول
                words = msg.strip().split()
                short_text = ' '.join(words[:5])
                if len(words) > 5:
                    short_text += '...'
                
                posts.append({
                    "text": msg.strip(),
                    "short_text": short_text,
                    "link": f"https://t.me/{ch}",
                    "date": "نامشخص"
                })
        all_results[ch] = posts
        print(f"✅ {ch}: {len(posts)} posts fetched")
    except Exception as e:
        print(f"❌ {ch}: {e}")
        all_results[ch] = []

# ذخیره خروجی در فایل JSON
output_path = 'post-channels/posts_formatted.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"✅ Results saved to {output_path}")
print("channels_script.py finished successfully.")
