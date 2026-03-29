#!/usr/bin/env python3
"""
OffsecAR — مولّد المقالات اليومية
ينشئ 3 مقالات تقنية عميقة بالعربي في مجال Offensive Security
"""

import os
import json
import anthropic
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BLOGS_DIR = Path("_blogs")
BLOGS_DIR.mkdir(exist_ok=True)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── قائمة المواضيع الدورية ─────────────────────────────────────────────────
TOPICS = [
    # منهجيات
    {"title_hint": "منهجية AI Red Team الشاملة",              "category": "منهجية", "slug": "ai-red-team-methodology"},
    {"title_hint": "اختبار اختراق تطبيقات الذكاء الاصطناعي",  "category": "منهجية", "slug": "ai-pentest-methodology"},
    {"title_hint": "منهجية Purple Team من الصفر",              "category": "منهجية", "slug": "purple-team-methodology"},
    {"title_hint": "Active Directory Attack Paths",             "category": "منهجية", "slug": "ad-attack-paths"},
    {"title_hint": "Cloud Red Team على AWS",                    "category": "منهجية", "slug": "aws-red-team"},
    {"title_hint": "منهجية تحليل البرمجيات الخبيثة",           "category": "منهجية", "slug": "malware-analysis-methodology"},
    {"title_hint": "منهجية اختبار اختراق الشبكات الداخلية",    "category": "منهجية", "slug": "internal-network-pentest"},
    {"title_hint": "Physical Red Team: اختراق المباني",         "category": "منهجية", "slug": "physical-red-team"},
    {"title_hint": "Web Application Penetration Testing",       "category": "منهجية", "slug": "web-app-pentest"},
    # تقنيات
    {"title_hint": "تقنيات LLVM Obfuscation للـ Red Team",      "category": "تقنية",  "slug": "llvm-obfuscation"},
    {"title_hint": "Kerberoasting: الدليل العملي",               "category": "تقنية",  "slug": "kerberoasting-guide"},
    {"title_hint": "NTLM Relay Attacks في 2025",                 "category": "تقنية",  "slug": "ntlm-relay-2025"},
    {"title_hint": "EDR Evasion: تقنيات التهرب الحديثة",        "category": "تقنية",  "slug": "edr-evasion"},
    {"title_hint": "Process Injection تقنيات متقدمة",            "category": "تقنية",  "slug": "process-injection"},
    {"title_hint": "Living off the Land: أدوات النظام سلاحاً",  "category": "تقنية",  "slug": "lolbas-techniques"},
    {"title_hint": "Prompt Injection هجمات نماذج اللغة",        "category": "تقنية",  "slug": "prompt-injection-attacks"},
    {"title_hint": "Supply Chain Attack تحليل عميق",             "category": "تقنية",  "slug": "supply-chain-attacks"},
    {"title_hint": "DNS Tunneling للـ C2 Traffic",               "category": "تقنية",  "slug": "dns-tunneling-c2"},
    {"title_hint": "Pass the Hash و Pass the Ticket",            "category": "تقنية",  "slug": "pass-the-hash-ticket"},
    {"title_hint": "SQL Injection تقنيات متقدمة",                "category": "تقنية",  "slug": "advanced-sql-injection"},
    {"title_hint": "Buffer Overflow من الأساس للاستغلال",        "category": "تقنية",  "slug": "buffer-overflow-guide"},
    # أدوات
    {"title_hint": "دليل Sliver C2 للـ Red Teamers",             "category": "أداة",   "slug": "sliver-c2-guide"},
    {"title_hint": "Cobalt Strike البديل المفتوح Havoc",         "category": "أداة",   "slug": "havoc-c2-framework"},
    {"title_hint": "Burp Suite مميزات لا تعرفها",                "category": "أداة",   "slug": "burp-suite-advanced"},
    {"title_hint": "BloodHound لتحليل Active Directory",         "category": "أداة",   "slug": "bloodhound-guide"},
    {"title_hint": "Metasploit تقنيات متقدمة 2025",              "category": "أداة",   "slug": "metasploit-advanced"},
    {"title_hint": "Nmap للمحترفين: تقنيات الـ Scanning",        "category": "أداة",   "slug": "nmap-advanced"},
    {"title_hint": "Impacket: السكاكين السويسرية للـ Red Team",  "category": "أداة",   "slug": "impacket-guide"},
    {"title_hint": "Frida لتحليل التطبيقات ديناميكياً",         "category": "أداة",   "slug": "frida-dynamic-analysis"},
    # تحليلات
    {"title_hint": "تحليل هجوم SolarWinds: الدروس المستفادة",   "category": "تحليل",  "slug": "solarwinds-analysis"},
    {"title_hint": "APT29 تكتيكات وأساليب الهجوم",              "category": "تحليل",  "slug": "apt29-tactics"},
    {"title_hint": "Zero-Day: من الاكتشاف للاستغلال",           "category": "تحليل",  "slug": "zero-day-lifecycle"},
    {"title_hint": "Ransomware تشريح هجوم كامل",                 "category": "تحليل",  "slug": "ransomware-anatomy"},
    {"title_hint": "MITRE ATT&CK: كيف تستخدمه عملياً",          "category": "تحليل",  "slug": "mitre-attack-practical"},
    {"title_hint": "Lazarus Group: تكتيكات أخطر مجموعة APT",    "category": "تحليل",  "slug": "lazarus-group-analysis"},
]

