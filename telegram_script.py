import requests
from bs4 import BeautifulSoup
import json
import re
from html import escape
from urllib.parse import urljoin
from datetime import datetime

# ========== تنظیمات (فقط این بخش را تغییر دهید) ==========
CHANNELS = ['vpnbyamoo', 'sinavm', 'hamclasixii']   # نام کانال‌ها بدون @
LIMIT_PER_CHANNEL = 10               # تعداد پست از هر کانال
# =======================================================

def clean_text(text):
    """حذف مارک‌داون و لینک‌های اضافی از متن"""
    if not text:
        return ""
    # حذف لینک تصاویر [*![](...)](...)
    text = re.sub(r'\[\*!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    # حذف لینک‌های معمولی [متن](لینک)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # حذف کاراکترهای مارک‌داون
    text = re.sub(r'[*_`~>#-]', '', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def extract_date_from_message(msg_soup):
    """استخراج تاریخ و زمان از یک پیام با چند روش fallback"""
    # روش اول: تگ time با attribute datetime
    time_tag = msg_soup.find('time', class_='datetime')
    if time_tag and time_tag.get('datetime'):
        try:
            dt = time_tag['datetime'].replace('T', ' ').split('+')[0]
            # تبدیل به فرمت 2025/02/17 14:30
            return dt.replace('-', '/')
        except:
            pass
    # روش دوم: جستجوی لینک تاریخ و گرفتن متن span
    date_link = msg_soup.find('a', class_='tgme_widget_message_date')
    if date_link:
        span = date_link.find('span', class_='time')
        if span:
            raw = span.get_text(strip=True)
            # معمولا فرمت "HH:MM" یا "HH:MM DD.MM.YYYY"
            if ':' in raw:
                return raw
    # روش سوم: جستجوی هر تگ small یا span با کلاس زمان
    time_span = msg_soup.find('span', class_='message_date')
    if time_span:
        return time_span.get_text(strip=True)
    return "تاریخ نامشخص"

def extract_images_from_message(msg_soup):
    """استخراج لینک تمام تصاویر یک پیام"""
    images = []
    # روش 1: a با کلاس tgme_widget_message_photo_wrap (پس‌زمینه)
    photo_wraps = msg_soup.find_all('a', class_='tgme_widget_message_photo_wrap')
    for a in photo_wraps:
        style = a.get('style', '')
        match = re.search(r'background-image:url\(\'([^\']+)\'\)', style)
        if match:
            img_url = match.group(1)
            if not img_url.startswith('http'):
                img_url = urljoin('https://t.me', img_url)
            images.append(img_url)
    # روش 2: تگ img با کلاس tgme_widget_message_photo
    if not images:
        img_tags = msg_soup.find_all('img', class_='tgme_widget_message_photo')
        for img in img_tags:
            src = img.get('src')
            if src:
                images.append(urljoin('https://t.me', src))
    # روش 3: تگ‌های تصویر داخل message_body (گاهی اوقات)
    if not images:
        all_imgs = msg_soup.find_all('img')
        for img in all_imgs:
            src = img.get('src')
            if src and 'tgme_widget_message_photo' in img.get('class', []):
                images.append(urljoin('https://t.me', src))
    return images

def fetch_channel_posts(channel, limit):
    url = f"https://t.me/s/{channel}"
    try:
        resp = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message')
        print(f"✅ {channel}: {len(messages)} پیام یافت شد")
    except Exception as e:
        print(f"❌ خطا در {channel}: {e}")
        return []

    posts = []
    for msg in messages[:limit]:
        text_div = msg.find('div', class_='tgme_widget_message_text')
        if not text_div:
            continue
        raw_text = text_div.get_text(strip=False)
        clean_msg = clean_text(raw_text)
        if not clean_msg:
            continue

        date_str = extract_date_from_message(msg)
        link_tag = msg.find('a', class_='tgme_widget_message_date')
        link = link_tag['href'] if link_tag else f"https://t.me/{channel}"
        images = extract_images_from_message(msg)

        posts.append({
            "text_html": escape(clean_msg).replace('\n', '<br>'),
            "date": date_str,
            "link": link,
            "plain_text": clean_msg,
            "images": images
        })
    return posts

# ------------------- دریافت داده از همه کانال‌ها -------------------
all_posts = {}
for ch in CHANNELS:
    all_posts[ch] = fetch_channel_posts(ch, LIMIT_PER_CHANNEL)

# ================== تولید HTML با طراحی ۱۰۰٪ شبیه تلگرام ==================
# ساخت سایدبار
sidebar_items = ''.join([f'<div class="chat-item" data-channel="{ch}"><div class="avatar">📢</div><div class="chat-info"><div class="chat-name">@{ch}</div><div class="chat-last">پیام‌ها</div></div></div>' for ch in CHANNELS])

# ساخت محتوای هر کانال (به صورت جدا)
channel_content_divs = {}
for ch, posts in all_posts.items():
    if not posts:
        channel_content_divs[ch] = '<div class="no-posts">هیچ پستی یافت نشد</div>'
        continue
    posts_html = ''
    for p in posts:
        # ساخت تصاویر
        images_html = ''
        if p['images']:
            for img_url in p['images']:
                images_html += f'<div class="message-photo"><img src="{img_url}" loading="lazy"></div>'
        else:
            images_html = '<div class="no-photo">🖼️ بدون تصویر</div>'
        copy_data = p['plain_text'].replace('\\', '\\\\').replace("'", "\\'").replace('"', '&quot;')
        posts_html += f'''
        <div class="message">
            <div class="message-avatar">📢</div>
            <div class="message-bubble">
                <div class="bubble-header">
                    <span class="sender">@{ch}</span>
                    <span class="time">{p['date']}</span>
                </div>
                <div class="bubble-text">{p['text_html']}</div>
                <div class="bubble-media">{images_html}</div>
                <div class="bubble-footer">
                    <a href="{p['link']}" class="btn" target="_blank">🔗 مشاهده در تلگرام</a>
                    <button class="btn copy-btn" data-text="{copy_data}">📋 کپی متن</button>
                </div>
            </div>
        </div>
        '''
    channel_content_divs[ch] = posts_html

# تبدیل به HTML نهایی
content_switcher = ''.join([f'<div id="channel-{ch}" class="channel-messages" style="display: none;">{channel_content_divs[ch]}</div>' for ch in CHANNELS])

html_code = f"""<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تلگرام میرور | کانال‌های منتخب</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css" rel="stylesheet">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            background: #0e1621;  /* رنگ پس‌زمینه تلگرام (دارک) */
            font-family: 'Vazir', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Tahoma, sans-serif;
            direction: rtl;
            height: 100vh;
            overflow: hidden;
        }}
        /* ساختار اصلی: شبیه تلگرام دسکتاپ */
        .telegram-app {{
            display: flex;
            height: 100vh;
            width: 100%;
        }}
        /* سایدبار (لیست چت‌ها) */
        .sidebar {{
            width: 320px;
            background: #17212b;
            border-left: 1px solid #2b3a4a;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }}
        .sidebar-header {{
            padding: 16px;
            background: #17212b;
            border-bottom: 1px solid #2b3a4a;
            font-weight: 600;
            font-size: 20px;
            color: #ffffff;
        }}
        .chat-list {{
            flex: 1;
        }}
        .chat-item {{
            display: flex;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            transition: background 0.2s;
            gap: 12px;
        }}
        .chat-item:hover {{
            background: #2b3a4a;
        }}
        .chat-item.active {{
            background: #2c3e50;
        }}
        .chat-item .avatar {{
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #29b6f6, #0288d1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
        }}
        .chat-info {{
            flex: 1;
        }}
        .chat-name {{
            font-weight: 600;
            color: #ffffff;
            font-size: 16px;
        }}
        .chat-last {{
            font-size: 13px;
            color: #8e9eae;
            margin-top: 4px;
        }}
        /* منطقه اصلی پیام‌ها */
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #0e1621;
            overflow: hidden;
        }}
        .messages-area {{
            flex: 1;
            overflow-y: auto;
            padding: 20px 16px;
        }}
        .channel-messages {{
            max-width: 800px;
            margin: 0 auto;
        }}
        /* استایل حباب پیام (شبیه تلگرام) */
        .message {{
            display: flex;
            margin-bottom: 24px;
            gap: 12px;
        }}
        .message-avatar {{
            width: 42px;
            height: 42px;
            background: #29b6f6;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            flex-shrink: 0;
        }}
        .message-bubble {{
            background: #17212b;
            border-radius: 18px;
            padding: 12px 16px;
            max-width: calc(100% - 60px);
            box-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }}
        .bubble-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
            font-size: 13px;
        }}
        .sender {{
            font-weight: 700;
            color: #29b6f6;
        }}
        .time {{
            color: #8e9eae;
            font-size: 11px;
        }}
        .bubble-text {{
            color: #ffffff;
            font-size: 15px;
            line-height: 1.5;
            word-wrap: break-word;
            white-space: pre-wrap;
        }}
        .bubble-media {{
            margin-top: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .message-photo {{
            flex: 1 1 200px;
            max-width: 100%;
        }}
        .message-photo img {{
            width: 100%;
            border-radius: 16px;
            max-height: 260px;
            object-fit: cover;
            border: 1px solid #2b3a4a;
        }}
        .no-photo {{
            color: #8e9eae;
            font-size: 12px;
            background: #1f2c38;
            padding: 8px 12px;
            border-radius: 20px;
            text-align: center;
        }}
        .bubble-footer {{
            margin-top: 12px;
            display: flex;
            gap: 8px;
        }}
        .btn {{
            background: #2b3a4a;
            border: none;
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 12px;
            color: #8e9eae;
            cursor: pointer;
            text-decoration: none;
            transition: 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .btn:hover {{
            background: #3a4a5a;
            color: #ffffff;
        }}
        .no-posts {{
            text-align: center;
            color: #8e9eae;
            padding: 40px;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #5e6e7e;
            padding: 12px;
            border-top: 1px solid #2b3a4a;
        }}
        @media (max-width: 700px) {{
            .sidebar {{
                width: 80px;
            }}
            .chat-info {{
                display: none;
            }}
            .chat-item {{
                justify-content: center;
                padding: 12px 0;
            }}
        }}
    </style>
</head>
<body>
<div class="telegram-app">
    <div class="sidebar">
        <div class="sidebar-header">📡 کانال‌ها</div>
        <div class="chat-list" id="chat-list">
            {sidebar_items}
        </div>
    </div>
    <div class="main-content">
        <div class="messages-area" id="messages-area">
            {content_switcher}
        </div>
        <div class="footer">به‌روزرسانی خودکار هر ۲ ساعت • {len(CHANNELS)} کانال</div>
    </div>
</div>
<script>
    // مدیریت سایدبار و تغییر کانال
    const chatItems = document.querySelectorAll('.chat-item');
    const channelDivs = {{
        {', '.join([f"'{ch}': document.getElementById('channel-{ch}')" for ch in CHANNELS])}
    }};

    function showChannel(channel) {{
        for(let id in channelDivs) {{
            if(channelDivs[id]) channelDivs[id].style.display = 'none';
        }}
        if(channelDivs[channel]) channelDivs[channel].style.display = 'block';
        chatItems.forEach(item => {{
            if(item.getAttribute('data-channel') === channel)
                item.classList.add('active');
            else
                item.classList.remove('active');
        }});
    }}

    chatItems.forEach(item => {{
        item.addEventListener('click', () => {{
            const ch = item.getAttribute('data-channel');
            showChannel(ch);
        }});
    }});

    // فعال کردن اولین کانال به صورت پیش‌فرض
    if(chatItems.length) {{
        const first = chatItems[0].getAttribute('data-channel');
        showChannel(first);
    }}

    // دکمه کپی متن
    document.querySelectorAll('.copy-btn').forEach(btn => {{
        btn.addEventListener('click', function(e) {{
            const text = this.getAttribute('data-text');
            navigator.clipboard.writeText(text).then(() => {{
                const old = this.innerHTML;
                this.innerHTML = '✅ کپی شد!';
                setTimeout(() => {{ this.innerHTML = old; }}, 1500);
            }}).catch(() => alert('خطا در کپی'));
        }});
    }});
</script>
</body>
</html>
"""

# ذخیره فایل‌ها
with open('telegram-posts.html', 'w', encoding='utf-8') as f:
    f.write(html_code)

# ذخیره JSON خلاصه برای استفاده‌های دیگر
json_data = {ch: [{"text": p['plain_text'], "date": p['date'], "link": p['link'], "images": p['images']} for p in posts] for ch, posts in all_posts.items()}
with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)

print("✅ فایل HTML با طراحی ۱۰۰٪ شبیه تلگرام (سایدبار، تصاویر، تاریخ) ذخیره شد.")
