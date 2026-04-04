#!/usr/bin/env python3
"""OffsecAR — تيليقرام: صورة + نص جاهز لكل منصة"""

import os, requests
from pathlib import Path
from datetime import datetime, timezone
from image_generator import make_twitter, make_linkedin, make_whatsapp

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
POSTS_DIR  = Path("_posts")
BLOGS_DIR  = Path("_blogs")
SITE_URL   = "https://malekalthubiany.github.io/OffsecAR"
TMP        = Path("/tmp/offsec_images")
TMP.mkdir(exist_ok=True)


def tg_text(text: str):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text,
              "parse_mode": "HTML", "disable_web_page_preview": True}
    )


def tg_photo(img_path: Path, caption: str):
    with open(img_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption,
                  "parse_mode": "HTML"},
            files={"photo": f}
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


def site_url_post(date_str, stem):
    slug = stem[11:] if len(stem) > 11 else stem
    y, m, d = date_str.split("-")
    return f"{SITE_URL}/{y}/{m}/{d}/{slug}/"


def site_url_blog(slug):
    return f"{SITE_URL}/blogs/{slug}/"


def clean(text, limit=280):
    return text[:limit] + ("..." if len(text) > limit else "")


def send_three(title, category, severity, cvss, excerpt, url, source_url=""):
    date_str = datetime.now(timezone.utc).strftime("%d %b %Y")

    # ── تويتر ──
    img_tw = TMP / "tw.png"
    make_twitter(title, category, severity, cvss, excerpt, date_str, img_tw)
    sev_line = ""
    if severity and severity not in ("", "None"):
        sev_line = f"خطورة {severity}"
        if cvss and cvss not in ("", "None"):
            sev_line += f" · CVSS {cvss}"
    tw_text = (
        f"{title}\n\n"
        + (f"{sev_line}\n\n" if sev_line else "")
        + f"{clean(excerpt, 200)}\n\n"
        + (f"المصدر: {source_url}\n" if source_url and source_url not in ("","None") else "")
        + f"{url}\n\n"
        f"#أمن_المعلومات #OffsecAR #RedTeam"
    )
    tg_photo(img_tw, f"<b>Twitter / X</b>\n\n<code>{tw_text[:900]}</code>")

    # ── لينكدإن ──
    img_li = TMP / "li.png"
    make_linkedin(title, category, excerpt, date_str, img_li)
    li_text = (
        f"{title}\n\n"
        f"{clean(excerpt, 400)}\n\n"
        + (f"المصدر الأصلي: {source_url}\n" if source_url and source_url not in ("","None") else "")
        + f"التحليل الكامل: {url}\n\n"
        f"OffsecAR — الأمن الهجومي بالعربي\n"
        f"#أمن_المعلومات #OffsecAR #CyberSecurity #RedTeam"
    )
    tg_photo(img_li, f"<b>LinkedIn</b>\n\n<code>{li_text[:1000]}</code>")

    # ── واتساب ──
    img_wa = TMP / "wa.png"
    make_whatsapp(title, category, excerpt, date_str, img_wa)
    wa_text = (
        f"*{title}*\n\n"
        f"{clean(excerpt, 300)}\n\n"
        + (f"المصدر: {source_url}\n" if source_url and source_url not in ("","None") else "")
        + f"{url}\n\n"
        f"_OffsecAR_"
    )
    tg_photo(img_wa, f"<b>WhatsApp</b>\n\n<code>{wa_text[:800]}</code>")


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posts = sorted(POSTS_DIR.glob(f"{today}-*.md")) if POSTS_DIR.exists() else []
    blogs = sorted(BLOGS_DIR.glob(f"{today}-*.md")) if BLOGS_DIR.exists() else []

    if not posts and not blogs:
        tg_text(f"لا يوجد محتوى جديد اليوم ({today})")
        return

    tg_text(f"<b>OffsecAR · {today}</b>\n\nأخبار: {len(posts)}  |  مقالات: {len(blogs)}")

    for p in posts:
        fm = parse_fm(p)
        if not fm: continue
        title    = fm.get("title","")
        category = fm.get("category","")
        severity = fm.get("severity","")
        cvss     = fm.get("cvss","")
        source_url = fm.get("source_url","")
        body     = fm.get("_body","")
        excerpt  = body[:350]
        url      = site_url_post(today, p.stem)
        tg_text(f"── خبر ──")
        send_three(title, category, severity, cvss, excerpt, url, source_url)

    for b in blogs:
        fm = parse_fm(b)
        if not fm: continue
        title    = fm.get("title","")
        category = fm.get("category","")
        excerpt  = fm.get("excerpt", fm.get("_body","")[:350])
        slug     = fm.get("slug", b.stem)
        url      = site_url_blog(slug)
        tg_text(f"── مقالة ──")
        send_three(title, category, "", "", excerpt, url)

    tg_text(f"تم ✓")
    print("✅ تم!")


if __name__ == "__main__":
    main()
