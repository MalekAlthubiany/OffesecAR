#!/usr/bin/env python3
"""مولّد صور PNG عبر HTML → Screenshot"""

import os, subprocess, tempfile
from pathlib import Path
from datetime import datetime, timezone


def _html_to_png(html: str, out: Path, width: int, height: int):
    """يحول HTML لـ PNG عبر chromium headless"""
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w",
                                     encoding="utf-8", delete=False) as f:
        f.write(html)
        tmp_html = f.name

    cmd = [
        "chromium-browser", "--headless", "--no-sandbox",
        "--disable-gpu", "--disable-dev-shm-usage",
        f"--window-size={width},{height}",
        f"--screenshot={out}",
        f"file://{tmp_html}"
    ]
    # جرب chromium أو chromium-browser أو google-chrome
    for browser in ["chromium-browser", "chromium", "google-chrome", "google-chrome-stable"]:
        try:
            cmd[0] = browser
            subprocess.run(cmd, capture_output=True, timeout=30, check=True)
            Path(tmp_html).unlink(missing_ok=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    Path(tmp_html).unlink(missing_ok=True)
    return False


CAT_COLORS = {
    "منهجية": "#e03c2a", "تقنية": "#e8884e", "أداة": "#4e9de8",
    "تحليل": "#7ec845", "ثغرة حرجة": "#e03c2a", "تقنية هجوم": "#e8884e",
    "تهديد متقدم": "#e8c44e", "تحليل أخبار": "#7ec845",
    "الأمن الهجومي في الذكاء الاصطناعي": "#b44ee8",
}
SEV_COLORS = {"حرجة": "#e03c2a", "عالية": "#e8884e", "متوسطة": "#e8c44e"}

GOOGLE_FONTS = "https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@700&family=Noto+Sans+Arabic:wght@300;400;500;700&display=swap"


def _card_style(accent="#e03c2a", w=1080, h=1080):
    return f"""
<meta charset="UTF-8">
<link href="{GOOGLE_FONTS}" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:{w}px; height:{h}px; overflow:hidden;
  background:#0d0d0d;
  font-family:'Noto Sans Arabic',sans-serif;
  direction:rtl;
}}
.bg {{
  position:absolute; inset:0;
  background:repeating-linear-gradient(90deg,#111 0,#111 1px,transparent 1px,transparent 50px);
}}
.top-bar {{ position:absolute; top:0; left:0; right:0; height:5px; background:{accent}; }}
.card {{
  position:absolute; inset:0;
  padding:44px 54px 36px;
  display:flex; flex-direction:column; justify-content:space-between;
}}
.tag {{
  display:inline-flex; align-items:center;
  border:1px solid {accent}44; background:#1a0804;
  color:{accent}; font-size:17px; font-weight:500;
  padding:6px 18px; border-radius:6px;
  width:fit-content;
}}
.category {{ color:#555; font-size:17px; text-align:left; }}
.eyebrow {{ display:flex; justify-content:space-between; align-items:center; }}
.title {{
  font-family:'Noto Naskh Arabic',serif;
  font-size:52px; font-weight:700;
  color:#f0ede8; line-height:1.5;
  margin:28px 0 20px;
}}
.divider {{ width:50px; height:3px; background:{accent}; border-radius:2px; margin:0 0 22px auto; }}
.excerpt {{ font-size:28px; font-weight:300; color:#aaa; line-height:1.7; }}
.footer {{ border-top:1px solid #222; padding-top:16px; }}
.sev-badge {{
  display:inline-flex; align-items:center; gap:8px;
  background:#1a1a1a; border:1px solid {accent}55;
  color:{accent}; font-size:18px; font-weight:500;
  padding:7px 16px; border-radius:6px; margin-bottom:14px;
}}
.foot-row {{ display:flex; justify-content:space-between; align-items:center; }}
.handle {{ color:#444; font-size:17px; }}
.date {{ color:#444; font-size:17px; font-family:monospace; }}
</style>"""


def make_twitter(title, category, severity, cvss, excerpt, date_str, out: Path):
    accent = SEV_COLORS.get(severity, CAT_COLORS.get(category, "#e03c2a"))
    sev_html = ""
    if severity and severity not in ("","None"):
        sev_txt = f"خطورة {severity}"
        if cvss and cvss not in ("","None"):
            sev_txt += f"  ·  CVSS {cvss}"
        sev_html = f'<div class="sev-badge">{sev_txt}</div>'

    short = excerpt[:260] + ("..." if len(excerpt) > 260 else "")
    html = f"""<!DOCTYPE html><html><head>{_card_style(accent,1080,1080)}</head><body>
<div class="bg"></div><div class="top-bar"></div>
<div class="card">
  <div>
    <div class="eyebrow">
      <div class="tag">OffsecAR</div>
      <div class="category">{category}</div>
    </div>
    <div class="title">{title}</div>
    <div class="divider"></div>
    <div class="excerpt">{short}</div>
  </div>
  <div class="footer">
    {sev_html}
    <div class="foot-row">
      <div class="handle">@OffsecAR</div>
      <div class="date">{date_str}</div>
    </div>
  </div>
</div></body></html>"""

    if not _html_to_png(html, out, 1080, 1080):
        _fallback_png(title, out, 1080, 1080, accent)
    return out


def make_linkedin(title, category, excerpt, date_str, out: Path):
    accent = CAT_COLORS.get(category, "#4e9de8")
    short = excerpt[:220] + ("..." if len(excerpt) > 220 else "")
    html = f"""<!DOCTYPE html><html><head>{_card_style(accent,1200,627)}</head><body>
<div class="bg"></div><div class="top-bar"></div>
<div class="card">
  <div>
    <div class="eyebrow">
      <div class="tag">OffsecAR</div>
      <div class="category">{category}</div>
    </div>
    <div class="title" style="font-size:44px;margin:22px 0 16px;">{title}</div>
    <div class="divider"></div>
    <div class="excerpt" style="font-size:24px;">{short}</div>
  </div>
  <div class="footer">
    <div class="foot-row">
      <div class="handle">linkedin.com/company/OffsecAR</div>
      <div class="date">{date_str}</div>
    </div>
  </div>
</div></body></html>"""

    if not _html_to_png(html, out, 1200, 627):
        _fallback_png(title, out, 1200, 627, accent)
    return out


def make_whatsapp(title, category, excerpt, date_str, out: Path):
    accent = "#25d366"
    short = excerpt[:200] + ("..." if len(excerpt) > 200 else "")
    html = f"""<!DOCTYPE html><html><head>{_card_style(accent,800,800)}</head><body>
<div class="bg"></div>
<div style="position:absolute;top:0;left:0;bottom:0;width:5px;background:#25d366;"></div>
<div class="top-bar" style="background:#1a1a1a;"></div>
<div class="card" style="padding-right:44px;padding-left:24px;">
  <div>
    <div class="eyebrow">
      <div class="tag" style="border-color:#25d36644;color:#25d366;">OffsecAR</div>
      <div class="category">{category}</div>
    </div>
    <div class="title" style="font-size:40px;margin:22px 0 14px;">{title}</div>
    <div class="divider" style="background:#25d366;"></div>
    <div class="excerpt" style="font-size:24px;">{short}</div>
  </div>
  <div class="footer" style="border-color:#1a1a1a;">
    <div class="foot-row">
      <div class="handle" style="color:#333;">@OffsecAR</div>
      <div class="date" style="color:#333;">{date_str}</div>
    </div>
  </div>
</div></body></html>"""

    if not _html_to_png(html, out, 800, 800):
        _fallback_png(title, out, 800, 800, accent)
    return out


def _fallback_png(title, out, w, h, accent):
    """fallback بسيط لو فشل chromium"""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (w,h), "#0d0d0d")
        d = ImageDraw.Draw(img)
        d.rectangle([0,0,w,5], fill=accent)
        d.text((w//2, h//2), "OffsecAR", fill="#333333", anchor="mm")
        img.save(out, "PNG")
    except:
        out.write_bytes(b"")


# واجهات قديمة للتوافق
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
