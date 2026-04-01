#!/usr/bin/env python3
"""
OffsecAR
النظام الرئيسي: يجمع الأخبار، يكتبها بالعربي، يصمم صورة، ينشر على تويتر، ويحدث الموقع
"""

import os
import json
import requests
import anthropic
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re

# ─── إعدادات ───────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]

POSTS_DIR  = Path("_posts")
IMAGES_DIR = Path("assets/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
POSTS_DIR.mkdir(parents=True, exist_ok=True)

# مصادر أخبار الأمن الهجومي
RSS_FEEDS = [
    "https://www.exploit-db.com/rss.xml",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json",
    "https://seclists.org/rss/fulldisclosure.rss",
    "https://portswigger.net/daily-swig/rss",
    "https://www.darkreading.com/rss.xml",
]

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ─── 1. جمع الأخبار ────────────────────────────────────────────────────────
def fetch_latest_news() -> list[dict]:
    """يجمع أحدث أخبار الأمن الهجومي من مصادر متعددة"""
    items = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                items.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", ""))[:600],
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": feed.feed.get("title", url),
                })
        except Exception as e:
            print(f"⚠️ فشل تحميل: {url} — {e}")
    return items[:15]


# ─── 2. توليد المحتوى العربي (Claude) ─────────────────────────────────────
def generate_arabic_content(news_items: list[dict]) -> dict:
    """يختار الخبر الأبرز ويكتبه بأسلوب ثمانية العربي"""
    news_json = json.dumps(news_items, ensure_ascii=False, indent=2)

    prompt = f"""أنت محرر أمن معلومات في مجلة تقنية عربية راقية تكتب بأسلوب شركة ثمانية:
- لغة عربية فصحى واضحة ومشوقة
- جمل قصيرة، حيوية، تجذب القارئ
- لا تترجم المصطلحات التقنية (CVE, exploit, buffer overflow, RCE, etc.) — أبقها إنجليزية
- الأسلوب: ذكي، محايد، تحليلي

من هذه الأخبار اختر الأبرز في مجال الأمن الهجومي (exploits، ثغرات حرجة، أدوات red team، تقنيات هجوم):

{news_json}

أرجع JSON فقط بهذه الحقول:
{{
  "headline": "العنوان الرئيسي (15-20 كلمة)",
  "category": "تصنيف واحد بالعربي: ثغرة حرجة | أداة اختبار | تقنية هجوم | تهديد متقدم | تحليل",
  "severity": "حرجة | عالية | متوسطة",
  "cvss": "الرقم أو null",
  "cve_id": "CVE-XXXX-XXXX أو null",
  "summary_short": "ملخص تويتر: 3-4 جمل قوية (للصورة)",
  "summary_long": "ملخص موقع: 5-7 جمل تحليلية مفصلة",
  "hashtags": ["#أمن_المعلومات", "#ثغرات", "إلخ — 5 هاشتاقات"],
  "tweet_text": "نص التغريدة المرافقة للصورة (280 حرف max بالعربي + الهاشتاقات)",
  "source_url": "رابط المصدر الأصلي",
  "source_name": "اسم المصدر بالإنجليزية"
}}"""

    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    # تنظيف markdown إن وجد
    raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


