#!/usr/bin/env python3
"""مولّد صور PNG - Playwright مع خطوط نظام"""

import asyncio
from pathlib import Path
from datetime import datetime, timezone

CAT_COLORS = {
    "منهجية": "#e03c2a", "تقنية": "#e8884e", "أداة": "#4e9de8",
    "تحليل": "#7ec845", "ثغرة حرجة": "#e03c2a", "تقنية هجوم": "#e8884e",
    "تهديد متقدم": "#e8c44e", "تحليل أخبار": "#7ec845",
    "الأمن الهجومي في الذكاء الاصطناعي": "#b44ee8",
}
SEV_COLORS = {"حرجة": "#e03c2a", "عالية": "#e8884e", "متوسطة": "#e8c44e"}


def _find_arabic_font() -> str:
    """يجيب مسار خط عربي من النظام"""
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansArabic-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return ""


def _font_face(font_path: str) -> str:
    """يحول الخط لـ base64 داخل CSS"""
    if not font_path:
        return ""
    import base64
    data = base64.b64encode(Path(font_path).read_bytes()).decode()
    ext = "truetype" if font_path.endswith(".ttf") else "opentype"
    return f"""@font-face {{
  font-family: 'ArabicFont';
  src: url('data:font/{ext};base64,{data}') format('{ext}');
}}"""


def _build_html(title, category, severity, cvss, excerpt, date_str,
                w, h, accent, foot_handle, font_face_css):

    sev_block = ""
    if severity and severity not in ("", "None"):
        sc = SEV_COLORS.get(severity, "#e8884e")
        sev_txt = f"خطورة {severity}"
        if cvss and cvss not in ("", "None"):
            sev_txt += f"  ·  CVSS {cvss}"
        sev_block = f'<div class="sev" style="color:{sc};border-color:{sc}66;">{sev_txt}</div>'

    short = excerpt[:260] + ("..." if len(excerpt) > 260 else "")
    ftitle = 50 if w >= 1080 else 42
    fbody  = 26 if w >= 1080 else 22

    return f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<style>
{font_face_css}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  width:{w}px;height:{h}px;overflow:hidden;
  background:#0d0d0d;
  font-family:'ArabicFont','Noto Sans Arabic','Arial Unicode MS',sans-serif;
  direction:rtl;text-align:right;
}}
.grid{{
  position:absolute;inset:0;
  background:repeating-linear-gradient(90deg,#0f0f0f 0,#0f0f0f 1px,transparent 1px,transparent 50px);
}}
.bar{{position:absolute;top:0;left:0;right:0;height:5px;background:{accent};}}
.wrap{{
  position:absolute;inset:0;
  padding:44px 54px 36px;
  display:flex;flex-direction:column;justify-content:space-between;
}}
.top{{display:flex;justify-content:space-between;align-items:center;}}
.tag{{
  background:#1c0b08;border:1px solid {accent}66;color:{accent};
  font-size:17px;font-weight:500;padding:7px 18px;border-radius:6px;
}}
.cat{{color:#555;font-size:16px;}}
.title{{
  font-size:{ftitle}px;font-weight:700;
  color:#f0ede8;line-height:1.6;
  margin:26px 0 18px;
}}
.line{{width:50px;height:3px;background:{accent};border-radius:2px;margin:0 0 20px auto;}}
.body{{font-size:{fbody}px;font-weight:400;color:#999;line-height:1.75;}}
.bot{{border-top:1px solid #1e1e1e;padding-top:16px;}}
.sev{{
  display:inline-block;background:#141414;border:1px solid;
  font-size:17px;font-weight:500;padding:6px 16px;
  border-radius:6px;margin-bottom:14px;
}}
.foot{{display:flex;justify-content:space-between;align-items:center;}}
.handle{{color:#444;font-size:16px;}}
.date{{color:#444;font-size:16px;}}
</style></head><body>
<div class="grid"></div>
<div class="bar"></div>
<div class="wrap">
  <div>
    <div class="top">
      <div class="tag">OffsecAR</div>
      <div class="cat">{category}</div>
    </div>
    <div class="title">{title}</div>
    <div class="line"></div>
    <div class="body">{short}</div>
  </div>
  <div class="bot">
    {sev_block}
    <div class="foot">
      <div class="handle">{foot_handle}</div>
      <div class="date">{date_str}</div>
    </div>
  </div>
</div>
</body></html>"""


async def _pw_screenshot(html: str, out: Path, w: int, h: int):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox","--disable-gpu"])
        page = await browser.new_page(viewport={"width": w, "height": h})
        await page.set_content(html, wait_until="domcontentloaded")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(out))
        await browser.close()


def _render(html: str, out: Path, w: int, h: int):
    try:
        asyncio.run(_pw_screenshot(html, out, w, h))
    except Exception as e:
        print(f"⚠️ {e}")
        _fallback(out, w, h)


def _fallback(out: Path, w: int, h: int):
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (w, h), "#0d0d0d")
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w, 5], fill="#e03c2a")
        img.save(out, "PNG")
    except:
        out.write_bytes(b"")


# ── تحميل الخط مرة واحدة ──
_FONT_PATH = _find_arabic_font()
_FONT_FACE = _font_face(_FONT_PATH)


def make_twitter(title, category, severity, cvss, excerpt, date_str, out: Path):
    accent = SEV_COLORS.get(severity, CAT_COLORS.get(category, "#e03c2a"))
    html = _build_html(title, category, severity, cvss, excerpt, date_str,
                       1080, 1080, accent, "@OffsecAR", _FONT_FACE)
    _render(html, out, 1080, 1080)
    return out


def make_linkedin(title, category, excerpt, date_str, out: Path):
    accent = CAT_COLORS.get(category, "#4e9de8")
    html = _build_html(title, category, "", "", excerpt, date_str,
                       1200, 627, accent, "linkedin.com/company/OffsecAR", _FONT_FACE)
    _render(html, out, 1200, 627)
    return out


def make_whatsapp(title, category, excerpt, date_str, out: Path):
    html = _build_html(title, category, "", "", excerpt, date_str,
                       800, 800, "#25d366", "@OffsecAR", _FONT_FACE)
    _render(html, out, 800, 800)
    return out


def create_blog_image_svg(title, category, slug, images_dir: Path):
    date_str = datetime.now(timezone.utc).strftime("%d %b %Y")
    make_twitter(title, category, "", "", title, date_str, images_dir/f"{slug}-tw.png")
    make_linkedin(title, category, title, date_str, images_dir/f"{slug}-li.png")
    make_whatsapp(title, category, title, date_str, images_dir/f"{slug}-wa.png")
    return images_dir/f"{slug}-tw.png"


def create_news_image_svg(headline, category, severity, cvss, images_dir, date_str):
    make_twitter(headline, category, severity, cvss, headline, date_str, images_dir/f"{date_str}-tw.png")
    make_linkedin(headline, category, headline, date_str, images_dir/f"{date_str}-li.png")
    make_whatsapp(headline, category, headline, date_str, images_dir/f"{date_str}-wa.png")
    return images_dir/f"{date_str}-tw.png"
