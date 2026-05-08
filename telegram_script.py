import requests
from bs4 import BeautifulSoup
import json
import re
from html import escape
from datetime import datetime

CHANNEL = 'sinavm'
LIMIT = 5

def clean_text(text):
    if not text:
        return ""
    # حذف لینک‌های تصاویر
    text = re.sub(r'\[\*!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    # حذف مارک‌داون ساده
    text = re.sub(r'[*_`~>#]', '', text)
    text = text.strip()
    return text

url = f"https://t.me/s/{CHANNEL}"
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # پیدا کردن همه پست‌ها
    messages = soup.find_all('div', class_='tgme_widget_message')
    print(f"✅ {len(messages)} پست پیدا شد")
except Exception as e:
    print(f"❌ خطا در دریافت صفحه: {e}")
    messages = []

# ساخت HTML با استایل کارتی
html_out = f"""<!DOCTYPE html>
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

data_json = []
count = 0
for msg in messages:
    if count >= LIMIT:
        break
    # استخراج متن
    text_div = msg.find('div', class_='tgme_widget_message_text')
    if not text_div:
        continue
    raw_text = text_div.get_text(strip=False)
    clean_msg = clean_text(raw_text)
    if not clean_msg:
        continue
        
    # استخراج تاریخ
    date_tag = msg.find('time', class_='datetime')
    if date_tag and date_tag.get('datetime'):
        date_str = date_tag['datetime'].replace('T', ' ').split('+')[0]
    else:
        date_str = "تاریخ نامشخص"
    
    # استخراج لینک مستقیم پست
    link_tag = msg.find('a', class_='tgme_widget_message_date')
    if link_tag and link_tag.get('href'):
        link = link_tag['href']
    else:
        link = f"https://t.me/{CHANNEL}"
    
    # محدود کردن طول متن برای نمایش (اختیاری)
    if len(clean_msg) > 300:
        clean_msg = clean_msg[:300] + '...'
    
    text_html = escape(clean_msg).replace('\n', '<br>')
    
    html_out += f"""
    <div class="card">
        <div class="channel">@{CHANNEL}</div>
        <div class="date">{date_str}</div>
        <div class="text">{text_html}</div>
        <a href="{link}" class="link" target="_blank">مشاهده در تلگرام</a>
    </div>
    """
    data_json.append({
        "text": raw_text,
        "clean_text": clean_msg,
        "date": date_str,
        "link": link
    })
    count += 1

if not data_json:
    html_out += '<div class="card">هیچ پستی یافت نشد</div>'

html_out += '<div class="footer">به‌روزرسانی خودکار هر ۲ ساعت</div></div></body></html>'

with open('telegram-posts.html', 'w', encoding='utf-8') as f:
    f.write(html_out)
with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(data_json, f, ensure_ascii=False, indent=2)

print("✅ فایل‌ها با موفقیت ذخیره شدند")
