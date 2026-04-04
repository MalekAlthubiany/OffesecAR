#!/usr/bin/env python3
"""
مولّد الصور PNG - باستخدام Pillow مع arabic-reshaper
"""

from pathlib import Path
from datetime import datetime, timezone

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False

from PIL import Image, ImageDraw, ImageFont

def fix_arabic(text: str) -> str:
    if HAS_ARABIC and text:
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except:
            pass
    return text

def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    paths = [
        f"/usr/share/fonts/truetype/noto/NotoSansArabic-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/opentype/noto/NotoSansArabic-{'Bold' if bold else 'Regular'}.otf",
        f"/usr/share/fonts/truetype/noto/NotoNaskhArabic-{'Bold' if bold else 'Regular'}.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap_text(text: str, font, draw, max_width: int) -> list[str]:
    words = text.split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            line.append(word)
        else:
            if line: lines.append(" ".join(line))
            line = [word]
    if line: lines.append(" ".join(line))
    return lines

CAT_COLORS = {
    "منهجية":      "#e03c2a",
    "تقنية":       "#e8884e",
    "أداة":        "#4e9de8",
    "تحليل":       "#9de84e",
    "الأمن الهجومي في الذكاء الاصطناعي": "#b44ee8",
    "AI Red Team": "#b44ee8",
}

def create_blog_image_svg(title: str, category: str, slug: str, images_dir: Path) -> Path:
    """يصمم صورة blog PNG 1200x630"""
    W, H = 1200, 630
    cat_color = CAT_COLORS.get(category, "#e03c2a")
    date_str = datetime.now(timezone.utc).strftime("%d %b %Y")

    img = Image.new("RGB", (W, H), "#0d0d0d")
    draw = ImageDraw.Draw(img)

    # خلفية شبكة خفية
    for i in range(0, W, 60):
        draw.line([(i, 0), (i, H)], fill="#111111", width=1)

    # شريط علوي ملون
    draw.rectangle([0, 0, W, 6], fill=cat_color)

    # فونتات
    font_cat   = load_font(22)
    font_title = load_font(54, bold=True)
    font_small = load_font(20)

    # تاق التصنيف
    cat_fixed = fix_arabic(category)
    draw.rounded_rectangle([54, 28, 54+220, 28+42], radius=6, fill="#1a0804", outline=cat_color, width=1)
    draw.text((164, 49), cat_fixed, font=font_cat, fill=cat_color, anchor="mm")

    # العنوان
    title_fixed = fix_arabic(title)
    lines = wrap_text(title_fixed, font_title, draw, W - 140)
    y = 130
    for line in lines[:3]:
        draw.text((W - 70, y), line, font=font_title, fill="#f0ede8", anchor="ra")
        y += 72

    # خط فاصل أحمر
    draw.rectangle([54, y + 16, 54 + 80, y + 20], fill=cat_color, outline=None)

    # شعار وتاريخ
    draw.text((60, H - 44), "OffsecAR", font=font_small, fill="#444444")
    draw.text((W - 60, H - 44), date_str, font=font_small, fill="#444444", anchor="ra")

    # أيقونات التواصل
    tw_text = "twitter.com/OffsecAR"
    li_text = "linkedin.com/company/OffsecAR"
    draw.text((60, H - 80), f"𝕏  {tw_text}  ·  in  {li_text}", font=font_small, fill="#333333")

    out = images_dir / f"{slug}.png"
    img.save(out, "PNG")
    print(f"   🖼️  {out}")
    return out


def create_news_image_svg(headline: str, category: str, severity: str,
                           cvss: str, images_dir: Path, date_str: str) -> Path:
    """يصمم صورة خبر PNG 1080x1080"""
    W, H = 1080, 1080
    sev_colors = {"حرجة": "#e03c2a", "عالية": "#e8884e", "متوسطة": "#e8c44e"}
    sev_col = sev_colors.get(severity, "#e8884e")

    img = Image.new("RGB", (W, H), "#0d0d0d")
    draw = ImageDraw.Draw(img)

    for i in range(0, W, 60):
        draw.line([(i, 0), (i, H)], fill="#111111", width=1)

    draw.rectangle([0, 0, W, 6], fill="#e03c2a")

    font_tag   = load_font(22)
    font_title = load_font(52, bold=True)
    font_body  = load_font(30)
    font_small = load_font(22)

    # تاق OffsecAR
    draw.rounded_rectangle([54, 28, 54+200, 28+38], radius=6, fill="#1a0804", outline="#e03c2a", width=1)
    draw.text((154, 47), "OffsecAR", font=font_tag, fill="#e03c2a", anchor="mm")

    # التصنيف
    cat_fixed = fix_arabic(category)
    draw.text((W - 60, 110), cat_fixed, font=font_tag, fill="#888888", anchor="ra")

    # فاصل
    draw.rectangle([54, 155, W - 54, 157], fill="#2a2a2a")

    # العنوان
    title_fixed = fix_arabic(headline)
    lines = wrap_text(title_fixed, font_title, draw, W - 140)
    y = 220
    for line in lines[:3]:
        draw.text((W - 70, y), line, font=font_title, fill="#f5f5f5", anchor="ra")
        y += 72

    # خط أحمر
    draw.rectangle([54, y + 16, 54 + 60, y + 20], fill="#e03c2a")

    # درجة الخطورة
    if severity and severity not in ("", "None"):
        sev_y = H - 170
        draw.rounded_rectangle([54, sev_y, 54+280, sev_y+44], radius=8, fill="#1a1a1a", outline=sev_col, width=1)
        draw.ellipse([80, sev_y+15, 80+14, sev_y+29], fill=sev_col)
        sev_text = fix_arabic(f"خطورة {severity}")
        if cvss and cvss not in ("", "None"):
            sev_text += f"  ·  CVSS {cvss}"
        draw.text((104, sev_y+22), sev_text, font=font_small, fill=sev_col, anchor="la")

    # فاصل سفلي
    draw.rectangle([54, H - 100, W - 54, H - 98], fill="#2a2a2a")

    # شعار وتاريخ
    draw.text((60, H - 74), "@OffsecAR", font=font_small, fill="#555555")
    draw.text((W - 60, H - 74), date_str, font=font_small, fill="#555555", anchor="ra")

    # أيقونات التواصل
    draw.text((60, H - 42), "𝕏  twitter.com/OffsecAR  ·  in  linkedin.com/company/OffsecAR", font=font_small, fill="#333333")

    out = images_dir / f"{date_str}-post.png"
    img.save(out, "PNG")
    print(f"   🖼️  {out}")
    return out
