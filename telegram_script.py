import html
import json
import re
from ez_telegram import EzClient
from markdown import markdown
from bs4 import BeautifulSoup

channel_username = 'sinavm'
LIMIT = 5

def markdown_to_plain_text(md_text):
    """تبدیل متن مارک‌داون به متن ساده"""
    if not md_text:
        return ""
    # تبدیل مارک‌داون به HTML
    html_content = markdown(md_text, extensions=['nl2br'])
    # استخراج متن ساده از HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    plain = soup.get_text()
    # حذف لینک‌های اضافی باقی‌مانده
    plain = re.sub(r'\[.*?\]\(.*?\)', '', plain)
    # حذف کاراکترهای اضافی
    plain = re.sub(r'[*_`~>#]', '', plain)
    # حذف خطوط تکراری
    plain = re.sub(r'\n\s*\n', '\n', plain)
    return plain.strip()

client = EzClient()
try:
    all_msgs = client.get_messages(channel_username)
    messages = all_msgs[:LIMIT] if len(all_msgs) > LIMIT else all_msgs
    print(f"✅ {len(messages)} پست گرفته شد")
except Exception as e:
    print(f"❌ خطا: {e}")
    messages = []

# HTML با استایل مشابه قبل (بدون تغییر)
html_out = """<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"><title>آخرین پست‌ها</title>
<style>
body {background:#eef2f7; font-family:Tahoma,sans-serif; padding:20px; margin:0;}
.container {max-width:700px; margin:0 auto;}
.card {background:white; border-radius:16px; padding:16px; margin-bottom:18px; box-shadow:0 2px 8px rgba(0,0,0,0.08);}
.channel {font-weight:bold; color:#1e88e5; font-size:16px;}
.date {font-size:12px; color:#888; margin:6px 0;}
.text {margin:12px 0; line-height:1.6; word-break:break-word; white-space:pre-wrap;}
.link {display:inline-block; background:#e3f2fd; padding:6px 14px; border-radius:30px; text-decoration:none; font-size:13px; color:#0b5e7e;}
.link:hover {background:#bbdefb;}
.footer {text-align:center; font-size:12px; color:#888; margin-top:20px;}
</style>
</head>
<body>
<div class="container">
<h3 style="text-align:center;">📱 @{channel_username}</h3>
"""

data_json = []
for msg in messages:
    if not msg or not msg.strip():
        continue
    raw_text = msg.strip()
    clean_text = markdown_to_plain_text(raw_text)
    if not clean_text:
        continue
    if len(clean_text) > 300:
        clean_text = clean_text[:300] + '...'
    text = html.escape(clean_text).replace('\n', '<br>')
    link = f"https://t.me/{channel_username}"
    date_str = "تاریخ نامشخص"
    html_out += f"""
    <div class="card">
        <div class="channel">@{channel_username}</div>
        <div class="date">{date_str}</div>
        <div class="text">{text}</div>
        <a href="{link}" class="link" target="_blank">مشاهده در تلگرام</a>
    </div>
    """
    data_json.append({"text": clean_text, "date": 0, "link": link})

if not data_json:
    html_out += '<div class="card">هیچ پستی یافت نشد</div>'

html_out += '<div class="footer">به‌روزرسانی خودکار هر ۲ ساعت</div></div></body></html>'

with open('telegram-posts.html', 'w', encoding='utf-8') as f:
    f.write(html_out)
with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(data_json, f, ensure_ascii=False, indent=2)

print("✅ فایل‌ها ذخیره شدند")
