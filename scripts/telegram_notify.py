#!/usr/bin/env python3
"""
OffsecAR — مرسل التيليقرام
يرسل يومياً محتوى جاهز للنسخ واللصق على تويتر ولينكدإن وواتساب
مع صورة SVG ملخصة للخبر أو المقالة
"""

import os
import json
import requests
import glob
from pathlib import Path
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
POSTS_DIR  = Path("_posts")
BLOGS_DIR  = Path("_blogs")
IMAGES_DIR = Path("assets/images")
SITE_URL   = "https://malekalthubiany.github.io/OffsecAR"

def send_telegram_message(text: str):
    """يرسل رسالة نصية"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    })
    if not resp.ok:
        print(f"⚠️ خطأ: {resp.text}")
    return resp.ok

def send_telegram_image(image_path: Path, caption: str):
    """يرسل صورة مع نص"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as f:
        resp = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption[:1024],
            "parse_mode": "HTML",
        }, files={"photo": f})
    if not resp.ok:
        print(f"⚠️ خطأ في الصورة: {resp.text}")
    return resp.ok

def send_telegram_document(image_path: Path, caption: str = ""):
    """يرسل ملف SVG كـ document"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    with open(image_path, "rb") as f:
        resp = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption[:1024],
            "parse_mode": "HTML",
        }, files={"document": f})
    return resp.ok

def parse_front_matter(file_path: Path) -> dict:
    """يقرأ front matter من ملف Markdown"""
    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    fm["_body"] = parts[2].strip()
    return fm

def get_todays_files() -> tuple[list, list]:
    """يجيب ملفات اليوم من _posts و _blogs"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posts = sorted(POSTS_DIR.glob(f"{today}-*.md")) if POSTS_DIR.exists() else []
    blogs = sorted(BLOGS_DIR.glob(f"{today}-*.md")) if BLOGS_DIR.exists() else []
    return posts, blogs

def format_twitter_text(title: str, excerpt: str, url: str,
                         category: str, severity: str = "", cvss: str = "") -> str:
    """يصيغ نص التغريدة"""
    sev_emoji = {"حرجة": "🔴", "عالية": "🟠", "متوسطة": "🟡"}.get(severity, "🔵")
    lines = []
    if severity and severity not in ("", "None"):
        lines.append(f"{sev_emoji} {title}")
        if cvss and cvss not in ("", "None"):
            lines.append(f"CVSS: {cvss}")
    else:
        lines.append(f"📌 {title}")
    lines.append("")
    # اقتطع الملخص لـ 200 حرف
    short = excerpt[:200] + "..." if len(excerpt) > 200 else excerpt
    lines.append(short)
    lines.append("")
    lines.append(f"🔗 {url}")
    lines.append("")
    lines.append("#أمن_المعلومات #OffsecAR #RedTeam #Cybersecurity")
    return "\n".join(lines)

def format_linkedin_text(title: str, excerpt: str, url: str, category: str) -> str:
    """يصيغ نص لينكدإن"""
    return f"""📢 {title}

{excerpt[:400]}{"..." if len(excerpt) > 400 else ""}

التصنيف: {category}
🔗 اقرأ التحليل الكامل: {url}

---
OffsecAR — أخبار الأمن الهجومي بالعربي يومياً
#أمن_المعلومات #OffsecAR #CyberSecurity #RedTeam #OffensiveSecurity"""

def format_whatsapp_text(title: str, excerpt: str, url: str) -> str:
    """يصيغ نص واتساب"""
    return f"""*{title}*

{excerpt[:300]}{"..." if len(excerpt) > 300 else ""}

📎 {url}

_OffsecAR — يومية الأمن الهجومي بالعربي_"""

def send_divider(label: str):
    """يرسل فاصل بين المحتوى"""
    send_telegram_message(f"{'─' * 20}\n<b>{label}</b>\n{'─' * 20}")

