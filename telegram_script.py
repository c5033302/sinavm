import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# ========== تنظیمات (فقط همین قسمت رو تغییر بدید) ==========
CHANNELS = ['vpnbyamoo', 'sinavm']   # اسم کانال‌ها، مثل ['channel1', 'channel2']
MESSAGES_LIMIT = 15                  # تعداد پیام برای هر کانال
# =======================================================

def get_env_vars():
    """دریافت و بررسی متغیرهای محیطی"""
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    string_session = os.getenv('STRING_SESSION')
    if not api_id or not api_hash or not string_session:
        raise ValueError("Missing API_ID, API_HASH, or STRING_SESSION in environment variables!")
    return int(api_id), api_hash, string_session

def clean_text(text):
    """حذف کاراکترهای اضافه از متن پیام و تبدیل به HTML"""
    if not text:
        return ""
    # جایگزینی newline با <br> برای HTML
    return text.replace('\n', '<br>').strip()

def get_media_info(message):
    """اطلاعات رسانه (در صورت وجود) را برمی‌گرداند"""
    if message.photo:
        return "🖼️ عکس"
    elif message.video:
        return "🎥 ویدیو"
    elif message.document:
        # می‌توان نوع فایل را بررسی کرد
        mime = message.document.mime_type
        if "image" in mime:
            return "🖼️ تصویر"
        elif "video" in mime:
            return "🎥 ویدیو"
        else:
            return "📎 فایل"
    elif message.audio:
        return "🎵 صدا"
    elif message.voice:
        return "🎤 پیام صوتی"
    return None

async def fetch_posts():
    api_id, api_hash, string_session = get_env_vars()
    client = TelegramClient(StringSession(string_session), api_id, api_hash)

    all_data = {}
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("Error: Session is invalid. Please generate a new STRING_SESSION.")
            return all_data

        for channel_username in CHANNELS:
            channel_username = channel_username.strip()
            print(f"Processing channel: @{channel_username}")
            posts = []
            try:
                entity = await client.get_entity(channel_username)
                async for message in client.iter_messages(entity, limit=MESSAGES_LIMIT):
                    if message and not message.deleted:
                        # استخراج تاریخ و زمان
                        msg_date = message.date.strftime('%Y-%m-%d %H:%M:%S') if message.date else "No date"
                        # متن
                        msg_text = clean_text(message.raw_text)
                        # رسانه
                        media_type = get_media_info(message)
                        # لینک مستقیم به پیام
                        link = f"https://t.me/{channel_username}/{message.id}"
                        post_info = {
                            "id": message.id,
                            "date": msg_date,
                            "text": msg_text,
                            "link": link,
                            "media": media_type,
                            "has_media": media_type is not None
                        }
                        posts.append(post_info)
                print(f"✅ Successfully fetched {len(posts)} posts from @{channel_username}")
            except errors.rpcerrorlist.UsernameNotOccupiedError:
                print(f"❌ Error: The username '@{channel_username}' does not exist.")
            except errors.rpcerrorlist.ChannelPrivateError:
                print(f"❌ Error: Cannot access the private channel '@{channel_username}'.")
            except Exception as e:
                print(f"❌ An unexpected error occurred for @{channel_username}: {e}")
            all_data[channel_username] = posts
    except Exception as e:
        print(f"❌ A critical error occurred: {e}")
    finally:
        await client.disconnect()
    return all_data

async def generate_html(all_posts):
    """HTML با ظاهر شبیه تلگرام (سایدبار، حباب، رسانه)"""
    # ساخت سایدبار (لیست کانال‌ها)
    sidebar_items = ""
    for ch in all_posts.keys():
        post_count = len(all_posts.get(ch, []))
        sidebar_items += f'''
        <div class="chat-item" data-channel="{ch}">
            <div class="avatar">📢</div>
            <div class="chat-info">
                <div class="chat-name">@{ch}</div>
                <div class="chat-last">{post_count} پیام</div>
            </div>
        </div>
        '''

    # ساخت بخش پیام‌ها برای هر کانال (مخفی به جز اولین)
    channel_messages = {}
    first_channel = list(all_posts.keys())[0] if all_posts else None
    for ch, posts in all_posts.items():
        posts_html = ""
        if not posts:
            posts_html = '<div class="no-posts">هیچ پیامی یافت نشد</div>'
        else:
            for p in posts:
                # نمایش متن یا پیام رسانه‌ای
                if p['text']:
                    text_html = p['text']
                elif p['has_media']:
                    text_html = f'<span class="media-placeholder">{p["media"]}</span>'
                else:
                    text_html = "<i>پیام خالی</i>"
                # دکمه کپی متن (فقط اگر متن دارد)
                copy_btn = f'<button class="btn copy-btn" data-text="{p["text"].replace(chr(34), "&quot;")}">📋 کپی متن</button>' if p['text'] else ''
                posts_html += f'''
                <div class="message">
                    <div class="message-avatar">📢</div>
                    <div class="message-bubble">
                        <div class="bubble-header">
                            <span class="sender">@{ch}</span>
                            <span class="time">{p["date"]}</span>
                        </div>
                        <div class="bubble-text">{text_html}</div>
                        <div class="bubble-footer">
                            <a href="{p["link"]}" class="btn" target="_blank">🔗 مشاهده در تلگرام</a>
                            {copy_btn}
                        </div>
                    </div>
                </div>
                '''
        channel_messages[ch] = f'<div id="channel-{ch}" class="channel-messages" style="display: {"block" if ch == first_channel else "none"};">{posts_html}</div>'

    content_switcher = ''.join(channel_messages.values())

    html_code = f"""<!DOCTYPE html>
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
        /* سایدبار */
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
        /* حباب پیام */
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
        .media-placeholder {{
            background: #2b3a4a;
            padding: 8px 12px;
            border-radius: 16px;
            display: inline-block;
            font-size: 13px;
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
        <div class="chat-list" id="chat-list">
            {sidebar_items}
        </div>
    </div>
    <div class="main-content">
        <div class="messages-area" id="messages-area">
            {content_switcher}
        </div>
        <div class="footer">به‌روزرسانی خودکار هر ۲ ساعت • {len(all_posts)} کانال</div>
    </div>
</div>
<script>
    // مدیریت سایدبار و تغییر کانال
    const chatItems = document.querySelectorAll('.chat-item');
    const channelDivs = {{
        {', '.join([f"'{ch}': document.getElementById('channel-{ch}')" for ch in all_posts.keys()])}
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
</html>"""
    return html_code

async def save_output(all_posts):
    html_output = await generate_html(all_posts)
    with open('telegram-posts.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    # ذخیره دیتای خام برای استفاده‌های بعدی
    with open('posts_formatted.json', 'w', encoding='utf-8') as f:
        # تبدیل داده‌ها به JSON قابل ذخیره (حذف توابع)
        json_data = {ch: posts for ch, posts in all_posts.items()}
        json.dump(json_data, f, ensure_ascii=False, indent=2)

async def main():
    print("🚀 Scraper started...")
    all_posts_data = await fetch_posts()
    if all_posts_data and any(all_posts_data.values()):
        await save_output(all_posts_data)
        print("✅ Successfully saved data and HTML output.")
    else:
        print("❌ Failed to fetch data or no posts found. No output generated.")

if __name__ == '__main__':
    asyncio.run(main())
