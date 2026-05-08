import html
import json
from telegram_channel_viewer import channel
from datetime import datetime
import re

# ---------- تنظیمات ----------
channel_username = 'sinavm'   # نام کاربری کانال (بدون @)
posts_limit = 5                # تعداد پست‌های مورد نیاز
# ---------------------------

def clean_text(text):
    """حذف مارک‌داون و لینک‌های اضافی از متن"""
    if not text:
        return ""
    # حذف لینک‌های تصاویر [*![](...)](...)
    text = re.sub(r'\[\*!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    # حذف مارک‌داون ساده
    text = re.sub(r'[#*`~>]', '', text)
    # جایگزینی لاین‌بریک با <br>
    text = text.replace('\n', '<br>')
    return text.strip()

try:
    # دریافت اطلاعات کانال
    ch = channel(channel_username)
    # دریافت لیست پست‌ها (تعداد دلخواه)
    all_posts = ch.messages[:posts_limit]   # جدیدترین پست‌ها ابتدا قرار دارند
    print(f"✅ {len(all_posts)} posts fetched successfully.")
except Exception as e:
    print(f"❌ Error fetching posts: {e}")
    all_posts = []

# ---------- ساخت HTML با استایل کارت‌های زیبا ----------
html_output = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>آخرین پست‌های کانال @{channel_username}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: #eef2f7;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
            direction: rtl;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .card {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            padding: 16px 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }}
        .card-header {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            border-bottom: 1px solid #e9ecef;
            padding-bottom: 8px;
        }}
        .channel-icon {{
            width: 40px;
            height: 40px;
            background: #29b6f6;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 18px;
            margin-left: 12px;
        }}
        .channel-name {{
            font-weight: bold;
            font-size: 16px;
            color: #1e2a3a;
            text-decoration: none;
        }}
        .channel-name:hover {{
            text-decoration: underline;
        }}
        .date {{
            font-size: 12px;
            color: #6c757d;
            margin-right: auto;
        }}
        .message-text {{
            font-size: 15px;
            line-height: 1.6;
            color: #2c3e50;
            margin: 12px 0;
            word-wrap: break-word;
        }}
        .message-link {{
            display: inline-block;
            margin-top: 8px;
            font-size: 13px;
            color: #29b6f6;
            text-decoration: none;
            background: #e3f2fd;
            padding: 6px 12px;
            border-radius: 20px;
            transition: background 0.2s;
        }}
        .message-link:hover {{
            background: #bbdefb;
            text-decoration: none;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            font-size: 12px;
            color: #6c757d;
        }}
    </style>
</head>
<body>
<div class="container">
    <h2 style="text-align: center; margin-bottom: 24px;">📱 آخرین پست‌های کانال @{channel_username}</h2>
"""

json_data = []

for idx, post in enumerate(all_posts, 1):
    if not post.text or not post.text.strip():
        continue
        
    # متن تمیز شده
    clean_msg = clean_text(post.text)
    # اگر بعد از پاکسازی چیزی نماند، رد کن
    if not clean_msg:
        continue
        
    # تاریخ به صورت شمسی یا میلادی (میلادی از قبل موجود است)
    date_obj = post.date
    if date_obj:
        # تبدیل به زمان محلی (اختیاری)
        date_str = date_obj.strftime('%Y/%m/%d - %H:%M')
    else:
        date_str = "تاریخ نامشخص"
        
    # لینک مستقیم به پست
    post_link = f"https://t.me/{channel_username}/{post.id}"
    
    # ساخت کارت HTML
    html_output += f"""
    <div class="card">
        <div class="card-header">
            <div class="channel-icon">📢</div>
            <a href="https://t.me/{channel_username}" class="channel-name" target="_blank">@{channel_username}</a>
            <div class="date">{html.escape(date_str)}</div>
        </div>
        <div class="message-text">
            {clean_msg}
        </div>
        <a href="{post_link}" class="message-link" target="_blank">🔗 مشاهده پست در تلگرام</a>
    </div>
    """
    
    # ذخیره در JSON برای استفاده احتمالی
    json_data.append({
        "text": post.text,
        "clean_text": clean_msg,
        "date": date_obj.timestamp() if date_obj else 0,
        "date_str": date_str,
        "link": post_link,
        "channel": channel_username
    })

if not json_data:
    html_output += '<div class="card" style="text-align: center;">هیچ پست متنی یافت نشد.</div>\n'

html_output += """
    <div class="footer">
        تولید شده توسط GitHub Actions • به‌روزرسانی خودکار هر ۲ ساعت
    </div>
</div>
</body>
</html>
"""

# ---------- ذخیره فایل‌ها ----------
with open('telegram-posts.html', 'w', encoding='utf-8') as f:
    f.write(html_output)
print("✅ telegram-posts.html با استایل جدید ذخیره شد.")

with open('posts_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)
print("✅ posts_formatted.json ذخیره شد.")

print("اسکریپت با موفقیت به پایان رسید.")
