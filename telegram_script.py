import requests
from bs4 import BeautifulSoup
import json
import re
from html import escape
from urllib.parse import urljoin
from datetime import datetime

CHANNELS = ['vpnbyamoo', 'sinavm']
LIMIT_PER_CHANNEL = 10

def clean_text(text):
    if not text: return ""
    text = re.sub(r'\[\*!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'[*_`~>#-]', '', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def parse_date(date_str):
    if not date_str or "نامشخص" in date_str: return None
    try:
        if 'T' in date_str:
            dt = date_str.split('+')[0].replace('T', ' ')
            return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        elif '/' in date_str:
            return datetime.strptime(date_str, '%Y/%m/%d %H:%M')
    except:
        return None
    return None

def extract_date(msg):
    time_tag = msg.find('time', class_='datetime')
    if time_tag and time_tag.get('datetime'):
        return time_tag['datetime'].replace('T', ' ').split('+')[0].replace('-', '/')
    date_link = msg.find('a', class_='tgme_widget_message_date')
    if date_link:
        span = date_link.find('span', class_='time')
        if span:
            raw = span.get_text(strip=True)
            return raw if ':' in raw else "تاریخ نامشخص"
    return "تاریخ نامشخص"

def extract_images(msg):
    images = []
    for a in msg.find_all('a', class_='tgme_widget_message_photo_wrap'):
        style = a.get('style', '')
        m = re.search(r'background-image:url\(\'([^\']+)\'\)', style)
        if m:
            img = m.group(1)
            if not img.startswith('http'): img = urljoin('https://t.me', img)
            images.append(img)
    if not images:
        for img in msg.find_all('img', class_='tgme_widget_message_photo'):
            src = img.get('src')
            if src: images.append(urljoin('https://t.me', src))
    return images

def fetch_channel(channel, limit):
    url = f"https://t.me/s/{channel}"
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message')
        print(f"✅ {channel}: {len(messages)} raw messages")
    except Exception as e:
        print(f"❌ {channel}: {e}")
        return []
    posts = []
    for msg in messages:
        text_div = msg.find('div', class_='tgme_widget_message_text')
        raw_text = text_div.get_text(strip=False) if text_div else ""
        clean_msg = clean_text(raw_text)
        date_str = extract_date(msg)
        link_tag = msg.find('a', class_='tgme_widget_message_date')
        link = link_tag['href'] if link_tag else f"https://t.me/{channel}"
        images = extract_images(msg)
        if not clean_msg and not images:
            continue
        posts.append({
            "text_html": escape(clean_msg).replace('\n', '<br>') if clean_msg else "",
            "date": date_str,
            "link": link,
            "plain_text": clean_msg,
            "images": images,
            "dt": parse_date(date_str)
        })
    posts.sort(key=lambda x: x['dt'] if x['dt'] else datetime.min, reverse=True)
    return posts[:limit]

all_data = {}
for ch in CHANNELS:
    all_data[ch] = fetch_channel(ch, LIMIT_PER_CHANNEL)

# ---------- تولید HTML (طراحی شبیه تلگرام) ----------
sidebar_items = ''.join([f'<div class="chat-item" data-channel="{ch}"><div class="avatar">📢</div><div class="chat-info"><div class="chat-name">@{ch}</div><div class="chat-last">{len(all_data[ch])} پیام</div></div></div>' for ch in CHANNELS])

channel_divs = {}
for ch, posts in all_data.items():
    if not posts:
        channel_divs[ch] = '<div class="no-posts">هیچ پستی یافت نشد</div>'
        continue
    posts_html = ''
    for p in posts:
        images_html = ''
        if p['images']:
            for img in p['images']:
                images_html += f'<div class="message-photo"><img src="{img}" loading="lazy"></div>'
        else:
            images_html = '<div class="no-photo">🖼️ بدون تصویر</div>'
        copy_txt = p['plain_text'].replace('\\', '\\\\').replace("'", "\\'").replace('"', '&quot;')
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
                    <button class="btn copy-btn" data-text="{copy_txt}">📋 کپی متن</button>
                </div>
            </div>
        </div>
        '''
    channel_divs[ch] = posts_html

content_switcher = ''.join([f'<div id="channel-{ch}" class="channel-messages" style="display: none;">{channel_divs[ch]}</div>' for ch in CHANNELS])

html_output = f"""<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>آرشیو کانال‌های تلگرام</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css" rel="stylesheet">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#0e1621; font-family:'Vazir',sans-serif; direction:rtl; height:100vh; overflow:hidden; }}
        .telegram-app {{ display:flex; height:100vh; width:100%; }}
        .sidebar {{ width:320px; background:#17212b; border-left:1px solid #2b3a4a; overflow-y:auto; }}
        .sidebar-header {{ padding:16px; background:#17212b; border-bottom:1px solid #2b3a4a; font-weight:600; font-size:20px; color:#fff; }}
        .chat-item {{ display:flex; align-items:center; padding:12px 16px; cursor:pointer; gap:12px; }}
        .chat-item:hover {{ background:#2b3a4a; }}
        .chat-item.active {{ background:#2c3e50; }}
        .chat-item .avatar {{ width:48px; height:48px; background:linear-gradient(135deg,#29b6f6,#0288d1); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:24px; color:#fff; }}
        .chat-info {{ flex:1; }}
        .chat-name {{ font-weight:600; color:#fff; font-size:16px; }}
        .chat-last {{ font-size:13px; color:#8e9eae; margin-top:4px; }}
        .main-content {{ flex:1; display:flex; flex-direction:column; background:#0e1621; overflow:hidden; }}
        .messages-area {{ flex:1; overflow-y:auto; padding:20px 16px; }}
        .channel-messages {{ max-width:800px; margin:0 auto; }}
        .message {{ display:flex; margin-bottom:24px; gap:12px; }}
        .message-avatar {{ width:42px; height:42px; background:#29b6f6; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:22px; flex-shrink:0; }}
        .message-bubble {{ background:#17212b; border-radius:18px; padding:12px 16px; max-width:calc(100% - 60px); box-shadow:0 1px 2px rgba(0,0,0,0.2); }}
        .bubble-header {{ display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px; }}
        .sender {{ font-weight:700; color:#29b6f6; }}
        .time {{ color:#8e9eae; font-size:11px; }}
        .bubble-text {{ color:#fff; font-size:15px; line-height:1.5; white-space:pre-wrap; }}
        .bubble-media {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:8px; }}
        .message-photo {{ flex:1 1 200px; max-width:100%; }}
        .message-photo img {{ width:100%; border-radius:16px; max-height:260px; object-fit:cover; border:1px solid #2b3a4a; }}
        .no-photo {{ color:#8e9eae; font-size:12px; background:#1f2c38; padding:8px 12px; border-radius:20px; text-align:center; }}
        .bubble-footer {{ margin-top:12px; display:flex; gap:8px; }}
        .btn {{ background:#2b3a4a; border:none; padding:6px 14px; border-radius:30px; font-size:12px; color:#8e9eae; cursor:pointer; text-decoration:none; transition:0.2s; display:inline-flex; align-items:center; gap:6px; }}
        .btn:hover {{ background:#3a4a5a; color:#fff; }}
        .no-posts {{ text-align:center; color:#8e9eae; padding:40px; }}
        .footer {{ text-align:center; font-size:12px; color:#5e6e7e; padding:12px; border-top:1px solid #2b3a4a; }}
        @media (max-width:700px) {{ .sidebar {{ width:80px; }} .chat-info {{ display:none; }} .chat-item {{ justify-content:center; padding:12px 0; }} }}
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
    const items = document.querySelectorAll('.chat-item');
    const divs = {{{','.join([f'"{ch}":document.getElementById("channel-{ch}")' for ch in CHANNELS])}}};
    function show(ch){{
        for(let id in divs) if(divs[id]) divs[id].style.display='none';
        if(divs[ch]) divs[ch].style.display='block';
        items.forEach(i=>{{
            if(i.getAttribute('data-channel')===ch) i.classList.add('active');
            else i.classList.remove('active');
        }});
    }}
    items.forEach(i=>i.addEventListener('click',()=>show(i.getAttribute('data-channel'))));
    if(items.length) show(items[0].getAttribute('data-channel'));
    document.querySelectorAll('.copy-btn').forEach(btn=>btn.addEventListener('click',function(e){{
        let t=this.getAttribute('data-text');
        navigator.clipboard.writeText(t).then(()=>{{
            let old=this.innerHTML; this.innerHTML='✅ کپی شد!';
            setTimeout(()=>this.innerHTML=old,1500);
        }}).catch(()=>alert('خطا'));
    }}));
</script>
</body>
</html>
"""

with open('telegram-posts.html', 'w', encoding='utf-8') as f:
    f.write(html_output)

with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump({ch: [{"text": p['plain_text'], "date": p['date'], "link": p['link'], "images": p['images']} for p in posts] for ch, posts in all_data.items()}, f, ensure_ascii=False, indent=2)

print("✅ فایل HTML با مرتب‌سازی جدیدترین پست‌ها و تصاویر تولید شد.")
