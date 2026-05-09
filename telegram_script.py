import requests
from bs4 import BeautifulSoup
import json
import re
from html import escape

# ==================== تنظیمات ====================
CHANNELS = ['vpnbyamoo', 'sinavm']   # نام کانال‌ها (بدون @) - هر تعداد که می‌خواهی اضافه کن
LIMIT_PER_CHANNEL = 10               # تعداد پست از هر کانال
# ================================================

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[\*!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'[*_`~>#-]', '', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def fetch_channel_posts(channel_name, limit):
    url = f"https://t.me/s/{channel_name}"
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message')
        print(f"✅ {channel_name}: {len(messages)} پست پیدا شد")
    except Exception as e:
        print(f"❌ خطا در {channel_name}: {e}")
        return []

    posts = []
    count = 0
    for msg in messages:
        if count >= limit:
            break
        text_div = msg.find('div', class_='tgme_widget_message_text')
        if not text_div:
            continue
        raw_text = text_div.get_text(strip=False)
        clean_msg = clean_text(raw_text)
        if not clean_msg:
            continue

        date_tag = msg.find('time', class_='datetime')
        if date_tag and date_tag.get('datetime'):
            date_raw = date_tag['datetime'].replace('T', ' ').split('+')[0]
            date_str = date_raw.replace('-', '/')
        else:
            date_str = "تاریخ نامشخص"

        link_tag = msg.find('a', class_='tgme_widget_message_date')
        link = link_tag['href'] if link_tag and link_tag.get('href') else f"https://t.me/{channel_name}"

        text_with_br = escape(clean_msg).replace('\n', '<br>')
        posts.append({
            "text_html": text_with_br,
            "date": date_str,
            "link": link,
            "plain_text": clean_msg
        })
        count += 1
    return posts

# دریافت پست‌های همه کانال‌ها
all_data = {}
for ch in CHANNELS:
    all_data[ch] = fetch_channel_posts(ch, LIMIT_PER_CHANNEL)

# ---------- ساخت HTML با چند بخش (هر کانال یک بخش) ----------
def make_card(post, channel_name):
    copy_text_escaped = post['plain_text'].replace('\\', '\\\\').replace("'", "\\'").replace('"', '&quot;')
    return f'''
    <div class="card">
        <div class="card-header">
            <div class="avatar">📢</div>
            <div class="meta">
                <a href="https://t.me/{channel_name}" class="channel-name" target="_blank">@{channel_name}</a>
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

# ساخت HTML نهایی
html_parts = []
for ch, posts in all_data.items():
    if not posts:
        continue
    html_parts.append(f'<div class="channel-section"><h2 class="section-title">📌 کانال @{ch}</h2>')
    for post in posts:
        html_parts.append(make_card(post, ch))
    html_parts.append('</div>')

if not html_parts:
    html_parts.append('<div class="card">هیچ پستی یافت نشد</div>')

cards_html = ''.join(html_parts)

html_output = f"""<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>آخرین پست‌های کانال‌های منتخب</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            background: #eef2f7;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Tahoma, sans-serif;
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
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            margin: 24px 0 12px 0;
            padding-right: 8px;
            border-right: 4px solid #29b6f6;
            color: #1e2a3a;
        }}
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
            <span>📡</span>
            <h1>آخرین پست‌های کانال‌ها</h1>
        </div>
    </div>
    {cards_html}
    <div class="footer">
        به‌روزرسانی خودکار هر ۲ ساعت • {len(CHANNELS)} کانال
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

# ذخیره داده‌های همه کانال‌ها در یک JSON
with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print("✅ فایل‌های چند کاناله با موفقیت ذخیره شدند")
