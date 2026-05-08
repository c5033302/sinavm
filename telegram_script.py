import html
import json
from ez_telegram import EzClient

# نام کانال خود را اینجا وارد کنید (بدون @)
channel_username = 'sinavm'  # ← این را به یوزرنیم کانال خود تغییر دهید

# دریافت پست‌ها با ez-telegram
try:
    client = EzClient()
    all_messages = client.get_messages(channel=channel_username)  # دریافت همه پیام‌ها
    # محدود کردن به 20 پیام اول (جدیدترین‌ها)
    messages_text = all_messages[:20] if len(all_messages) > 20 else all_messages
    print(f"✅ {len(messages_text)} posts fetched.")
except Exception as e:
    print(f"❌ Error fetching posts: {e}")
    messages_text = []

# ----------------------------
# ساخت خروجی HTML و JSON
# ----------------------------
posts_html = '<div class="telegram-posts">\n'
posts_json = []
count = 0

for i, post_text in enumerate(messages_text):
    if post_text and post_text.strip():
        words = post_text.strip().split()
        short_text = ' '.join(words[:5])
        if len(words) > 5:
            short_text += '...'
        text = html.escape(short_text)
        # لینک به صفحه کانال (چون ID دقیق نداریم)
        link = f'https://t.me/{channel_username}'
        # تاریخ دقیق نداریم، می‌توانید خالی بگذارید یا پیام بدهید
        date_str = 'تاریخ نامشخص'

        posts_html += f'<div class="telegram-post"><a href="{link}" target="_blank" class="post-link">{text}</a><br><small>{date_str}</small></div>\n'
        posts_json.append({
            "text": post_text.strip(),
            "date": 0,
            "link": link
        })
        count += 1
        if count == 5:
            break

if count == 0:
    print("No posts with text found")
    posts_html += '<div class="telegram-post">پستی با متن یافت نشد.</div>\n'

posts_html += '</div>'

# ذخیره فایل‌ها
with open('telegram-posts.html', 'w', encoding='utf-8') as f:
    f.write(posts_html)
print("✅ telegram-posts.html saved")

with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(posts_json, f, ensure_ascii=False, indent=2)
print("✅ posts_formatted.json saved")

print("Script finished successfully.")
