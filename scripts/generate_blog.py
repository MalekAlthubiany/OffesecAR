#!/usr/bin/env python3
"""
OffsecAR — مولّد المقالات اليومية
ينشئ 3 مقالات تقنية عميقة بالعربي + صورة hero لكل مقالة
"""

import os
import json
import anthropic
from datetime import datetime, timezone, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BLOGS_DIR  = Path("_blogs")
IMAGES_DIR = Path("assets/images/blogs")
BLOGS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

DAILY_COUNT = 3

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
    # AI Red Team
    {"title_hint": "AI Red Team: مهاجمة نماذج اللغة الكبيرة",   "category": "AI Red Team", "slug": "llm-attack-techniques"},
    {"title_hint": "Jailbreaking: كسر قيود نماذج الذكاء الاصطناعي", "category": "AI Red Team", "slug": "llm-jailbreaking"},
    {"title_hint": "RAG Poisoning: تسميم قواعد المعرفة",         "category": "AI Red Team", "slug": "rag-poisoning"},
    {"title_hint": "AI Agent Hijacking: اختطاف وكلاء الذكاء الاصطناعي", "category": "AI Red Team", "slug": "ai-agent-hijacking"},
    {"title_hint": "Model Extraction: سرقة نماذج الذكاء الاصطناعي", "category": "AI Red Team", "slug": "model-extraction"},
    {"title_hint": "Adversarial Examples: خداع أنظمة الرؤية الاصطناعية", "category": "AI Red Team", "slug": "adversarial-examples"},
]


def pick_todays_topics() -> list[dict]:
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
    topics = []
    for i in range(DAILY_COUNT):
        idx = (day_of_year * DAILY_COUNT + i) % len(TOPICS)
        topics.append(TOPICS[idx])
    return topics


def generate_blog_post(topic: dict) -> dict:
    prompt = f"""أنت كاتب تقني متخصص في Offensive Security، تكتب بأسلوب شركة ثمانية:
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

    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


def create_blog_image(title: str, category: str, slug: str) -> Path:
    """يصمم صورة hero بأسلوب ثمانية الداكن"""
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#0d0d0d")
    draw = ImageDraw.Draw(img)

    # خلفية
    draw.rectangle([0, 0, W, H], fill="#0d0d0d")
    draw.rectangle([0, 0, W, 5], fill="#e03c2a")  # شريط أحمر علوي
    draw.rectangle([0, H - 5, W, H], fill="#1a1a1a")  # شريط سفلي

    # تأثير خلفية خفي
    for i in range(0, W, 60):
        draw.line([(i, 0), (i, H)], fill="#111111", width=1)

    # ألوان التصنيف
    cat_colors = {
        "منهجية":     "#e03c2a",
        "تقنية":      "#e8884e",
        "أداة":       "#4e9de8",
        "تحليل":      "#9de84e",
        "AI Red Team": "#b44ee8",
    }
    cat_color = cat_colors.get(category, "#e03c2a")

    # تحميل الخطوط
    def load_font(size, bold=False):
        paths = [
            f"/usr/share/fonts/truetype/noto/NotoSansArabic-{'Bold' if bold else 'Regular'}.ttf",
            f"/usr/share/fonts/opentype/noto/NotoSansArabic-{'Bold' if bold else 'Regular'}.otf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for p in paths:
            if Path(p).exists():
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    font_cat      = load_font(22)
    font_title    = load_font(52, bold=True)
    font_brand    = load_font(20)

    def fix_arabic(text):
        if ARABIC_SUPPORT:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        return text

    # تاق التصنيف
    draw.rounded_rectangle([54, 40, 54 + 200, 40 + 42], radius=6,
                            fill="#1a0a08", outline=cat_color, width=1)
    draw.text((154, 61), fix_arabic(category), font=font_cat, fill=cat_color, anchor="mm")

    # العنوان — مع تقطيع للسطور
    def wrap_text(text, font, max_w):
        words = text.split()
        lines, line = [], []
        for w in words:
            test = " ".join(line + [w])
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_w:
                line.append(w)
            else:
                if line:
                    lines.append(" ".join(line))
                line = [w]
        if line:
            lines.append(" ".join(line))
        return lines

    title_lines = wrap_text(fix_arabic(title), font_title, W - 120)
    y = 130
    for line in title_lines[:3]:
        draw.text((W - 60, y), line, font=font_title, fill="#f0ede8", anchor="ra")
        y += 72

    # خط أحمر فاصل
    draw.rectangle([54, y + 16, 54 + 80, y + 20], fill=cat_color)

    # الشعار + التاريخ
    date_str = datetime.now(timezone.utc).strftime("%d %b %Y")
    draw.text((W - 60, H - 44), fix_arabic("OffsecAR"), font=font_brand, fill="#444444")
    draw.text((W - 60, H - 44), date_str, font=font_brand, fill="#444444", anchor="ra")

    # حفظ
    out_path = IMAGES_DIR / f"{slug}.png"
    img.save(out_path, "PNG", quality=95)
    print(f"   🖼️  الصورة: {out_path}")
    return out_path


def save_blog_post(topic: dict, content: dict, image_path: Path, offset_minutes: int = 0) -> Path:
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
image: "/OffsecAR/assets/images/blogs/{slug}.png"
---

{content['body']}
"""
    post_file.write_text(front_matter, encoding="utf-8")
    print(f"   📝 المقالة: {post_file}")
    return post_file


def main():
    print(f"📚 توليد {DAILY_COUNT} مقالات اليوم...")
    topics = pick_todays_topics()

    for i, topic in enumerate(topics):
        print(f"\n[{i+1}/{DAILY_COUNT}] {topic['title_hint']}")
        try:
            content = generate_blog_post(topic)
            print(f"   العنوان: {content['title']}")
            image_path = create_blog_image(
                content['title'],
                topic['category'],
                topic['slug']
            )
            save_blog_post(topic, content, image_path, offset_minutes=i)
        except Exception as e:
            print(f"   ⚠️ خطأ: {e}")
            continue

    print("\n✅ تم توليد المقالات!")


if __name__ == "__main__":
    main()
