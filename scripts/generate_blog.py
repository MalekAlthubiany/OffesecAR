#!/usr/bin/env python3
"""
OffsecAR — مولّد المقالات اليومية
كل يوم ينشئ 3 مقالات:
  1. فئة دورية (منهجية / تقنية / أداة / تحليل)
  2. AI Red Team — ثابتة يومياً
  3. مقالة تحليلية مبنية على آخر أخبار الإنترنت
"""

import os, json, re, feedparser, requests
import anthropic
from datetime import datetime, timezone, timedelta
from pathlib import Path
from image_generator import create_blog_image_svg

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BLOGS_DIR  = Path("_blogs")
IMAGES_DIR = Path("assets/images/blogs")
BLOGS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── قوائم المواضيع ──────────────────────────────────────────────────────────

GENERAL_TOPICS = [
    {"title_hint": "منهجية Purple Team من الصفر",              "category": "منهجية", "slug": "purple-team-methodology"},
    {"title_hint": "Active Directory Attack Paths",             "category": "منهجية", "slug": "ad-attack-paths"},
    {"title_hint": "Cloud Red Team على AWS",                    "category": "منهجية", "slug": "aws-red-team"},
    {"title_hint": "منهجية تحليل البرمجيات الخبيثة",           "category": "منهجية", "slug": "malware-analysis-methodology"},
    {"title_hint": "منهجية اختبار اختراق الشبكات الداخلية",    "category": "منهجية", "slug": "internal-network-pentest"},
    {"title_hint": "Physical Red Team: اختراق المباني",         "category": "منهجية", "slug": "physical-red-team"},
    {"title_hint": "Web Application Penetration Testing",       "category": "منهجية", "slug": "web-app-pentest"},
    {"title_hint": "تقنيات LLVM Obfuscation للـ Red Team",      "category": "تقنية",  "slug": "llvm-obfuscation"},
    {"title_hint": "Kerberoasting: الدليل العملي",               "category": "تقنية",  "slug": "kerberoasting-guide"},
    {"title_hint": "NTLM Relay Attacks في 2025",                 "category": "تقنية",  "slug": "ntlm-relay-2025"},
    {"title_hint": "EDR Evasion: تقنيات التهرب الحديثة",        "category": "تقنية",  "slug": "edr-evasion"},
    {"title_hint": "Process Injection تقنيات متقدمة",            "category": "تقنية",  "slug": "process-injection"},
    {"title_hint": "Living off the Land: أدوات النظام سلاحاً",  "category": "تقنية",  "slug": "lolbas-techniques"},
    {"title_hint": "DNS Tunneling للـ C2 Traffic",               "category": "تقنية",  "slug": "dns-tunneling-c2"},
    {"title_hint": "Pass the Hash و Pass the Ticket",            "category": "تقنية",  "slug": "pass-the-hash-ticket"},
    {"title_hint": "SQL Injection تقنيات متقدمة",                "category": "تقنية",  "slug": "advanced-sql-injection"},
    {"title_hint": "Buffer Overflow من الأساس للاستغلال",        "category": "تقنية",  "slug": "buffer-overflow-guide"},
    {"title_hint": "دليل Sliver C2 للـ Red Teamers",             "category": "أداة",   "slug": "sliver-c2-guide"},
    {"title_hint": "Cobalt Strike البديل المفتوح Havoc",         "category": "أداة",   "slug": "havoc-c2-framework"},
    {"title_hint": "Burp Suite مميزات لا تعرفها",                "category": "أداة",   "slug": "burp-suite-advanced"},
    {"title_hint": "BloodHound لتحليل Active Directory",         "category": "أداة",   "slug": "bloodhound-guide"},
    {"title_hint": "Metasploit تقنيات متقدمة 2025",              "category": "أداة",   "slug": "metasploit-advanced"},
    {"title_hint": "Nmap للمحترفين: تقنيات الـ Scanning",        "category": "أداة",   "slug": "nmap-advanced"},
    {"title_hint": "Impacket: السكاكين السويسرية للـ Red Team",  "category": "أداة",   "slug": "impacket-guide"},
    {"title_hint": "Frida لتحليل التطبيقات ديناميكياً",         "category": "أداة",   "slug": "frida-dynamic-analysis"},
    {"title_hint": "تحليل هجوم SolarWinds: الدروس المستفادة",   "category": "تحليل",  "slug": "solarwinds-analysis"},
    {"title_hint": "APT29 تكتيكات وأساليب الهجوم",              "category": "تحليل",  "slug": "apt29-tactics"},
    {"title_hint": "Zero-Day: من الاكتشاف للاستغلال",           "category": "تحليل",  "slug": "zero-day-lifecycle"},
    {"title_hint": "Ransomware تشريح هجوم كامل",                 "category": "تحليل",  "slug": "ransomware-anatomy"},
    {"title_hint": "MITRE ATT&CK: كيف تستخدمه عملياً",          "category": "تحليل",  "slug": "mitre-attack-practical"},
    {"title_hint": "Lazarus Group: تكتيكات أخطر مجموعة APT",    "category": "تحليل",  "slug": "lazarus-group-analysis"},
]

