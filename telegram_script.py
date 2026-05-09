import requests
from bs4 import BeautifulSoup
import json
import re
from html import escape
from urllib.parse import urljoin

# ========== تنظیمات (تنها قسمتی که باید تغییر دهید) ==========
CHANNELS = ['vpnbyamoo', 'sinavm', 'hamclasixii']   # لیست کانال‌ها بدون @
LIMIT_PER_CHANNEL = 10               # تعداد پست از هر کانال
# ============================================================

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
        response = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message')
        print(f"✅ {channel_name}: {len(messages)} پست یافت شد")
    except Exception as e:
        print(f"❌ خطا در {channel_name}: {e}")
        return []

    posts = []
    for idx, msg in enumerate(messages):
        if idx >= limit:
            break

        # ---------- متن ----------
        text_div = msg.find('div', class_='tgme_widget_message_text')
        if not text_div:
            continue
        raw_text = text_div.get_text(strip=False)
        clean_msg = clean_text(raw_text)
        if not clean_msg:
            continue

        # ---------- تاریخ (با روش مطمئن) ----------
        date_str = "تاریخ نامشخص"
        # روش اول: تگ time
        time_tag = msg.find('time', class_='datetime')
        if time_tag and time_tag.get('datetime'):
            date_raw = time_tag['datetime'].replace('T', ' ').split('+')[0]
            date_str = date_raw.replace('-', '/')
        else:
            # روش دوم: جستجوی متن تاریخ در عنصر حاوی لینک
            date_link = msg.find('a', class_='tgme_widget_message_date')
            if date_link:
                span = date_link.find('span', class_='time')
                if span:
                    date_str = span.get_text(strip=True)
        # تبدیل به فرمت خوانا: 2025/02/17 14:30
        if len(date_str.split()) == 1:
            # فقط تاریخ بدون ساعت
            date_str = date_str + " --"
        # ---------- لینک پست ----------
        link_tag = msg.find('a', class_='tgme_widget_message_date')
        link = link_tag['href'] if link_tag and link_tag.get('href') else f"https://t.me/{channel_name}"

        # ---------- استخراج تصاویر (سه روش مختلف) ----------
        images = []
        # روش 1: تگ‌های a با تصویر پس‌زمینه
        photo_wraps = msg.find_all('a', class_='tgme_widget_message_photo_wrap')
        for a in photo_wraps:
            style = a.get('style', '')
            bg_match = re.search(r'background-image:url\(\'([^\']+)\'\)', style)
            if bg_match:
                img_url = bg_match.group(1)
                if not img_url.startswith('http'):
                    img_url = urljoin('https://t.me', img_url)
                images.append(img_url)
        # روش 2: تگ‌های img داخل پیام
        if not images:
            img_tags = msg.find_all('img', class_='tgme_widget_message_photo')
            for img in img_tags:
                src = img.get('src')
                if src:
                    img_url = urljoin('https://t.me', src)
                    images.append(img_url)
        # روش 3: اگر تصویری از نوع ویدیو/گالری باشد
        if not images:
            video_wraps = msg.find_all('a', class_='tgme_widget_message_video_wrap')
            for v in video_wraps:
                style = v.get('style', '')
                bg_match = re.search(r'background-image:url\(\'([^\']+)\'\)', style)
                if bg_match:
                    img_url = bg_match.group(1)
                    images.append(urljoin('https://t.me', img_url))

        posts.append({
            "text_html": escape(clean_msg).replace('\n', '<br>'),
            "date": date_str,
            "link": link,
            "plain_text": clean_msg,
            "images": images
        })
    return posts

# دریافت داده‌ها
all_data = {}
for ch in CHANNELS:
    all_data[ch] = fetch_channel_posts(ch, LIMIT_PER_CHANNEL)

