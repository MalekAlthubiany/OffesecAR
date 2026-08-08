#!/usr/bin/env python3
"""
OffsecAR — نشر ذكي
ينشر فقط عندما يوجد خبر يستحق انتباه الناس فعلاً
"""

import os, json, re, feedparser
import anthropic
from datetime import datetime, timezone
from pathlib import Path

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
POSTS_DIR  = Path("_posts")
IMAGES_DIR = Path("assets/images")
POSTS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

NEWS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://portswigger.net/daily-swig/rss",
    "https://www.darkreading.com/rss.xml",
    "https://www.exploit-db.com/rss.xml",
    "https://seclists.org/rss/fulldisclosure.rss",
    "https://feeds.reuters.com/reuters/technologyNews",
]


def fetch_news() -> list[dict]:
    items = []
    for url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                items.append({
                    "title":   entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", ""))[:600],
                    "link":    entry.get("link", ""),
                    "source":  feed.feed.get("title", ""),
                })
        except Exception as e:
            print(f"   ⚠️ {url}: {e}")
    return items


def evaluate_and_write(news_items: list[dict]) -> dict | None:
    news_json = json.dumps(news_items[:20], ensure_ascii=False, indent=2)

    prompt = f"""أنت محرر متخصص في الأمن السيبراني لمجتمع OffsecAR العربي.

راجع هذه الأخبار واسأل نفسك: هل هناك خبر سيجعل الناس يتوقفون ويقرأون؟

الأخبار التي تستحق النشر الفوري:

١. هجمات تؤثر على حياة الناس — بنوك، كهرباء، مستشفيات، حكومات، موانئ
٢. ثغرة في منتج يستخدمه الملايين — Windows، iOS، أندرويد، روترات منزلية، كاميرات
٣. الذكاء الاصطناعي في الهجوم — أداة AI جديدة تُستخدم للاختراق، deepfake هجومي
٤. اختراق ضخم — سرقة بيانات ملايين أشخاص، تسريب بيانات حكومية أو مالية
٥. حرب سيبرانية — دولة تهاجم دولة، اضطراب اقتصادي بسبب هجوم
٦. ثغرة zero-day مستغلة الآن في أجهزة شائعة

الأخبار التي لا تستحق:
- ثغرة في نظام غير شائع أو أداة متخصصة
- تحديث روتيني
- تقرير بحثي بدون تأثير فوري
- أداة pentest عادية

الأخبار المتاحة:
{news_json}

إذا وجدت خبراً يستحق النشر (درجة 8 أو أكثر من 10):
اكتب المقالة الكاملة بالعربي — احترافية، واضحة، تشرح التأثير الحقيقي على الناس والشركات.

أرجع JSON فقط:
{{
  "should_publish": true/false,
  "reason": "لماذا يستحق أو لا يستحق",
  "importance_score": 1-10,
  "title": "عنوان جذاب بالعربي يصف التأثير الحقيقي",
  "category": "هجوم على بنية تحتية / ثغرة حرجة / ذكاء اصطناعي هجومي / تسريب بيانات / حرب سيبرانية",
  "severity": "حرجة / عالية / متوسطة",
  "cvss": "رقم أو فارغ",
  "cve": "CVE أو فارغ",
  "body": "المقالة الكاملة — 500 إلى 900 كلمة عربية، تشرح: ما حدث، كيف حدث، من يتأثر، ماذا يعني للناس، التوصيات",
  "source_url": "رابط المصدر",
  "impact": "التأثير الاقتصادي أو الاجتماعي المتوقع"
}}"""

    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = re.sub(r"^```json\s*|```$", "", resp.content[0].text.strip(), flags=re.MULTILINE).strip()
    data = json.loads(raw)

    if not data.get("should_publish"):
        print(f"   ⏭ تخطي: {data.get('reason')}")
        return None

    score = int(data.get("importance_score", 0))
    if score < 8:
        print(f"   ⏭ تخطي — درجة الأهمية {score}/10: {data.get('reason')}")
        return None

    print(f"   ✅ خبر يستحق النشر ({score}/10)")
    print(f"   📌 {data.get('title')}")
    print(f"   💥 التأثير: {data.get('impact')}")
    return data


def save_post(content: dict, date_str: str):
    from image_generator import make_advisory

    slug      = f"offsec-{date_str}"
    post_file = POSTS_DIR / f"{date_str}-{slug}.md"
    img_out   = IMAGES_DIR / f"{date_str}-advisory.png"

    sev_en = {"حرجة":"critical","عالية":"high","متوسطة":"medium"}.get(content.get("severity",""),"high")

    try:
        make_advisory(
            content.get("title",""),
            content.get("category",""),
            content.get("severity",""),
            content.get("cvss",""),
            content.get("cve",""),
            content.get("body","")[:350],
            content.get("body",""),
            'آخر إصدار', 'تحديث مطلوب',
            'تنفيذ عن بُعد', 'دون مصادقة',
            'الإنترنت', 'عام',
            date_str, '', img_out
        )
    except Exception as e:
        print(f"   ⚠️ صورة: {e}")

    fm = f"""---
layout: post
title: "{content.get('title','').replace('"',"'")}"
date: {date_str}T08:00:00Z
category: "{content.get('category','')}"
severity: "{content.get('severity','')}"
severity_en: "{sev_en}"
cvss: "{content.get('cvss','')}"
cve: "{content.get('cve','')}"
source_url: "{content.get('source_url','')}"
impact: "{content.get('impact','').replace('"',"'")}"
image: "/OffsecAR/assets/images/{date_str}-advisory.png"
---

{content.get('body','')}
"""
    post_file.write_text(fm, encoding="utf-8")
    print(f"   📝 {post_file.name}")
    return post_file


def main():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"🔍 فحص الأخبار — {date_str}")

    news = fetch_news()
    print(f"   📡 {len(news)} خبر من المصادر")

    content = evaluate_and_write(news)

    if content is None:
        print("✅ لا يوجد ما يستحق النشر اليوم")
        return

    save_post(content, date_str)
    print("✅ تم النشر!")


if __name__ == "__main__":
    main()
