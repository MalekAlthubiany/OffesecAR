#!/usr/bin/env python3
"""مولّد صور PNG - خط Amiri العربي الكلاسيكي عبر Playwright"""

import asyncio, tempfile
from pathlib import Path
from datetime import datetime, timezone

CAT_COLORS = {
    "منهجية": "#e03c2a", "تقنية": "#e8884e", "أداة": "#4e9de8",
    "تحليل": "#7ec845", "ثغرة حرجة": "#e03c2a", "تقنية هجوم": "#e8884e",
    "تهديد متقدم": "#e8c44e", "تحليل أخبار": "#7ec845",
    "الأمن الهجومي في الذكاء الاصطناعي": "#b44ee8",
}
SEV_COLORS = {"حرجة": "#e03c2a", "عالية": "#e8884e", "متوسطة": "#e8c44e"}

FONTS = "https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Mono:wght@400&display=swap"


def _html(title, category, severity, cvss, excerpt, date_str, w, h, accent, handle):
    sev_block = ""
    if severity and severity not in ("", "None"):
        sc = SEV_COLORS.get(severity, "#e8884e")
        sev_txt = f"خطورة {severity}"
        if cvss and cvss not in ("", "None"):
            sev_txt += f"  ·  CVSS {cvss}"
        sev_block = f'''<div style="display:inline-flex;align-items:center;gap:8px;
            background:#110808;border:1px solid {sc}66;color:{sc};
            font-size:15px;font-weight:700;padding:7px 16px;border-radius:5px;margin-bottom:14px;">
            <span style="width:8px;height:8px;border-radius:50%;background:{sc};display:inline-block;"></span>
            {sev_txt}</div>'''

    words = title.split()
    lines = []
    cur = []
    for w_ in words:
        cur.append(w_)
        if len(cur) >= 5:
            lines.append(" ".join(cur)); cur = []
    if cur: lines.append(" ".join(cur))
    title_html = "".join(f'<div>{l}</div>' for l in lines[:3])

    exc_short = excerpt[:220] + ("..." if len(excerpt) > 220 else "")

    font_title = 52 if w >= 1080 else 44 if w >= 1000 else 38
    font_body  = 22 if w >= 1080 else 20 if w >= 1000 else 18

    return f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<link href="{FONTS}" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  width:{w}px;height:{h}px;overflow:hidden;
  background:#0a0a0a;
  font-family:'Amiri',serif;
  direction:rtl;text-align:right;
}}
.grid{{position:absolute;inset:0;
  background:repeating-linear-gradient(90deg,#0e0e0e 0,#0e0e0e 1px,transparent 1px,transparent 56px);}}
.bar{{position:absolute;top:0;left:0;right:0;height:3px;background:{accent};}}
.wrap{{position:absolute;inset:0;padding:36px 48px 32px;
  display:flex;flex-direction:column;justify-content:space-between;}}
.top{{display:flex;justify-content:space-between;align-items:center;}}
.tag{{background:none;border:1px solid {accent}99;color:{accent};
  font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:1px;
  padding:5px 14px;border-radius:4px;}}
.cat{{color:#3d3d3d;font-size:17px;font-style:italic;}}
.sep{{border:none;border-top:1px solid #181818;margin:16px 0;}}
.title{{font-size:{font_title}px;font-weight:700;color:#f0ede8;
  line-height:1.5;margin:18px 0 10px;}}
.accent-line{{width:44px;height:2px;background:{accent};border-radius:1px;
  margin:0 0 18px auto;}}
.callig-swash{{
  border:none;border-top:none;
  color:{accent};font-size:11px;opacity:0.2;
  text-align:left;letter-spacing:3px;margin:4px 0 14px;
  font-family:'IBM Plex Mono',monospace;
}}
.body{{font-size:{font_body}px;font-weight:400;color:#555;line-height:1.8;}}
.body-italic{{font-style:italic;color:#404040;font-size:{font_body-2}px;margin-top:6px;}}
.dots{{display:flex;flex-direction:column;gap:10px;position:absolute;right:16px;top:50%;transform:translateY(-50%);}}
.dot{{width:3px;height:3px;border-radius:50%;background:{accent};opacity:0.15;}}
.bot{{}}
.sep2{{border:none;border-top:1px solid #131313;margin-bottom:14px;}}
.foot{{display:flex;justify-content:space-between;align-items:center;}}
.handle{{color:#222;font-family:'IBM Plex Mono',monospace;font-size:11px;}}
.date{{color:#222;font-family:'IBM Plex Mono',monospace;font-size:11px;}}
.pulse{{width:7px;height:7px;border-radius:50%;background:{accent};opacity:0.9;}}
</style></head><body>
<div class="grid"></div>
<div class="bar"></div>
<div class="dots">
  <div class="dot"></div><div class="dot"></div>
  <div class="dot"></div><div class="dot"></div>
</div>
<div class="wrap">
  <div>
    <div class="top">
      <div class="tag">OffsecAR</div>
      <div class="cat">{category}</div>
    </div>
    <hr class="sep">
    <div class="title">{title_html}</div>
    <div class="accent-line"></div>
    <div class="body">{exc_short}</div>
  </div>
  <div class="bot">
    {sev_block}
    <hr class="sep2">
    <div class="foot">
      <div style="display:flex;align-items:center;gap:8px;">
        <div class="pulse"></div>
        <span class="handle">{handle}</span>
      </div>
      <div class="date">{date_str}</div>
    </div>
  </div>
</div>
</body></html>"""


async def _shoot(html, out, w, h):
    from playwright.async_api import async_playwright
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w",
                                      encoding="utf-8", delete=False) as f:
        f.write(html); tmp = f.name
    async with async_playwright() as p:
        br = await p.chromium.launch(args=["--no-sandbox","--disable-gpu"])
        pg = await br.new_page(viewport={"width":w,"height":h})
        await pg.goto(f"file://{tmp}", wait_until="networkidle")
        await pg.wait_for_timeout(2000)
        await pg.screenshot(path=str(out))
        await br.close()
    Path(tmp).unlink(missing_ok=True)


def _render(html, out, w, h):
    try:
        asyncio.run(_shoot(html, out, w, h))
        print(f"   🖼  {out.name}")
    except Exception as e:
        print(f"   ⚠️ {e}")
        _fallback(out, w, h)


def _fallback(out, w, h):
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (w,h), "#0a0a0a")
        ImageDraw.Draw(img).rectangle([0,0,w,3], fill="#e03c2a")
        img.save(out,"PNG")
    except: out.write_bytes(b"")


def make_twitter(title, category, severity, cvss, excerpt, date_str, out):
    accent = SEV_COLORS.get(severity, CAT_COLORS.get(category, "#e03c2a"))
    _render(_html(title,category,severity,cvss,excerpt,date_str,1080,1080,accent,"@OffsecAR"), Path(out),1080,1080)
    return Path(out)

def make_linkedin(title, category, excerpt, date_str, out):
    accent = CAT_COLORS.get(category, "#4e9de8")
    _render(_html(title,category,"","",excerpt,date_str,1200,627,accent,"linkedin.com/company/OffsecAR"), Path(out),1200,627)
    return Path(out)

def make_whatsapp(title, category, excerpt, date_str, out):
    _render(_html(title,category,"","",excerpt,date_str,800,800,"#25d366","@OffsecAR"), Path(out),800,800)
    return Path(out)

def create_blog_image_svg(title, category, slug, images_dir):
    images_dir = Path(images_dir)
    date_str = datetime.now(timezone.utc).strftime("%d %b %Y")
    make_twitter(title,category,"","",title,date_str,images_dir/f"{slug}-tw.png")
    make_linkedin(title,category,title,date_str,images_dir/f"{slug}-li.png")
    make_whatsapp(title,category,title,date_str,images_dir/f"{slug}-wa.png")
    return images_dir/f"{slug}-tw.png"

def create_news_image_svg(headline, category, severity, cvss, images_dir, date_str):
    images_dir = Path(images_dir)
    make_twitter(headline,category,severity,cvss,headline,date_str,images_dir/f"{date_str}-tw.png")
    make_linkedin(headline,category,headline,date_str,images_dir/f"{date_str}-li.png")
    make_whatsapp(headline,category,headline,date_str,images_dir/f"{date_str}-wa.png")
    return images_dir/f"{date_str}-tw.png"
