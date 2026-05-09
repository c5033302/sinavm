import requests
from bs4 import BeautifulSoup
import json
import re
from html import escape
from urllib.parse import urljoin
from datetime import datetime

# ========== تنظیمات (فقط همین قسمت رو تغییر بدید) ==========
CHANNELS = ['vpnbyamoo', 'sinavm']   # اسم کانال‌ها، مثل ['channel1', 'channel2']
LIMIT_PER_CHANNEL = 15               # تعداد پیام برای هر کانال
# =======================================================

def clean_text(text):
    if not text:
        return ""
    # حذف لینک‌های تصاویر [*![](...)](...)
    text = re.sub(r'\[\*!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    # حذف لینک‌های معمولی [متن](لینک)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # حذف مارک‌داون ساده
    text = re.sub(r'[*_`~>#-]', '', text)
    # تبدیل newline به <br>
    text = text.replace('\n', '<br>').strip()
    return text

def parse_date(date_str):
    """تبدیل رشته تاریخ به شیء datetime برای مرتب‌سازی"""
    if not date_str or "نامشخص" in date_str:
        return datetime.min
    # فرمت‌های متداول در صفحه t.me
    # مثال: "2025-02-17T14:30:00+00:00" یا "14:30"
    try:
        if 'T' in date_str:
            # حذف timezone
            clean = date_str.split('+')[0].replace('T', ' ')
            return datetime.strptime(clean, '%Y-%m-%d %H:%M:%S')
        elif ':' in date_str and len(date_str) <= 5:
            # فقط ساعت، بدون تاریخ -> آن را قدیمی فرض می‌کنیم
            return datetime.min
        else:
            # تلاش برای فرمت 'YYYY/MM/DD HH:MM'
            return datetime.strptime(date_str, '%Y/%m/%d %H:%M')
    except:
        return datetime.min

def fetch_channel_posts(channel, limit):
    url = f"https://t.me/s/{channel}"
    try:
        response = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message')
        print(f"✅ {channel}: {len(messages)} پیام خام یافت شد")
    except Exception as e:
        print(f"❌ خطا در {channel}: {e}")
        return []

    posts = []
    for msg in messages:
        # ---- استخراج متن ----
        text_div = msg.find('div', class_='tgme_widget_message_text')
        raw_text = text_div.get_text(strip=False) if text_div else ""
        clean_msg = clean_text(raw_text) if raw_text else ""
        
        # ---- استخراج تاریخ و زمان ----
        date_str = "تاریخ نامشخص"
        # روش اول: تگ time
        time_tag = msg.find('time', class_='datetime')
        if time_tag and time_tag.get('datetime'):
            dt = time_tag['datetime'].replace('T', ' ').split('+')[0]
            date_str = dt.replace('-', '/')
        else:
            # روش دوم: لینک تاریخ
            date_link = msg.find('a', class_='tgme_widget_message_date')
            if date_link:
                span = date_link.find('span', class_='time')
                if span:
                    raw_time = span.get_text(strip=True)
                    if ':' in raw_time:
                        date_str = raw_time  # فقط ساعت
                    else:
                        date_str = raw_time
        
        # ---- استخراج لینک مستقیم پست ----
        link_tag = msg.find('a', class_='tgme_widget_message_date')
        link = link_tag['href'] if link_tag else f"https://t.me/{channel}"
        
        # ---- استخراج تصاویر ----
        images = []
        # روش 1: پس‌زمینه عکس
        for a in msg.find_all('a', class_='tgme_widget_message_photo_wrap'):
            style = a.get('style', '')
            match = re.search(r'background-image:url\(\'([^\']+)\'\)', style)
            if match:
                img_url = match.group(1)
                if not img_url.startswith('http'):
                    img_url = urljoin('https://t.me', img_url)
                images.append(img_url)
        # روش 2: تگ img
        if not images:
            for img in msg.find_all('img', class_='tgme_widget_message_photo'):
                src = img.get('src')
                if src:
                    images.append(urljoin('https://t.me', src))
        
        # اگر هم متن نداشت و هم تصویر نداشت، پست را رد نکن (شاید ویدیو باشد)
        # ولی حداقل یک چیز داشته باشد
        if not clean_msg and not images:
            continue
        
        posts.append({
            "text_html": clean_msg if clean_msg else "<i>📱 محتوای رسانه‌ای</i>",
            "raw_text": raw_text,
            "date_str": date_str,
            "link": link,
            "images": images,
            "datetime_obj": parse_date(date_str)
        })
    
    # مرتب‌سازی بر اساس زمان (جدیدترین اول)
    posts.sort(key=lambda x: x['datetime_obj'], reverse=True)
    return posts[:limit]

# ---------- دریافت داده از همه کانال‌ها ----------
all_posts = {}
for ch in CHANNELS:
    all_posts[ch] = fetch_channel_posts(ch, LIMIT_PER_CHANNEL)

# ---------- تولید HTML با سایدبار و حباب (شبیه تلگرام) ----------
# ساخت سایدبار
sidebar_items = ""
for ch, posts in all_posts.items():
    post_count = len(posts)
    sidebar_items += f'''
    <div class="chat-item" data-channel="{ch}">
        <div class="avatar">📢</div>
        <div class="chat-info">
            <div class="chat-name">@{ch}</div>
            <div class="chat-last">{post_count} پیام</div>
        </div>
    </div>
    '''

# ساخت محتوای هر کانال (به صورت جدا)
channel_divs = {}
first_channel = next(iter(all_posts.keys())) if all_posts else None
for ch, posts in all_posts.items():
    if not posts:
        posts_html = '<div class="no-posts">هیچ پیامی یافت نشد</div>'
    else:
        posts_html = ""
        for p in posts:
            # ساخت تصاویر
            images_html = ""
            if p['images']:
                for img_url in p['images']:
                    images_html += f'<div class="message-photo"><img src="{img_url}" loading="lazy"></div>'
            else:
                images_html = '<div class="no-photo">🖼️ بدون تصویر</div>'
            
            # دکمه کپی متن (فقط اگر متن واقعی دارد)
            copy_btn = ''
            if p['raw_text']:
                copy_text = p['raw_text'].replace('\\', '\\\\').replace("'", "\\'").replace('"', '&quot;')
                copy_btn = f'<button class="btn copy-btn" data-text="{copy_text}">📋 کپی متن</button>'
            
            posts_html += f'''
            <div class="message">
                <div class="message-avatar">📢</div>
                <div class="message-bubble">
                    <div class="bubble-header">
                        <span class="sender">@{ch}</span>
                        <span class="time">{p['date_str']}</span>
                    </div>
                    <div class="bubble-text">{p['text_html']}</div>
                    <div class="bubble-media">{images_html}</div>
                    <div class="bubble-footer">
                        <a href="{p['link']}" class="btn" target="_blank">🔗 مشاهده در تلگرام</a>
                        {copy_btn}
                    </div>
                </div>
            </div>
            '''
    channel_divs[ch] = f'<div id="channel-{ch}" class="channel-messages" style="display: {"block" if ch == first_channel else "none"};">{posts_html}</div>'

content_switcher = ''.join(channel_divs.values())

html_output = f"""<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>آرشیو کانال‌های تلگرام</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css" rel="stylesheet">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            background: #0e1621;
            font-family: 'Vazir', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Tahoma, sans-serif;
            direction: rtl;
            height: 100vh;
            overflow: hidden;
        }}
        .telegram-app {{
            display: flex;
            height: 100vh;
            width: 100%;
        }}
        .sidebar {{
            width: 300px;
            background: #17212b;
            border-left: 1px solid #2b3a4a;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }}
        .sidebar-header {{
            padding: 20px 16px;
            background: #17212b;
            border-bottom: 1px solid #2b3a4a;
            font-weight: 600;
            font-size: 18px;
            color: #ffffff;
            text-align: center;
        }}
        .chat-list {{
            flex: 1;
        }}
        .chat-item {{
            display: flex;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            gap: 12px;
            transition: background 0.2s;
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
            flex-wrap: wrap;
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
            font-family: inherit;
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
        <div class="chat-list" id="chat-list">{sidebar_items}</div>
    </div>
    <div class="main-content">
        <div class="messages-area" id="messages-area">{content_switcher}</div>
        <div class="footer">به‌روزرسانی خودکار هر ۲ ساعت • {len(CHANNELS)} کانال</div>
    </div>
</div>
<script>
    const chatItems = document.querySelectorAll('.chat-item');
    const channelDivs = {{
        {', '.join([f"'{ch}': document.getElementById('channel-{ch}')" for ch in all_posts.keys()])}
    }};
    function showChannel(channel) {{
        for(let id in channelDivs) if(channelDivs[id]) channelDivs[id].style.display = 'none';
        if(channelDivs[channel]) channelDivs[channel].style.display = 'block';
        chatItems.forEach(item => {{
            if(item.getAttribute('data-channel') === channel)
                item.classList.add('active');
            else
                item.classList.remove('active');
        }});
    }}
    chatItems.forEach(item => item.addEventListener('click', () => showChannel(item.getAttribute('data-channel'))));
    if(chatItems.length) showChannel(chatItems[0].getAttribute('data-channel'));
    document.querySelectorAll('.copy-btn').forEach(btn => {{
        btn.addEventListener('click', function(e) {{
            let t = this.getAttribute('data-text');
            navigator.clipboard.writeText(t).then(() => {{
                let old = this.innerHTML;
                this.innerHTML = '✅ کپی شد!';
                setTimeout(() => this.innerHTML = old, 1500);
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
    json.dump(all_posts, f, ensure_ascii=False, indent=2)

print("✅ فایل HTML با موفقیت تولید شد (اسکرپینگ مستقیم، بدون نیاز به API)")