# ========== تولید HTML با سایدبار و طراحی شیک ==========
def build_post_card(post, channel_name):
    copy_text_escaped = post['plain_text'].replace('\\', '\\\\').replace("'", "\\'").replace('"', '&quot;')
    images_html = ''
    if post['images']:
        for img_url in post['images']:
            images_html += f'<div class="post-img"><img src="{img_url}" loading="lazy"></div>'
    else:
        images_html = '<div class="no-img">🖼️ تصویری وجود ندارد</div>'
    return f'''
    <div class="tg-message">
        <div class="msg-header">
            <div class="avatar">📢</div>
            <div class="msg-meta">
                <span class="msg-channel">@{channel_name}</span>
                <span class="msg-date">{post['date']}</span>
            </div>
        </div>
        <div class="msg-text">{post['text_html']}</div>
        <div class="msg-media">{images_html}</div>
        <div class="msg-actions">
            <a href="{post['link']}" class="btn" target="_blank">🔗 مشاهده در تلگرام</a>
            <button class="btn copy-btn" data-text="{copy_text_escaped}">📋 کپی متن</button>
        </div>
    </div>
    '''

# ساخت سایدبار
sidebar_items = ''.join([f'<li class="channel-item" data-channel="{ch}">📌 @{ch}</li>' for ch in CHANNELS])

# ساخت محتوای پست‌ها برای هر کانال (به صورت جداگانه)
channel_contents = {}
for ch, posts in all_data.items():
    cards = ''.join([build_post_card(p, ch) for p in posts])
    if not cards:
        cards = '<div class="no-posts">هیچ پستی یافت نشد</div>'
    channel_contents[ch] = f'<div id="channel-{ch}" class="channel-posts" style="display: block;">{cards}</div>'

content_html = ''.join([channel_contents[ch] for ch in CHANNELS])

