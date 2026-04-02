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
import re
from image_generator import create_news_image_svg

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
image: "/OffsecAR/assets/images/{image_path.name}"
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
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    image_path = create_news_image_svg(
        content.get("headline", ""),
        content.get("category", "ثغرة"),
        content.get("severity", "عالية"),
        str(content.get("cvss", "")),
        IMAGES_DIR,
        date_str
    )

    print("📝 إنشاء منشور Jekyll...")
    create_jekyll_post(content, "", image_path)

    print("\n✅ تم بنجاح!")


if __name__ == "__main__":
    main()
