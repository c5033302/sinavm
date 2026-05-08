import json
import re
from telegram_channel_viewer import channel

CHANNEL = 'sinavm'   # نام کانال (بدون @)
LIMIT = 5

def clean(text):
    if not text:
        return ""
    # حذف لینک‌های تصاویر
    text = re.sub(r'\[\*!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    # حذف مارک‌داون ساده
    text = re.sub(r'[*_`~>#]', '', text)
    text = text.replace('\n', '<br>')
    return text.strip()

try:
    ch = channel(CHANNEL)
    posts = ch.messages[:LIMIT]
    print(f"✅ {len(posts)} پست گرفته شد")
except Exception as e:
    print(f"❌ خطا: {e}")
    posts = []

# ساخت HTML با استایل کارتی و اطلاعات کامل
html = f"""<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"><title>آخرین پست‌های @{CHANNEL}</title>
<style>
body {{background:#eef2f7; font-family:Tahoma,sans-serif; padding:20px; margin:0;}}
.container {{max-width:700px; margin:0 auto;}}
.card {{background:white; border-radius:16px; padding:16px; margin-bottom:18px; box-shadow:0 2px 8px rgba(0,0,0,0.08);}}
.channel {{font-weight:bold; color:#1e88e5; font-size:16px;}}
.date {{font-size:12px; color:#888; margin:6px 0;}}
.text {{margin:12px 0; line-height:1.6; word-break:break-word;}}
.link {{display:inline-block; background:#e3f2fd; padding:6px 14px; border-radius:30px; text-decoration:none; font-size:13px; color:#0b5e7e;}}
.link:hover {{background:#bbdefb;}}
.footer {{text-align:center; font-size:12px; color:#888; margin-top:20px;}}
</style>
</head>
<body>
<div class="container">
<h3 style="text-align:center;">📱 @{CHANNEL}</h3>
"""

data = []
for p in posts:
    if not p.text or not p.text.strip():
        continue
    clean_text = clean(p.text)
    if not clean_text:
        continue
    date_str = p.date.strftime('%Y/%m/%d %H:%M') if p.date else 'تاریخ نامشخص'
    link = f"https://t.me/{CHANNEL}/{p.id}"
    html += f"""
    <div class="card">
        <div class="channel">@{CHANNEL}</div>
        <div class="date">{date_str}</div>
        <div class="text">{clean_text}</div>
        <a href="{link}" class="link" target="_blank">مشاهده در تلگرام</a>
    </div>
    """
    data.append({"text": p.text, "clean_text": clean_text, "date": date_str, "link": link})

if not data:
    html += '<div class="card">هیچ پستی یافت نشد</div>'

html += '<div class="footer">به‌روزرسانی خودکار هر ۲ ساعت</div></div></body></html>'

with open('telegram-posts.html', 'w', encoding='utf-8') as f:
    f.write(html)
with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ فایل‌های زیبا ذخیره شدند")