# عدد المقالات يومياً
DAILY_COUNT = 3


def pick_todays_topics() -> list[dict]:
    """يختار 3 مواضيع مختلفة لليوم بشكل دوري"""
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
    topics = []
    for i in range(DAILY_COUNT):
        idx = (day_of_year * DAILY_COUNT + i) % len(TOPICS)
        topics.append(TOPICS[idx])
    return topics


def generate_blog_post(topic: dict) -> dict:
    """يكتب مقالة تقنية عميقة بأسلوب ثمانية"""
    prompt = f"""أنت كاتب تقني متخصص في Offensive Security، تكتب بأسلوب شركة ثمانية:
- عربية فصحى واضحة، جمل قصيرة وحيوية
- المصطلحات التقنية تبقى إنجليزية (exploit, payload, shellcode, C2, etc.)
- الأسلوب: تحليلي، عملي، يخاطب المختص

اكتب مقالة تقنية متكاملة عن: "{topic['title_hint']}"
التصنيف: {topic['category']}

أرجع JSON فقط بهذه الحقول:
{{
  "title": "عنوان المقالة (15-20 كلمة)",
  "excerpt": "مقدمة جذابة (3-4 جمل)",
  "read_time": "وقت القراءة بالدقائق (رقم فقط)",
  "body": "جسم المقالة الكامل بصيغة Markdown:\\n- استخدم ## للعناوين الفرعية\\n- استخدم ```bash أو ```python للكود\\n- 600-900 كلمة\\n- قسّمها لـ 4-5 أقسام\\n- أضف أمثلة عملية وكود حيثما ناسب",
  "tags": ["تاق1", "تاق2", "تاق3"]
}}"""

    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


def save_blog_post(topic: dict, content: dict, offset_minutes: int = 0) -> Path:
    """يحفظ المقالة كملف Markdown لـ Jekyll"""
    now = datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    slug = topic["slug"]
    post_file = BLOGS_DIR / f"{date_str}-{slug}.md"

    tags_str = ", ".join(f'"{t}"' for t in content.get("tags", []))

    front_matter = f"""---
layout: blog
title: "{content['title'].replace('"', "'")}"
date: {time_str}
category: "{topic['category']}"
excerpt: "{content['excerpt'].replace('"', "'")}"
read_time: {content.get('read_time', 8)}
tags: [{tags_str}]
slug: "{slug}"
---

{content['body']}
"""
    post_file.write_text(front_matter, encoding="utf-8")
    print(f"✅ المقالة: {post_file}")
    return post_file


def main():
    print(f"📚 توليد {DAILY_COUNT} مقالات اليوم...")
    topics = pick_todays_topics()

    for i, topic in enumerate(topics):
        print(f"\n[{i+1}/{DAILY_COUNT}] {topic['title_hint']}")
        try:
            content = generate_blog_post(topic)
            print(f"   العنوان: {content['title']}")
            save_blog_post(topic, content, offset_minutes=i)
        except Exception as e:
            print(f"   ⚠️ خطأ: {e}")
            continue

    print("\n✅ تم توليد المقالات!")


if __name__ == "__main__":
    main()