html_output = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>آرشیو کانال‌های تلگرام</title>
    <!-- فونت زیبای فارسی Vazir (جایگزین امن) -->
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css" rel="stylesheet" type="text/css" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #f1f3f6;
            font-family: 'Vazir', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Tahoma, sans-serif;
            direction: rtl;
            height: 100vh;
            overflow: hidden;
        }}
        /* ساختار اصلی: سایدبار + محتوا */
        .app {{
            display: flex;
            height: 100vh;
            width: 100%;
        }}
        /* سایدبار (سبک تلگرام دسکتاپ) */
        .sidebar {{
            width: 280px;
            background: white;
            border-left: 1px solid #e0e0e0;
            display: flex;
            flex-direction: column;
            box-shadow: 0 0 10px rgba(0,0,0,0.05);
            z-index: 2;
            overflow-y: auto;
        }}
        .sidebar-header {{
            padding: 20px 16px;
            border-bottom: 1px solid #eef2f7;
            font-weight: 700;
            font-size: 20px;
            background: #fff;
            color: #1e2a3a;
        }}
        .channels-list {{
            list-style: none;
            padding: 8px 0;
        }}
        .channel-item {{
            padding: 12px 20px;
            cursor: pointer;
            transition: background 0.2s;
            font-size: 15px;
            font-weight: 500;
            color: #1e2a3a;
            border-right: 3px solid transparent;
        }}
        .channel-item:hover {{
            background: #f0f2f5;
        }}
        .channel-item.active {{
            background: #e3f2fd;
            border-right-color: #29b6f6;
            color: #126fa3;
        }}
        /* منطقه محتوای اصلی */
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            background: #eef2f7;
        }}
        .posts-container {{
            max-width: 800px;
            margin: 20px auto;
            padding: 0 16px 40px;
            width: 100%;
        }}
        /* کارت پست (شبیه خود تلگرام) */
        .tg-message {{
            background: white;
            border-radius: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
            transition: 0.2s;
            overflow: hidden;
        }}
        .tg-message:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        }}
        .msg-header {{
            display: flex;
            align-items: center;
            padding: 14px 18px 8px;
            gap: 12px;
        }}
        .avatar {{
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, #29b6f6, #0288d1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            color: white;
        }}
        .msg-meta {{
            flex: 1;
        }}
        .msg-channel {{
            font-weight: 700;
            font-size: 15px;
            color: #1e2a3a;
            display: block;
        }}
        .msg-date {{
            font-size: 11px;
            color: #8e9eae;
            margin-top: 2px;
        }}
        .msg-text {{
            padding: 5px 18px 8px 18px;
            font-size: 15px;
            line-height: 1.55;
            color: #1e2a3a;
            word-wrap: break-word;
            white-space: pre-wrap;
        }}
        .msg-media {{
            padding: 0 18px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 4px;
        }}
        .post-img {{
            flex: 1 1 200px;
            max-width: 100%;
        }}
        .post-img img {{
            width: 100%;
            max-height: 260px;
            object-fit: cover;
            border-radius: 18px;
            background: #f8f9fa;
            border: 1px solid #eef2f7;
        }}
        .no-img {{
            font-size: 12px;
            color: #9aaebf;
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 20px;
            text-align: center;
        }}
        .msg-actions {{
            padding: 10px 18px 18px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .btn {{
            background: #f0f4f9;
            border: none;
            padding: 6px 14px;
            border-radius: 40px;
            font-size: 13px;
            color: #126fa3;
            text-decoration: none;
            cursor: pointer;
            transition: 0.2s;
            font-family: inherit;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .btn:hover {{
            background: #e3eaf1;
        }}
        .no-posts {{
            text-align: center;
            padding: 40px;
            color: #8e9eae;
        }}
        .footer-note {{
            text-align: center;
            font-size: 12px;
            color: #9aaebf;
            margin: 20px 0;
        }}
        @media (max-width: 700px) {{
            .sidebar {{
                width: 80px;
            }}
            .sidebar-header {{
                text-align: center;
                padding: 20px 0;
                font-size: 0;
            }}
            .sidebar-header::before {{
                content: "☰";
                font-size: 28px;
            }}
            .channel-item {{
                text-align: center;
                font-size: 12px;
                padding: 12px 4px;
                word-break: keep-all;
            }}
            .channel-item span {{
                display: block;
                font-size: 20px;
                margin-bottom: 4px;
            }}
            .posts-container {{
                padding: 0 12px 40px;
            }}
        }}
    </style>
</head>
<body>
<div class="app">
    <div class="sidebar">
        <div class="sidebar-header">کانال‌ها</div>
        <ul class="channels-list">
            {sidebar_items}
        </ul>
    </div>
    <div class="main-content">
        <div class="posts-container" id="posts-container">
            {content_html}
        </div>
        <div class="footer-note">به‌روزرسانی خودکار هر ۲ ساعت • {len(CHANNELS)} کانال</div>
    </div>
</div>

<script>
    // مدیریت سایدبار: نمایش/مخفی کردن کانال‌ها
    const channelItems = document.querySelectorAll('.channel-item');
    const channelDivs = {{
        {', '.join([f"'{ch}': document.getElementById('channel-{ch}')" for ch in CHANNELS])}
    }};

    function showChannel(channel) {{
        // مخفی کردن همه
        Object.values(channelDivs).forEach(div => {{ if(div) div.style.display = 'none'; }});
        // نمایش کانال انتخاب شده
        if(channelDivs[channel]) channelDivs[channel].style.display = 'block';
        // تغییر کلاس active
        channelItems.forEach(item => {{
            if(item.getAttribute('data-channel') === channel)
                item.classList.add('active');
            else
                item.classList.remove('active');
        }});
    }}

    // رویداد کلیک روی آیتم‌های سایدبار
    channelItems.forEach(item => {{
        item.addEventListener('click', () => {{
            const channelName = item.getAttribute('data-channel');
            showChannel(channelName);
        }});
    }});

    // فعال کردن اولین کانال به طور پیش‌فرض
    if(channelItems.length) {{
        const firstChannel = channelItems[0].getAttribute('data-channel');
        showChannel(firstChannel);
    }}

    // دکمه کپی متن
    document.querySelectorAll('.copy-btn').forEach(btn => {{
        btn.addEventListener('click', function(e) {{
            const text = this.getAttribute('data-text');
            navigator.clipboard.writeText(text).then(() => {{
                const original = this.innerHTML;
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
    # حذف اطلاعات اضافی که قابل ذخیره نیست (مثل HTML)
    json_data = {ch: [{"text": p["plain_text"], "date": p["date"], "link": p["link"], "images": p["images"]} for p in posts] for ch, posts in all_data.items()}
    json.dump(json_data, f, ensure_ascii=False, indent=2)

print("✅ فایل HTML با سایدبار و تصاویر و تاریخ ذخیره شد.")
