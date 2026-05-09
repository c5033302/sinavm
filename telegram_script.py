import requests
from bs4 import BeautifulSoup
import json
import re
from html import escape

CHANNEL = 'vpnbyamoo'   # نام کانال (بدون @)
LIMIT = 5

def clean_text(text):
    if not text:
        return ""
    # حذف لینک‌های تصاویر [*![](...)](...)
    text = re.sub(r'\[\*!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    # حذف لینک‌های [متن](لینک)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # حذف مارک‌داون ساده
    text = re.sub(r'[*_`~>#-]', '', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

# دریافت صفحه کانال
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

posts_data = []
count = 0
for msg in messages:
    if count >= LIMIT:
        break
    text_div = msg.find('div', class_='tgme_widget_message_text')
    if not text_div:
        continue
    raw_text = text_div.get_text(strip=False)
    clean_msg = clean_text(raw_text)
    if not clean_msg:
        continue
    
    # استخراج تاریخ (دقیق)
    date_tag = msg.find('time', class_='datetime')
    if date_tag and date_tag.get('datetime'):
        date_raw = date_tag['datetime'].replace('T', ' ').split('+')[0]
        date_str = date_raw.replace('-', '/')
    else:
        date_str = "تاریخ نامشخص"
    
    # لینک مستقیم پست
    link_tag = msg.find('a', class_='tgme_widget_message_date')
    link = link_tag['href'] if link_tag and link_tag.get('href') else f"https://t.me/{CHANNEL}"
    
    # تبدیل متن با <br> برای HTML
    text_with_br = escape(clean_msg).replace('\n', '<br>')
    # برای دکمه کپی، متن ساده (بدون HTML) آماده می‌کنیم (با جایگزینی <br> با newline)
    plain_for_copy = clean_msg  # این خود متن ساده است (بدون <br>)
    
    posts_data.append({
        "text_html": text_with_br,
        "date": date_str,
        "link": link,
        "plain_text": plain_for_copy
    })
    count += 1

# ---------- ساخت HTML زیبا با CSS و دکمه کپی (بدون خطای f-string) ----------
# این تابع کمکی برای ساختن هر کارت به صورت رشته بدون f-string پیچیده
def make_card(post):
    # آماده‌سازی متن برای کپی (حذف backslash از درون f-string)
    copy_text = post['plain_text']
    # فرار از نقل قول و کاراکترهای خاص برای استفاده در attribute
    copy_text_escaped = copy_text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '&quot;')
    
    return f'''
    <div class="card">
        <div class="card-header">
            <div class="avatar">📢</div>
            <div class="meta">
                <a href="https://t.me/{CHANNEL}" class="channel-name" target="_blank">@{CHANNEL}</a>
                <div class="date">{post['date']}</div>
            </div>
        </div>
        <div class="message-body">{post['text_html']}</div>
        <div class="actions">
            <a href="{post['link']}" class="btn" target="_blank">🔗 مشاهده در تلگرام</a>
            <button class="btn copy-btn" data-text="{copy_text_escaped}">📋 کپی متن</button>
        </div>
    </div>
    '''

cards_html = ''.join([make_card(p) for p in posts_data])

html_output = f"""<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>آخرین پست‌های @{CHANNEL}</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            background: #eef2f7;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Tahoma, sans-serif;
            padding: 20px 12px 40px;
            direction: rtl;
        }}
        .container {{ max-width: 700px; margin: 0 auto; }}
        .header {{
            text-align: center;
            margin-bottom: 24px;
        }}
        .channel-badge {{
            display: inline-flex;
            align-items: center;
            background: white;
            padding: 8px 20px;
            border-radius: 60px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
            gap: 10px;
        }}
        .channel-badge span {{ font-size: 28px; }}
        .channel-badge h1 {{ font-size: 20px; font-weight: 600; color: #1e2a3a; }}
        .card {{
            background: white;
            border-radius: 24px;
            margin-bottom: 18px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03), 0 4px 12px rgba(0,0,0,0.08);
            transition: all 0.2s ease;
            overflow: hidden;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }}
        .card-header {{
            display: flex;
            align-items: center;
            padding: 14px 18px 8px;
            border-bottom: 1px solid #f0f2f5;
        }}
        .avatar {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #29b6f6, #0288d1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
            margin-left: 12px;
        }}
        .meta {{ flex: 1; }}
        .channel-name {{
            font-weight: 700;
            font-size: 15px;
            color: #1e2a3a;
            text-decoration: none;
        }}
        .date {{
            font-size: 11px;
            color: #8e9eae;
            margin-top: 2px;
        }}
        .message-body {{
            padding: 14px 18px;
            font-size: 15px;
            line-height: 1.55;
            color: #1e2a3a;
            word-wrap: break-word;
            white-space: pre-wrap;
        }}
        .actions {{
            padding: 0 18px 14px 18px;
            display: flex;
            gap: 12px;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #f0f4f9;
            border: none;
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 12.5px;
            color: #126fa3;
            text-decoration: none;
            cursor: pointer;
            transition: background 0.2s;
            font-family: inherit;
        }}
        .btn:hover {{ background: #e3eaf1; }}
        .footer {{
            text-align: center;
            margin-top: 28px;
            padding-top: 16px;
            border-top: 1px solid #d0dbe6;
            color: #8e9eae;
            font-size: 12px;
        }}
        @media (max-width: 550px) {{
            body {{ padding: 12px; }}
            .card-header {{ padding: 10px 14px 6px; }}
            .message-body {{ padding: 12px 14px; font-size: 14px; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="channel-badge">
            <span>📱</span>
            <h1>@{CHANNEL}</h1>
        </div>
    </div>
    {cards_html}
    <div class="footer">
        منبع: t.me/{CHANNEL} • به‌روزرسانی خودکار هر ۲ ساعت
    </div>
</div>
<script>
    document.querySelectorAll('.copy-btn').forEach(btn => {{
        btn.addEventListener('click', function(e) {{
            let text = this.getAttribute('data-text');
            navigator.clipboard.writeText(text).then(() => {{
                let original = this.innerHTML;
                this.innerHTML = '✅ کپی شد!';
                setTimeout(() => {{ this.innerHTML = original; }}, 1500);
            }}).catch(() => alert('خطا در کپی'));
        }});
    }});
</script>
</body>
</html>
"""

# ذخیره فایل‌ها
with open('telegram-posts.html', 'w', encoding='utf-8') as f:
    f.write(html_output)

with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(posts_data, f, ensure_ascii=False, indent=2)

print("✅ فایل‌های زیبا و حرفه‌ای ذخیره شدند")
