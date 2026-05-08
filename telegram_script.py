import requests
from bs4 import BeautifulSoup
import json
import re
from html import escape

CHANNEL = 'sinavm'
LIMIT = 5

def clean_telegram_text(text):
    """تمیز کردن کامل متن از لینک‌های تصاویر، مارک‌داون و کدهای اضافی"""
    if not text:
        return ""
    # حذف لینک‌های تصاویر [*![](...)](...)
    text = re.sub(r'\[\*!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    # حذف لینک‌های معمولی [متن](لینک) - معمولاً در تلگرام لینک به صورت جداگانه است
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # حذف ایموجی‌های یونیکد (اختیاری - اگر نمی‌خواهی ایموجی‌ها حذف شوند، این خط را بردار)
    # text = re.sub(r'[^\w\s\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF\u200c\u200d\u0621-\u064a\u0660-\u0669\u0020\u002E\u061F\u060C]', '', text)
    # حذف کاراکترهای مارک‌داون
    text = re.sub(r'[*_`~>#-]', '', text)
    # حذف فاصله‌های اضافی و خطوط خالی
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

url = f"https://t.me/s/{CHANNEL}"
try:
    response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message')
    print(f"✅ {len(messages)} پست پیدا شد")
except Exception as e:
    print(f"❌ خطا: {e}")
    messages = []

# HTML با استایل خیلی حرفه‌ای (شبیه تلگرام)
html_out = f"""<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>پیام‌های @{CHANNEL}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: #eef2f7;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Tahoma, sans-serif;
            padding: 16px;
            direction: rtl;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
        }}
        .card {{
            background: white;
            border-radius: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.02);
            transition: transform 0.2s, box-shadow 0.2s;
            overflow: hidden;
        }}
        .card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
            transform: translateY(-1px);
        }}
        .card-header {{
            display: flex;
            align-items: center;
            padding: 14px 16px 8px 16px;
            border-bottom: 1px solid #f0f2f5;
        }}
        .avatar {{
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #29b6f6, #0288d1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 18px;
            margin-left: 12px;
        }}
        .channel-info {{
            flex: 1;
        }}
        .channel-name {{
            font-weight: 700;
            font-size: 15px;
            color: #1e2a3a;
            text-decoration: none;
            display: inline-block;
        }}
        .channel-name:hover {{
            text-decoration: underline;
        }}
        .date {{
            font-size: 11px;
            color: #8e9eae;
            margin-top: 2px;
        }}
        .message-text {{
            padding: 12px 16px;
            font-size: 14.5px;
            line-height: 1.55;
            color: #1e2a3a;
            word-wrap: break-word;
            white-space: pre-wrap;
            background: white;
        }}
        .message-link {{
            display: inline-block;
            margin: 0 16px 16px 16px;
            background: #e9f0f5;
            padding: 6px 14px;
            border-radius: 40px;
            font-size: 12.5px;
            color: #126fa3;
            text-decoration: none;
            transition: background 0.2s;
        }}
        .message-link:hover {{
            background: #d4e2ed;
        }}
        .footer {{
            text-align: center;
            font-size: 11px;
            color: #9aaebf;
            margin: 24px 0 16px;
            padding-top: 8px;
            border-top: 1px solid #dce5ec;
        }}
        @media (max-width: 550px) {{
            body {{ padding: 12px; }}
            .card-header {{ padding: 12px 14px 6px; }}
            .message-text {{ padding: 10px 14px; font-size: 14px; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <div style="background: white; border-radius: 28px; padding: 12px 20px; margin-bottom: 20px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
        <span style="font-size: 24px;">📱</span>
        <h2 style="display: inline-block; font-size: 20px; margin-right: 8px; font-weight: 600;">آخرین پست‌های @{CHANNEL}</h2>
    </div>
"""

data_json = []
count = 0
for msg in messages:
    if count >= LIMIT:
        break
    text_div = msg.find('div', class_='tgme_widget_message_text')
    if not text_div:
        continue
    raw_text = text_div.get_text(strip=False)
    clean_msg = clean_telegram_text(raw_text)
    if not clean_msg or len(clean_msg) < 2:
        continue
    
    # استخراج تاریخ
    date_tag = msg.find('time', class_='datetime')
    if date_tag and date_tag.get('datetime'):
        date_str = date_tag['datetime'].replace('T', ' ').split('+')[0].replace('-', '/')
    else:
        date_str = "تاریخ نامشخص"
    
    # استخراج لینک مستقیم پست
    link_tag = msg.find('a', class_='tgme_widget_message_date')
    link = link_tag['href'] if link_tag and link_tag.get('href') else f"https://t.me/{CHANNEL}"
    
    # تبدیل لاین بریک به <br> و ایموجی‌ها را نگه می‌دارد
    text_html = escape(clean_msg).replace('\n', '<br>')
    
    # گاهی متن طولانی را محدود کن (اگه خیلی بلند بود، می‌توانی عدد را زیاد کنی)
    if len(text_html) > 800:
        text_html = text_html[:800] + '...'
    
    html_out += f"""
    <div class="card">
        <div class="card-header">
            <div class="avatar">📢</div>
            <div class="channel-info">
                <a href="https://t.me/{CHANNEL}" class="channel-name" target="_blank">@{CHANNEL}</a>
                <div class="date">{date_str}</div>
            </div>
        </div>
        <div class="message-text">{text_html}</div>
        <a href="{link}" class="message-link" target="_blank">🔗 مشاهده در تلگرام</a>
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
    html_out += '<div class="card" style="text-align:center; padding:32px;">📭 هیچ پستی یافت نشد</div>'

html_out += f"""
    <div class="footer">
        منبع: https://t.me/{CHANNEL} • به‌روزرسانی خودکار هر ۲ ساعت
    </div>
</div>
</body>
</html>
"""

with open('telegram-posts.html', 'w', encoding='utf-8') as f:
    f.write(html_out)
with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(data_json, f, ensure_ascii=False, indent=2)

print("✅ فایل‌ها با موفقیت ذخیره شدند")