AI_RED_TEAM_TOPICS = [
    {"title_hint": "AI Red Team: مهاجمة نماذج اللغة الكبيرة",        "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "llm-attack-techniques"},
    {"title_hint": "Jailbreaking: كسر قيود نماذج الذكاء الاصطناعي",  "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "llm-jailbreaking"},
    {"title_hint": "RAG Poisoning: تسميم قواعد المعرفة",              "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "rag-poisoning"},
    {"title_hint": "AI Agent Hijacking: اختطاف وكلاء الذكاء الاصطناعي", "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "ai-agent-hijacking"},
    {"title_hint": "Model Extraction: سرقة نماذج الذكاء الاصطناعي",   "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "model-extraction"},
    {"title_hint": "Adversarial Examples: خداع أنظمة الرؤية الاصطناعية", "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "adversarial-examples"},
    {"title_hint": "Prompt Injection في تطبيقات الإنتاج",             "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "prompt-injection-production"},
    {"title_hint": "LLM Fine-tuning Attacks: تلاعب بالنماذج",         "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "llm-finetuning-attacks"},
    {"title_hint": "AI Supply Chain: تسميم بيانات التدريب",           "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "ai-supply-chain-poisoning"},
    {"title_hint": "Multimodal Attacks: اختراق عبر الصور والصوت",     "category": "الأمن الهجومي في الذكاء الاصطناعي", "slug": "multimodal-attacks"},
]

NEWS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://portswigger.net/daily-swig/rss",
    "https://www.darkreading.com/rss.xml",
    "https://www.exploit-db.com/rss.xml",
]

BUGBOUNTY_FEEDS = [
    "https://medium.com/feed/bug-bounty-writeups",
    "https://medium.com/feed/bugbountywriteup",
    "https://feeds.feedburner.com/PentesterLab",
]

BUGBOUNTY_KEYWORDS = [
    "writeup", "write-up", "bug bounty", "bounty", "hackerone", "bugcrowd",
    "XSS", "SSRF", "SQLi", "RCE", "IDOR", "CSRF", "XXE", "open redirect",
    "account takeover", "authentication bypass", "privilege escalation"
]


def pick_todays_general_topic() -> dict:
    day = datetime.now(timezone.utc).timetuple().tm_yday
    return GENERAL_TOPICS[day % len(GENERAL_TOPICS)]


def pick_todays_ai_topic() -> dict:
    day = datetime.now(timezone.utc).timetuple().tm_yday
    return AI_RED_TEAM_TOPICS[day % len(AI_RED_TEAM_TOPICS)]


def fetch_latest_news() -> list[dict]:
    items = []
    for url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                items.append({
                    "title":   entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", ""))[:500],
                    "link":    entry.get("link", ""),
                    "source":  feed.feed.get("title", ""),
                })
        except Exception as e:
            print(f"   ⚠️ {url}: {e}")
    return items[:12]


AI_NEWS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://portswigger.net/daily-swig/rss",
]

AI_KEYWORDS = ["AI", "LLM", "GPT", "Claude", "artificial intelligence", "machine learning",
                "prompt injection", "jailbreak", "model", "chatbot", "OpenAI", "Anthropic",
                "deepfake", "generative", "neural", "agent"]

def fetch_ai_security_news() -> list[dict]:
    """يجمع أخبار الأمن المتعلقة بالذكاء الاصطناعي"""
    items = []
    for url in AI_NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                # فلتر أخبار الذكاء الاصطناعي
                combined = (title + " " + summary).lower()
                if any(kw.lower() in combined for kw in AI_KEYWORDS):
                    items.append({
                        "title":   title,
                        "summary": summary[:500],
                        "link":    entry.get("link", ""),
                        "source":  feed.feed.get("title", ""),
                    })
        except Exception as e:
            print(f"   ⚠️ {url}: {e}")
    return items[:6]


def generate_ai_security_post(news_items: list[dict], topic: dict) -> dict:
    """يكتب مقالة عن الأمن الهجومي في الذكاء الاصطناعي مبنية على أخبار الإنترنت"""
    news_json = json.dumps(news_items, ensure_ascii=False, indent=2)
    prompt = f"""أنت خبير في أمن الذكاء الاصطناعي، تكتب بأسلوب ثمانية العربي الرصين.

استناداً لهذه الأخبار الحديثة عن أمن الذكاء الاصطناعي:
{news_json}

اكتب مقالة متخصصة تجمع بين:
- تحليل الأخبار من منظور الأمن الهجومي
- شرح التقنيات والأدوات المذكورة
- ربطها بموضوع: "{topic['title_hint']}"
- توصيات عملية للمختصين

المقالة يجب أن تكون محدّثة ومبنية على المستجدات الحقيقية.

أرجع JSON فقط:
{{
  "title": "عنوان مشوق يعكس آخر المستجدات (15-20 كلمة)",
  "excerpt": "مقدمة جذابة (3-4 جمل)",
  "read_time": "وقت القراءة بالدقائق (رقم)",
  "body": "المقالة الكاملة بصيغة Markdown، 700-1000 كلمة، 4-5 أقسام بـ ##",
  "tags": ["تاق1", "تاق2", "تاق3"]
}}"""
    resp = client.messages.create(model="claude-sonnet-4-5", max_tokens=3000,
                                   messages=[{"role": "user", "content": prompt}])
    raw = re.sub(r"^```json\s*|```$", "", resp.content[0].text.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


def generate_general_post(topic: dict) -> dict:
    prompt = f"""أنت كاتب تقني متخصص في Offensive Security، تكتب بأسلوب ثمانية:
- عربية فصحى واضحة، جمل قصيرة وحيوية
- المصطلحات التقنية تبقى إنجليزية
- الأسلوب: تحليلي، عملي، يخاطب المختص

اكتب مقالة تقنية متكاملة عن: "{topic['title_hint']}"
التصنيف: {topic['category']}

أرجع JSON فقط:
{{
  "title": "عنوان المقالة (15-20 كلمة)",
  "excerpt": "مقدمة جذابة (3-4 جمل)",
  "read_time": "وقت القراءة بالدقائق (رقم فقط)",
  "body": "جسم المقالة بصيغة Markdown، 600-900 كلمة، 4-5 أقسام بـ ##، مع كود عملي",
  "tags": ["تاق1", "تاق2", "تاق3"]
}}"""
    resp = client.messages.create(model="claude-sonnet-4-5", max_tokens=2500, messages=[{"role": "user", "content": prompt}])
    raw = re.sub(r"^```json\s*|```$", "", resp.content[0].text.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


def generate_news_post(news_items: list[dict]) -> dict:
    news_json = json.dumps(news_items, ensure_ascii=False, indent=2)
    prompt = f"""أنت محلل أمن هجومي متخصص، تكتب بأسلوب ثمانية العربي.

من هذه الأخبار الحديثة، اختر الأبرز في مجال Offensive Security واكتب مقالة تحليلية عميقة عنها:

{news_json}

المقالة يجب أن:
- تحلل الخبر بعمق من منظور الأمن الهجومي
- تشرح التقنيات والثغرات المستخدمة
- تقدم توصيات عملية للـ Red Teamers
- تربط الخبر بسياق أشمل في مجال الأمن

أرجع JSON فقط:
{{
  "title": "عنوان تحليلي مشوق (15-20 كلمة)",
  "excerpt": "مقدمة تشد القارئ (3-4 جمل)",
  "read_time": "وقت القراءة بالدقائق (رقم)",
  "body": "التحليل الكامل بصيغة Markdown، 700-1000 كلمة، 4-5 أقسام",
  "tags": ["تاق1", "تاق2", "تاق3"],
  "source_title": "عنوان الخبر الأصلي",
  "source_url": "رابط الخبر"
}}"""
    resp = client.messages.create(model="claude-sonnet-4-5", max_tokens=3000, messages=[{"role": "user", "content": prompt}])
    raw = re.sub(r"^```json\s*|```$", "", resp.content[0].text.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


def save_blog_post(topic_cat: str, topic_slug: str, content: dict, offset_minutes: int = 0) -> Path:
    now = datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    post_file = BLOGS_DIR / f"{date_str}-{topic_slug}.md"
    tags_str = ", ".join(f'"{t}"' for t in content.get("tags", []))

    image_path = create_blog_image_svg(content['title'], topic_cat, topic_slug, IMAGES_DIR)

    front_matter = f"""---
layout: blog
title: "{content['title'].replace('"', "'")}"
date: {time_str}
category: "{topic_cat}"
excerpt: "{content['excerpt'].replace('"', "'")}"
read_time: {content.get('read_time', 8)}
tags: [{tags_str}]
slug: "{topic_slug}"
image: "/OffsecAR/assets/images/blogs/{topic_slug}.svg"
---

{content['body']}
"""
    post_file.write_text(front_matter, encoding="utf-8")
    print(f"   📝 {post_file.name}")
    return post_file


def fetch_bugbounty_writeups() -> list[dict]:
    """يجمع writeups من منصات Bug Bounty"""
    items = []
    for url in BUGBOUNTY_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                combined = (title + " " + summary).lower()
                if any(kw.lower() in combined for kw in BUGBOUNTY_KEYWORDS):
                    items.append({
                        "title":   title,
                        "summary": summary[:600],
                        "link":    entry.get("link", ""),
                        "source":  feed.feed.get("title", ""),
                    })
        except Exception as e:
            print(f"   ⚠️ {url}: {e}")
    return items[:5]


def generate_bugbounty_post(writeups: list[dict]) -> dict:
    """يكتب ملخص writeup بأسلوب OffsecAR"""
    writeups_json = json.dumps(writeups, ensure_ascii=False, indent=2)
    prompt = f"""أنت محلل أمن هجومي متخصص في Bug Bounty، تكتب بأسلوب ثمانية العربي.

من هذه الـ writeups الحديثة اختر الأبرز واكتب مقالة تقنية عربية عنها:
{writeups_json}

المقالة يجب أن:
- تشرح الثغرة المكتشفة بوضوح (النوع، التأثير، كيف تعمل)
- تصف خطوات الاكتشاف باختصار
- تقدم الدروس المستفادة للـ Bug Hunter
- تضع السياق الأمني الأشمل
- تذكر المنصة والباحث والمكافأة إن توفرت
- تضع رابط المصدر في النهاية

أرجع JSON فقط:
{{
  "title": "عنوان تقني مشوق (15-20 كلمة)",
  "excerpt": "مقدمة جذابة (3-4 جمل)",
  "read_time": "وقت القراءة بالدقائق (رقم)",
  "body": "المقالة الكاملة بصيغة Markdown، 600-900 كلمة، 4-5 أقسام بـ ##",
  "tags": ["Bug Bounty", "ثغرات", "تاق3"],
  "source_title": "عنوان الـ writeup الأصلي",
  "source_url": "رابط المصدر"
}}"""
    resp = client.messages.create(model="claude-sonnet-4-5", max_tokens=3000,
                                   messages=[{"role": "user", "content": prompt}])
    raw = re.sub(r"^```json\s*|```$", "", resp.content[0].text.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


def main():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"📚 توليد مقالات {date_str}...\n")

    # ── ١. مقالة الفئة الدورية ──────────────────────────────────────────
    topic1 = pick_todays_general_topic()
    print(f"[1/3] {topic1['category']} — {topic1['title_hint']}")
    try:
        content1 = generate_general_post(topic1)
        print(f"   العنوان: {content1['title']}")
        save_blog_post(topic1['category'], topic1['slug'], content1, offset_minutes=0)
    except Exception as e:
        print(f"   ⚠️ {e}")

    # ── ٢. مقالة الأمن الهجومي في الذكاء الاصطناعي (من أخبار الإنترنت) ──
    print(f"\n[2/3] الأمن الهجومي في الذكاء الاصطناعي — من أخبار الإنترنت")
    try:
        ai_news = fetch_ai_security_news()
        topic2 = pick_todays_ai_topic()
        if ai_news:
            content2 = generate_ai_security_post(ai_news, topic2)
        else:
            content2 = generate_general_post(topic2)
        print(f"   العنوان: {content2['title']}")
        slug2 = f"ai-security-{date_str}"
        save_blog_post("الأمن الهجومي في الذكاء الاصطناعي", slug2, content2, offset_minutes=1)
    except Exception as e:
        print(f"   ⚠️ {e}")

    # ── ٣. مقالة من أخبار اليوم ─────────────────────────────────────────
    print(f"\n[3/4] تحليل أخبار — من الإنترنت")
    try:
        news = fetch_latest_news()
        if news:
            content3 = generate_news_post(news)
            print(f"   العنوان: {content3['title']}")
            slug3 = f"news-analysis-{date_str}"
            save_blog_post("تحليل", slug3, content3, offset_minutes=2)
        else:
            print("   ⚠️ لا توجد أخبار")
    except Exception as e:
        print(f"   ⚠️ {e}")

    # ── ٤. مقالة Bug Bounty Writeup ──────────────────────────────────────
    print(f"\n[4/4] Bug Bounty Writeup — من منصات المكافأة")
    try:
        writeups = fetch_bugbounty_writeups()
        if writeups:
            content4 = generate_bugbounty_post(writeups)
            print(f"   العنوان: {content4['title']}")
            slug4 = f"bugbounty-{date_str}"
            save_blog_post("Bug Bounty", slug4, content4, offset_minutes=3)
        else:
            print("   ⚠️ لا توجد writeups")
    except Exception as e:
        print(f"   ⚠️ {e}")

    print("\n✅ تم توليد المقالات الأربع!")


if __name__ == "__main__":
    main()