def process_post(post_path: Path, index: int, total: int):
    """يعالج ويرسل خبر واحد"""
    fm = parse_front_matter(post_path)
    if not fm:
        return

    title    = fm.get("title", "")
    excerpt  = fm.get("_body", "")[:400]
    category = fm.get("category", "")
    severity = fm.get("severity", "")
    cvss     = fm.get("cvss", "")
    image    = fm.get("image", "")
    date_str = fm.get("date", "")[:10]

    # رابط الموقع
    slug = post_path.stem
    post_url = f"{SITE_URL}/{date_str.replace('-', '/')}/{slug}/"

    # ── رسالة الرأس ──
    send_telegram_message(
        f"📰 <b>خبر {index}/{total}</b>\n"
        f"<b>{title}</b>\n\n"
        f"📂 {category}"
        + (f" | ⚠️ خطورة {severity}" if severity and severity != "None" else "")
        + (f" | CVSS {cvss}" if cvss and cvss not in ("", "None") else "")
    )

    # ── الصورة ──
    if image:
        img_path = Path(image.lstrip("/").replace("OffsecAR/", ""))
        if img_path.exists():
            send_telegram_document(img_path, caption=title[:200])

    # ── نصوص النشر ──
    tw  = format_twitter_text(title, excerpt, post_url, category, severity, cvss)
    li  = format_linkedin_text(title, excerpt, post_url, category)
    wa  = format_whatsapp_text(title, excerpt, post_url)

    send_telegram_message(
        f"🐦 <b>Twitter / X</b>\n<code>{tw}</code>"
    )
    send_telegram_message(
        f"💼 <b>LinkedIn</b>\n<code>{li}</code>"
    )
    send_telegram_message(
        f"💬 <b>WhatsApp</b>\n<code>{wa}</code>"
    )

def process_blog(blog_path: Path, index: int, total: int):
    """يعالج ويرسل مقالة واحدة"""
    fm = parse_front_matter(blog_path)
    if not fm:
        return

    title    = fm.get("title", "")
    excerpt  = fm.get("excerpt", fm.get("_body", "")[:300])
    category = fm.get("category", "")
    read_time= fm.get("read_time", "")
    image    = fm.get("image", "")
    slug     = fm.get("slug", blog_path.stem)

    blog_url = f"{SITE_URL}/blogs/{slug}/"

    # ── رسالة الرأس ──
    send_telegram_message(
        f"📝 <b>مقالة {index}/{total}</b>\n"
        f"<b>{title}</b>\n\n"
        f"📂 {category}"
        + (f" | ⏱ {read_time} دقائق" if read_time else "")
    )

    # ── الصورة ──
    if image:
        img_path = Path(image.lstrip("/").replace("OffsecAR/", ""))
        if img_path.exists():
            send_telegram_document(img_path, caption=title[:200])

    # ── نصوص النشر ──
    tw = f"📌 {title}\n\n{excerpt[:200]}...\n\n🔗 {blog_url}\n\n#أمن_المعلومات #OffsecAR"
    li = format_linkedin_text(title, excerpt, blog_url, category)
    wa = format_whatsapp_text(title, excerpt, blog_url)

    send_telegram_message(f"🐦 <b>Twitter / X</b>\n<code>{tw}</code>")
    send_telegram_message(f"💼 <b>LinkedIn</b>\n<code>{li}</code>")
    send_telegram_message(f"💬 <b>WhatsApp</b>\n<code>{wa}</code>")


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posts, blogs = get_todays_files()

    if not posts and not blogs:
        send_telegram_message(f"⚠️ لا يوجد محتوى جديد اليوم ({today})")
        return

    # ── رسالة ترحيب ──
    send_telegram_message(
        f"🌅 <b>OffsecAR · يومية {today}</b>\n\n"
        f"📰 أخبار: {len(posts)}\n"
        f"📝 مقالات: {len(blogs)}\n\n"
        f"انسخ النصوص أدناه والصقها مباشرة 👇"
    )

    # ── الأخبار ──
    if posts:
        send_divider("📰 أخبار اليوم")
        for i, post in enumerate(posts, 1):
            process_post(post, i, len(posts))

    # ── المقالات ──
    if blogs:
        send_divider("📝 مقالات اليوم")
        for i, blog in enumerate(blogs, 1):
            process_blog(blog, i, len(blogs))

    send_telegram_message(f"✅ <b>انتهى محتوى اليوم</b>\n🔗 {SITE_URL}")
    print("✅ تم إرسال كل المحتوى للتيليقرام!")


if __name__ == "__main__":
    main()