# ─── 3. تصميم الصورة ───────────────────────────────────────────────────────
def create_post_image(content: dict) -> Path:
    """يصمم صورة 1080×1080 بأسلوب ثمانية الداكن للنشر على تويتر"""

    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), color="#0d0d0d")
    draw = ImageDraw.Draw(img)

    # ألوان
    C_RED    = "#e03c2a"
    C_WHITE  = "#f5f5f5"
    C_MUTED  = "#888888"
    C_DARK2  = "#181818"
    C_BORDER = "#2a2a2a"

    # خلفية طبقات
    draw.rectangle([0, 0, W, H], fill="#0d0d0d")
    draw.rectangle([0, 0, W, 6], fill=C_RED)   # شريط علوي أحمر

    # تدرج خلفية ركن أيسر سفلي (بسيط)
    for i in range(300):
        alpha = int(30 * (1 - i / 300))
        draw.ellipse(
            [W - 400 + i // 2, H - 400 + i // 2, W + 50, H + 50],
            fill=f"#1a0a08",
        )

    # ── تحميل الخطوط ──────────────────────────────────────────────────
    def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
        # محاولة تحميل Noto Sans Arabic
        paths = [
            f"/usr/share/fonts/truetype/noto/NotoSansArabic-{'Bold' if bold else 'Regular'}.ttf",
            f"/usr/share/fonts/opentype/noto/NotoSansArabic-{'Bold' if bold else 'Regular'}.otf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for p in paths:
            if Path(p).exists():
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    font_tag      = load_font(22)
    font_category = load_font(26)
    font_headline = load_font(54, bold=True)
    font_body     = load_font(32)
    font_small    = load_font(22)
    font_handle   = load_font(24)

    # ── التاريخ والتاق ────────────────────────────────────────────────
    today = datetime.now(timezone.utc).strftime("%d %B %Y")
    draw.text((W - 60, 36), today, font=font_tag, fill=C_MUTED, anchor="ra")

    # بطاقة التاق الأحمر
    tag_text = "OffsecAR"
    draw.rounded_rectangle([54, 24, 54 + 260, 24 + 38], radius=6, fill="#1a0804", outline=C_RED, width=1)
    draw.text((184, 43), tag_text, font=font_tag, fill=C_RED, anchor="mm")

    # ── التصنيف ───────────────────────────────────────────────────────
    category = content.get("category", "ثغرة")
    draw.text((W - 60, 110), category, font=font_category, fill=C_MUTED, anchor="ra")

    # CVE إن وجد
    cve = content.get("cve_id")
    if cve:
        draw.text((60, 110), cve, font=font_category, fill=C_RED)

    # ── الخط الفاصل ───────────────────────────────────────────────────
    draw.rectangle([54, 160, W - 54, 162], fill=C_BORDER)

    # ── العنوان الرئيسي ───────────────────────────────────────────────
    headline = content.get("headline", "عنوان الخبر")

    def wrap_arabic(text: str, font, max_width: int) -> list[str]:
        words = text.split()
        lines, line = [], []
        for word in words:
            test = " ".join(line + [word])
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                line.append(word)
            else:
                if line:
                    lines.append(" ".join(line))
                line = [word]
        if line:
            lines.append(" ".join(line))
        return lines

    headline_lines = wrap_arabic(headline, font_headline, W - 140)
    y = 200
    for line in headline_lines[:3]:
        draw.text((W - 70, y), line, font=font_headline, fill=C_WHITE, anchor="ra")
        y += 68

    # ── الخط الأحمر تحت العنوان ───────────────────────────────────────
    draw.rectangle([54, y + 12, 54 + 60, y + 16], fill=C_RED)
    y += 48

    # ── الملخص ────────────────────────────────────────────────────────
    summary = content.get("summary_short", "")
    summary_lines = wrap_arabic(summary, font_body, W - 140)
    for line in summary_lines[:4]:
        draw.text((W - 70, y), line, font=font_body, fill="#cccccc", anchor="ra")
        y += 46

    # ── درجة الخطورة ──────────────────────────────────────────────────
    severity = content.get("severity", "عالية")
    cvss     = content.get("cvss")
    sev_colors = {"حرجة": "#e03c2a", "عالية": "#e8884e", "متوسطة": "#e8c44e"}
    sev_col = sev_colors.get(severity, "#e8884e")

    sev_y = H - 160
    draw.rounded_rectangle([54, sev_y, 54 + 220, sev_y + 44], radius=8, fill="#1a1a1a", outline=sev_col, width=1)
    dot_x = 80
    draw.ellipse([dot_x, sev_y + 15, dot_x + 14, sev_y + 29], fill=sev_col)
    sev_text = f"خطورة {severity}" + (f"  ·  CVSS {cvss}" if cvss else "")
    draw.text((dot_x + 24, sev_y + 22), sev_text, font=font_small, fill=sev_col, anchor="la")

    # ── الفاصل السفلي ─────────────────────────────────────────────────
    draw.rectangle([54, H - 96, W - 54, H - 94], fill=C_BORDER)

    # ── اسم الحساب ────────────────────────────────────────────────────
    draw.text((60, H - 72), "@OffsecARE", font=font_handle, fill=C_MUTED)
    draw.text((W - 60, H - 72), "offsec-ar.github.io", font=font_handle, fill=C_MUTED, anchor="ra")

    # ── حفظ ───────────────────────────────────────────────────────────
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = IMAGES_DIR / f"{date_str}-post.png"
    img.save(out_path, "PNG", quality=95)
    print(f"✅ الصورة: {out_path}")
    return out_path




# ─── 5. إنشاء منشور Jekyll ─────────────────────────────────────────────────
def create_jekyll_post(content: dict, tweet_url: str, image_path: Path) -> Path:
    """ينشئ ملف Markdown لـ Jekyll"""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    time_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slug = f"offensec-{date_str}"
    post_file = POSTS_DIR / f"{date_str}-{slug}.md"

    severity = content.get("severity", "عالية")
    sev_en = {"حرجة": "critical", "عالية": "high", "متوسطة": "medium"}.get(severity, "high")
    hashtags_str = " ".join(content.get("hashtags", []))
    cve = content.get("cve_id", "")

    front_matter = f"""---
layout: post
title: "{content.get('headline', '').replace('"', "'")}"
date: {time_str}
category: "{content.get('category', 'ثغرة')}"
severity: "{severity}"
severity_en: "{sev_en}"
cve: "{cve}"
cvss: "{content.get('cvss', '')}"
source: "{content.get('source_name', '')}"
source_url: "{content.get('source_url', '')}"
tweet_url: "{tweet_url}"
image: "/assets/images/{image_path.name}"
hashtags: "{hashtags_str}"
---

{content.get('summary_long', '')}

---

**المصدر:** [{content.get('source_name', 'المصدر')}]({content.get('source_url', '#')})
"""

    post_file.write_text(front_matter, encoding="utf-8")
    print(f"✅ المنشور: {post_file}")
    return post_file


# ─── رئيسي ─────────────────────────────────────────────────────────────────
def main():
    print("🔍 جمع الأخبار...")
    news = fetch_latest_news()
    if not news:
        print("❌ لا توجد أخبار")
        return

    print("✍️ توليد المحتوى العربي...")
    content = generate_arabic_content(news)
    print(f"   العنوان: {content.get('headline')}")

    print("🎨 تصميم الصورة...")
    image_path = create_post_image(content)

    print("📝 إنشاء منشور Jekyll...")
    create_jekyll_post(content, "", image_path)

    print("\n✅ تم بنجاح!")


if __name__ == "__main__":
    main()
