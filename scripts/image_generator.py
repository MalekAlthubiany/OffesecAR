#!/usr/bin/env python3
"""مولّد صور PNG لكل منصة"""

from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False


def fix(text: str) -> str:
    if HAS_ARABIC and text:
        try:
            return get_display(arabic_reshaper.reshape(text))
        except:
            pass
    return text


def font(size: int, bold: bool = False):
    for p in [
        f"/usr/share/fonts/truetype/noto/NotoSansArabic-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/opentype/noto/NotoSansArabic-{'Bold' if bold else 'Regular'}.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(text, fnt, draw, max_w):
    words, lines, line = text.split(), [], []
    for w in words:
        test = " ".join(line + [w])
        if draw.textbbox((0,0), test, font=fnt)[2] <= max_w:
            line.append(w)
        else:
            if line: lines.append(" ".join(line))
            line = [w]
    if line: lines.append(" ".join(line))
    return lines


CAT_COLORS = {
    "منهجية": "#e03c2a", "تقنية": "#e8884e", "أداة": "#4e9de8",
    "تحليل": "#7ec845", "الأمن الهجومي في الذكاء الاصطناعي": "#b44ee8",
    "AI Red Team": "#b44ee8", "ثغرة حرجة": "#e03c2a",
    "تقنية هجوم": "#e8884e", "تهديد متقدم": "#e8c44e",
}
SEV_COLORS = {"حرجة": "#e03c2a", "عالية": "#e8884e", "متوسطة": "#e8c44e"}


def _base_canvas(w, h, accent="#e03c2a"):
    img = Image.new("RGB", (w, h), "#0d0d0d")
    d = ImageDraw.Draw(img)
    for i in range(0, w, 50):
        d.line([(i,0),(i,h)], fill="#111", width=1)
    d.rectangle([0,0,w,4], fill=accent)
    return img, d


def make_twitter(title, category, severity, cvss, excerpt, date_str, out: Path):
    """صورة تويتر 1080×1080"""
    W, H = 1080, 1080
    accent = SEV_COLORS.get(severity, CAT_COLORS.get(category, "#e03c2a"))
    img, d = _base_canvas(W, H, accent)

    f_tag   = font(20)
    f_title = font(50, bold=True)
    f_body  = font(28)
    f_small = font(19)

    # تاق
    d.rounded_rectangle([54,26,54+160,26+38], radius=5, fill="#1a0804", outline=accent, width=1)
    d.text((134,45), fix("OffsecAR"), font=f_tag, fill=accent, anchor="mm")

    # تصنيف يمين
    d.text((W-54, 45), fix(category), font=f_tag, fill="#666", anchor="ra")

    # خط فاصل
    d.rectangle([54,82,W-54,83], fill="#222")

    # عنوان
    lines = wrap(fix(title), f_title, d, W-120)
    y = 120
    for line in lines[:3]:
        d.text((W-60, y), line, font=f_title, fill="#f0ede8", anchor="ra")
        y += 66

    # خط أحمر
    d.rectangle([54, y+10, 54+50, y+14], fill=accent)
    y += 44

    # ملخص
    body_lines = wrap(fix(excerpt[:300]), f_body, d, W-120)
    for line in body_lines[:5]:
        d.text((W-60, y), line, font=f_body, fill="#aaaaaa", anchor="ra")
        y += 42

    # خطورة
    if severity and severity not in ("", "None"):
        sev_y = H-160
        sev_col = SEV_COLORS.get(severity, "#e8884e")
        d.rounded_rectangle([54,sev_y,54+260,sev_y+40], radius=6, fill="#1a1a1a", outline=sev_col, width=1)
        sev_txt = fix(f"خطورة {severity}")
        if cvss and cvss not in ("","None"):
            sev_txt += f"  CVSS {cvss}"
        d.text((74, sev_y+20), sev_txt, font=f_small, fill=sev_col, anchor="lm")

    # فاصل سفلي
    d.rectangle([54,H-94,W-54,H-93], fill="#222")
    d.text((60, H-70), "@OffsecAR", font=f_small, fill="#444")
    d.text((W-60, H-70), date_str, font=f_small, fill="#444", anchor="ra")

    img.save(out, "PNG")
    return out


def make_linkedin(title, category, excerpt, date_str, out: Path):
    """صورة لينكدإن 1200×627"""
    W, H = 1200, 627
    accent = CAT_COLORS.get(category, "#4e9de8")
    img, d = _base_canvas(W, H, accent)

    f_cat   = font(20)
    f_title = font(46, bold=True)
    f_body  = font(26)
    f_small = font(18)

    # تاق
    d.rounded_rectangle([54,22,54+160,22+36], radius=5, fill="#0a1a2a", outline=accent, width=1)
    d.text((134,40), fix("OffsecAR"), font=f_cat, fill=accent, anchor="mm")
    d.text((W-54,40), fix(category), font=f_cat, fill="#666", anchor="ra")
    d.rectangle([54,70,W-54,71], fill="#222")

    # عنوان
    lines = wrap(fix(title), f_title, d, W-120)
    y = 100
    for line in lines[:2]:
        d.text((W-60, y), line, font=f_title, fill="#f0ede8", anchor="ra")
        y += 60

    d.rectangle([54, y+8, 54+50, y+12], fill=accent)
    y += 38

    # ملخص
    body_lines = wrap(fix(excerpt[:250]), f_body, d, W-120)
    for line in body_lines[:4]:
        d.text((W-60, y), line, font=f_body, fill="#aaaaaa", anchor="ra")
        y += 38

    # فوتر
    d.rectangle([54,H-68,W-54,H-67], fill="#222")
    d.text((60, H-44), "@OffsecAR  |  linkedin.com/company/OffsecAR", font=f_small, fill="#444")
    d.text((W-60, H-44), date_str, font=f_small, fill="#444", anchor="ra")

    img.save(out, "PNG")
    return out


def make_whatsapp(title, category, excerpt, date_str, out: Path):
    """صورة واتساب 800×800"""
    W, H = 800, 800
    accent = CAT_COLORS.get(category, "#25d366")
    img, d = _base_canvas(W, H, "#1a1a1a")

    # شريط أخضر جانبي
    d.rectangle([0,0,5,H], fill="#25d366")

    f_cat   = font(18)
    f_title = font(40, bold=True)
    f_body  = font(24)
    f_small = font(17)

    d.text((30, 28), fix("OffsecAR"), font=f_cat, fill="#25d366")
    d.text((W-30, 28), fix(category), font=f_cat, fill="#555", anchor="ra")
    d.rectangle([30,60,W-30,61], fill="#222")

    lines = wrap(fix(title), f_title, d, W-80)
    y = 88
    for line in lines[:3]:
        d.text((W-30, y), line, font=f_title, fill="#f0ede8", anchor="ra")
        y += 56

    d.rectangle([30, y+8, 30+40, y+11], fill="#25d366")
    y += 36

    body_lines = wrap(fix(excerpt[:220]), f_body, d, W-80)
    for line in body_lines[:5]:
        d.text((W-30, y), line, font=f_body, fill="#aaa", anchor="ra")
        y += 36

    d.rectangle([30,H-60,W-30,H-59], fill="#222")
    d.text((30, H-38), "@OffsecAR", font=f_small, fill="#333")
    d.text((W-30, H-38), date_str, font=f_small, fill="#333", anchor="ra")

    img.save(out, "PNG")
    return out


def create_blog_image_svg(title, category, slug, images_dir: Path):
    """واجهة قديمة — تولّد صور الثلاث منصات"""
    date_str = datetime.now(timezone.utc).strftime("%d %b %Y")
    exc = title
    make_twitter(title, category, "", "", exc, date_str, images_dir / f"{slug}-tw.png")
    make_linkedin(title, category, exc, date_str, images_dir / f"{slug}-li.png")
    make_whatsapp(title, category, exc, date_str, images_dir / f"{slug}-wa.png")
    return images_dir / f"{slug}-tw.png"


def create_news_image_svg(headline, category, severity, cvss, images_dir: Path, date_str):
    """يولّد صور الثلاث منصات للخبر"""
    make_twitter(headline, category, severity, cvss, headline, date_str, images_dir / f"{date_str}-tw.png")
    make_linkedin(headline, category, headline, date_str, images_dir / f"{date_str}-li.png")
    make_whatsapp(headline, category, headline, date_str, images_dir / f"{date_str}-wa.png")
    return images_dir / f"{date_str}-tw.png"
