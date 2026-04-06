#!/usr/bin/env python3
"""OffsecAR — تيليقرام: صورة + نص منشور كامل لكل منصة"""

import os, requests
from pathlib import Path
from datetime import datetime, timezone
from image_generator import make_advisory, make_twitter

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
POSTS_DIR  = Path("_posts")
BLOGS_DIR  = Path("_blogs")
SITE_URL   = "https://malekalthubiany.github.io/OffsecAR"
TMP        = Path("/tmp/offsec_imgs")
TMP.mkdir(exist_ok=True)


def tg(text: str):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text,
              "parse_mode": "HTML", "disable_web_page_preview": True}
    )

def tg_photo(img_path: Path, caption: str):
    if not img_path.exists():
        tg(caption); return
    with open(img_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024], "parse_mode": "HTML"},
            files={"photo": f}
        )

def tg_doc(img_path: Path, caption: str = ""):
    """يرسل الصورة كـ document (بجودة كاملة)"""
    if not img_path.exists(): return
    with open(img_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024], "parse_mode": "HTML"},
            files={"document": f}
        )

def parse_fm(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"): return {}
    parts = raw.split("---", 2)
    if len(parts) < 3: return {}
    fm = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"\'')
    fm["_body"] = parts[2].strip()
    return fm

def get_todays_files():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posts = sorted(POSTS_DIR.glob(f"{today}-*.md")) if POSTS_DIR.exists() else []
    blogs = sorted(BLOGS_DIR.glob(f"{today}-*.md")) if BLOGS_DIR.exists() else []
    return posts, blogs, today

def post_url(date_str, stem):
    slug = stem[11:] if len(stem) > 11 else stem
    y,m,d = date_str.split("-")
    return f"{SITE_URL}/{y}/{m}/{d}/{slug}/"

def blog_url(slug, filename_stem=""):
    """يبني رابط المقالة — Jekyll يستخدم slug من front matter مباشرة"""
    # Jekyll يستخدم الـ slug كـ permalink إن وُجد في front matter
    s = slug.strip() if slug else ""
    if not s and filename_stem:
        # fallback: أزل التاريخ من اسم الملف
        s = filename_stem[11:] if len(filename_stem) > 11 else filename_stem
    return f"{SITE_URL}/blogs/{s}/" if s else SITE_URL



def send_news(fm, date_str, stem, idx, total):
    title      = fm.get("title","")
    category   = fm.get("category","")
    severity   = fm.get("severity","")
    cvss       = fm.get("cvss","")
    cve        = fm.get("cve","")
    source_url = fm.get("source_url","")
    body       = fm.get("_body","")
    url        = post_url(date_str, stem)

    # ── توليد الصورة ──
    img = TMP / f"news_{idx}.png"
    actions = [
        'مراجعة الأنظمة المتأثرة فوراً',
        'تطبيق التحديثات الأمنية المتاحة',
        'مراقبة السجلات بحثاً عن نشاط مشبوه',
        'عزل الأنظمة حتى اكتمال التحديث',
    ]
    excerpt = body[:300].replace('\n','  ')
    try:
        make_advisory(
            title, category, severity, cvss, cve,
            excerpt, body,
            'آخر إصدار', 'تحديث فوري مطلوب',
            'تنفيذ أوامر عن بعد', 'وصول غير مصرح',
            'الشبكة', 'بدون مصادقة',
            date_str, f"REF: OFFSEC-{date_str.replace('-','')}", img
        )
    except Exception as e:
        print(f"   ⚠️ صورة: {e}")

    # ── رسالة الفصل ──
    tg(f"━━━━━━━━━━━━━━━━━━━━\n📰 <b>خبر {idx}/{total}</b>\n━━━━━━━━━━━━━━━━━━━━")

    # ── Twitter/X — المنشور الكامل ──
    sev_tag = f"🔴 خطورة {severity}" if severity and severity not in ("","None") else ""
    cvss_tag = f"CVSS {cvss}" if cvss and cvss not in ("","None") else ""
    tw_post = (
        f"{title}\n\n"
        + (f"{sev_tag}  {cvss_tag}\n\n" if sev_tag else "")
        + f"{body[:350]}...\n\n"
        + (f"المصدر: {source_url}\n" if source_url and source_url not in ("","None") else "")
        + f"اقرأ التحليل: {url}\n\n"

    )
    tg_doc(img, f"<b>🐦 Twitter / X</b>")
    tg(f"<b>🐦 نص التغريدة — انسخ والصق:</b>\n\n<code>{tw_post[:950]}</code>")

    # ── LinkedIn — المنشور الكامل ──
    li_post = (
        f"🔐 {title}\n\n"
        + (f"الخطورة: {severity}" + (f"  |  CVSS {cvss}" if cvss and cvss not in ("","None") else "") + "\n\n" if severity and severity not in ("","None") else "")
        + f"{body[:600]}\n\n"
        + "─────────────────\n"
        + (f"📎 المصدر الأصلي: {source_url}\n" if source_url and source_url not in ("","None") else "")
        + f"📖 التحليل الكامل: {url}\n\n"
        f"OffsecAR — الأمن الهجومي بالعربي يومياً\n"

    )
    tg(f"<b>💼 نص LinkedIn — انسخ والصق:</b>\n\n<code>{li_post[:1000]}</code>")

    # ── WhatsApp ──
    wa_post = (
        f"*{title}*\n\n"
        + (f"{sev_tag}" + (f"  |  {cvss_tag}" if cvss_tag else "") + "\n\n" if sev_tag else "")
        + body[:2000]
        + (f"\n\nالمصدر: {source_url}" if source_url and source_url not in ("","None") else "")
        + f"\n{url}"
        + "\n\nOffsecAR"
    )
    tg(f"<b>💬 نص WhatsApp — انسخ والصق:</b>\n\n<code>{wa_post[:800]}</code>")


def send_blog(fm, idx, total):
    title     = fm.get("title","")
    category  = fm.get("category","")
    read_time = fm.get("read_time","")
    body      = fm.get("_body","")
    excerpt   = fm.get("excerpt", body[:300])
    slug      = fm.get("slug","")
    url       = blog_url(slug)  # slug من front matter أدق

    # ── صورة ──
    img = TMP / f"blog_{idx}.png"
    actions = [
        'قراءة المقالة كاملة على موقع OffsecAR',
        'تطبيق التقنية في بيئة اختبار آمنة',
        'مشاركة المعرفة مع فريقك',
        'متابعتنا لمزيد من المحتوى اليومي',
    ]
    try:
        make_advisory(
            title, category, '', '', '',
            excerpt[:300], actions,
            'مقالة جديدة', 'متاحة الآن',
            category, 'محتوى متخصص',
            'موقع OffsecAR', 'مجاني',
            datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            f"REF: BLOG-{datetime.now(timezone.utc).strftime('%Y%m%d')}", img
        )
    except Exception as e:
        print(f"   ⚠️ صورة: {e}")

    tg(f"━━━━━━━━━━━━━━━━━━━━\n📝 <b>مقالة {idx}/{total}</b>\n━━━━━━━━━━━━━━━━━━━━")

    # Twitter
    tw_post = (
        f"📌 {title}\n\n"
        f"{excerpt[:250]}...\n\n"
        + (f"⏱ {read_time} دقائق قراءة\n\n" if read_time else "")
        + f"🔗 {url}\n\n"

    )
    tg_doc(img, f"<b>🐦 Twitter / X</b>")
    tg(f"<b>🐦 نص التغريدة:</b>\n\n<code>{tw_post[:900]}</code>")

    # LinkedIn
    li_post = (
        f"📢 {title}\n\n"
        f"{body[:700]}\n\n"
        + (f"⏱ وقت القراءة: {read_time} دقائق\n" if read_time else "")
        + f"📖 اقرأ المقالة كاملة: {url}\n\n"
        f"OffsecAR — الأمن الهجومي بالعربي\n"

    )
    tg(f"<b>💼 نص LinkedIn:</b>\n\n<code>{li_post[:1000]}</code>")

    wa_post = (
        f"*{title}*\n\n"
        + body[:2000]
        + f"\n\n{url}"
        + "\n\nOffsecAR"
    )
    tg(f"<b>💬 نص WhatsApp:</b>\n\n<code>{wa_post[:800]}</code>")


def main():
    posts, blogs, today = get_todays_files()

    if not posts and not blogs:
        tg(f"⚠️ لا يوجد محتوى جديد اليوم ({today})")
        return

    tg(
        f"🌅 <b>OffsecAR · {today}</b>\n\n"
        f"📰 أخبار: {len(posts)}  |  📝 مقالات: {len(blogs)}\n\n"
        f"كل عنصر يأتي مع:\n"
        f"• صورة تنبيه أمني جاهزة\n"
        f"• نص Twitter كامل\n"
        f"• نص LinkedIn كامل\n"
        f"• نص WhatsApp كامل"
    )

    for i, p in enumerate(posts, 1):
        fm = parse_fm(p)
        if fm: send_news(fm, today, p.stem, i, len(posts))

    for i, b in enumerate(blogs, 1):
        fm = parse_fm(b)
        if fm: send_blog(fm, i, len(blogs))

    tg(f"✅ <b>انتهى محتوى اليوم</b>\n🔗 {SITE_URL}")
    print("✅ تم!")

if __name__ == "__main__":
    main()
