import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

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
    """حذف کاراکترهای اضافه از متن پیام"""
    if not text:
        return ""
    return text.replace('\n', '<br>').strip()

async def fetch_posts():
    api_id, api_hash, string_session = get_env_vars()
    client = TelegramClient(StringSession(string_session), api_id, api_hash)

    all_data = {}
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("Error: Session is invalid. Please generate a new STRING_SESSION.")
            return

        for channel_username in CHANNELS:
            channel_username = channel_username.strip()
            print(f"Processing channel: @{channel_username}")
            posts = []
            try:
                entity = await client.get_entity(channel_username)
                async for message in client.iter_messages(entity, limit=MESSAGES_LIMIT):
                    if message and not message.deleted:
                        post_info = {
                            "id": message.id,
                            "date": message.date.strftime('%Y-%m-%d %H:%M:%S') if message.date else "No date",
                            "text": clean_text(message.raw_text),
                            "link": f"https://t.me/{channel_username}/{message.id}",
                            "media": bool(message.photo or message.video or message.document or message.audio),
                        }
                        posts.append(post_info)
                print(f"Successfully fetched {len(posts)} posts from @{channel_username}")
            except errors.rpcerrorlist.UsernameNotOccupiedError:
                print(f"Error: The username '@{channel_username}' does not exist.")
            except errors.rpcerrorlist.ChannelPrivateError:
                print(f"Error: Cannot access the private channel '@{channel_username}'.")
            except Exception as e:
                print(f"An unexpected error occurred for @{channel_username}: {e}")
            all_data[channel_username] = posts
    except Exception as e:
        print(f"A critical error occurred: {e}")
    finally:
        await client.disconnect()

    return all_data

async def generate_html(all_posts):
    """HTML با ظاهر مدرن و شبیه تلگرام می‌سازه"""
    html_content = """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Channel Posts Mirror</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: #eef2f7;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Tahoma, sans-serif;
                padding: 20px;
                direction: rtl;
            }
            .container { max-width: 800px; margin: 0 auto; }
            .card {
                background: #ffffff;
                border-radius: 16px;
                margin-bottom: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                transition: transform 0.2s, box-shadow 0.2s;
                overflow: hidden;
                border: 1px solid #e9ecef;
            }
            .card:hover { transform: translateY(-3px); box-shadow: 0 12px 24px rgba(0,0,0,0.12); }
            .card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 16px 20px;
                background: #f8fafc;
                border-bottom: 1px solid #eef2f6;
            }
            .channel-info span:first-child { font-weight: 800; color: #0b5e7e; background: #e3f2fd; padding: 4px 12px; border-radius: 40px; font-size: 0.85rem; }
            .card-date { font-size: 0.75rem; color: #6c88a0; }
            .card-body { padding: 20px; }
            .card-text { font-size: 0.95rem; line-height: 1.6; color: #1e2a3a; word-wrap: break-word; }
            .card-link { margin-top: 16px; text-align: left; }
            .card-link a {
                background: #e9ecef;
                padding: 6px 16px;
                border-radius: 30px;
                font-size: 0.8rem;
                color: #2c3e50;
                text-decoration: none;
                transition: background 0.2s;
                display: inline-block;
            }
            .card-link a:hover { background: #d4d9e1; }
            .footer { text-align: center; margin-top: 30px; font-size: 0.8rem; color: #7f8c8d; border-top: 1px solid #ddd; padding-top: 20px; }
            @media (max-width: 550px) { body { padding: 12px; } .card-header { padding: 12px 16px; } .card-body { padding: 16px; } }
        </style>
    </head>
    <body>
    <div class="container">
        <h2 style="text-align: center; margin-bottom: 25px; color: #2c3e50;">📡 آخرین پست‌های کانال‌ها</h2>
    """
    for channel, posts in all_posts.items():
        if not posts:
            html_content += f'<div class="card" style="background:#fff6e5;"><div class="card-header"><div class="channel-info"><span>⚠️ @{channel}</span></div></div><div class="card-body"><div class="card-text">هیچ پیامی برای این کانال یافت نشد.</div></div></div>'
            continue
        for post in posts:
            html_content += f"""
        <div class="card">
            <div class="card-header">
                <div class="channel-info"><span>📢 @{channel}</span></div>
                <div class="card-date">🕘 {post['date']}</div>
            </div>
            <div class="card-body">
                <div class="card-text">{post['text'] if post['text'] else '<i style="color:#aaa;">[این پیام شامل محتوای رسانه‌ای است]</i>'}</div>
                <div class="card-link"><a href="{post['link']}" target="_blank">🔗 مشاهده در تلگرام</a></div>
            </div>
        </div>"""
    html_content += """
        <div class="footer">🤖 به‌روزرسانی خودکار هر ۲ ساعت | Telegram Mirror Bot</div>
    </div>
    </body>
    </html>"""
    return html_content

async def save_output(all_posts):
    html_output = await generate_html(all_posts)
    with open('telegram-posts.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    # ذخیره دیتای خام برای استفاده‌های بعدی
    with open('posts_formatted.json', 'w', encoding='utf-8') as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)

async def main():
    print("🚀 Scraper started...")
    all_posts_data = await fetch_posts()
    if all_posts_data:
        await save_output(all_posts_data)
        print("✅ Successfully saved data and HTML output.")
    else:
        print("❌ Failed to fetch data. No output generated.")

if __name__ == '__main__':
    asyncio.run(main())
