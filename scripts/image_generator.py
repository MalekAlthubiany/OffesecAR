#!/usr/bin/env python3
"""مولّد صور Advisory — HTML → PNG عبر Playwright"""

import asyncio, tempfile
from pathlib import Path
from datetime import datetime, timezone

LOGO_PATH = Path('assets/images/logo.png')
SITE      = 'malekalthubiany.github.io/OffsecAR'

def _logo_src():
    # مسار مطلق للـ workflow
    for p in [
        Path('/home/runner/work/OffsecAR/OffsecAR/assets/images/logo.png'),
        Path('assets/images/logo.png'),
        LOGO_PATH,
    ]:
        if p.exists():
            return f'file://{p.resolve()}'
    return ''

def _build_html(title, category, severity, cvss, cve, desc, actions,
                fix, fix_sub, impact, impact_sub, vector, vector_sub,
                date_str, ref):

    logo_src = _logo_src()
    cvss_f   = float(cvss) if cvss and cvss not in ('', 'None') else 0
    cvss_w   = f'{min(cvss_f/10*100, 100):.0f}%'
    sev_color = '#b3261e' if severity in ('حرجة',) else '#d97c38' if severity == 'عالية' else '#888'

    actions_html = ''
    arabic_nums  = ['١','٢','٣','٤','٥','٦']
    for i, act in enumerate(actions):
        col = f'color:{sev_color};font-weight:600;' if i == 1 else ''
        num_col = sev_color if i == 1 else sev_color
        actions_html += f'''
        <div class="action-item">
          <span class="action-num" style="color:{num_col}">{arabic_nums[i]}.</span>
          <span class="action-text" style="{col}">{act}</span>
        </div>'''

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800;900&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:1040px;background:#f9f9f9;font-family:'Tajawal',sans-serif;direction:rtl;text-align:right;color:#1a1a1a;}}
.page{{padding:48px 52px;}}
.header{{display:flex;justify-content:space-between;align-items:center;padding-bottom:20px;border-bottom:1px solid #e0dcd6;margin-bottom:40px;}}
.header-date{{font-family:'IBM Plex Mono',monospace;font-size:13px;color:#999;direction:ltr;}}
.header-badge{{background:#1a1a1a;color:#f9f9f9;font-size:14px;font-weight:700;padding:7px 20px;border-radius:100px;}}
.main-title{{font-size:50px;font-weight:900;line-height:1.3;color:#111;margin-bottom:8px;}}
.main-sub{{font-size:24px;font-weight:400;color:#888;margin-bottom:24px;}}
.cve-bar{{display:flex;align-items:center;justify-content:space-between;background:{sev_color};color:#fff;padding:12px 20px;border-radius:6px;}}
.cve-num{{font-family:'IBM Plex Mono',monospace;font-size:15px;font-weight:500;direction:ltr;}}
.cve-sev{{font-size:15px;font-weight:700;display:flex;align-items:center;gap:8px;}}
.cve-dot{{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.7);}}
.sep{{border:none;border-top:1px solid #e0dcd6;margin:28px 0;}}
.section-label{{font-size:12px;font-weight:700;color:#bbb;letter-spacing:0.1em;margin-bottom:12px;}}
.desc-text{{font-size:20px;font-weight:400;color:#555;line-height:1.9;}}
.tech-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:16px;}}
.tech-card{{background:#fff;border:1px solid #ede9e3;border-radius:8px;padding:18px 20px;box-shadow:0 2px 8px rgba(0,0,0,0.04);}}
.tech-card-label{{font-size:12px;color:#bbb;font-weight:500;margin-bottom:8px;}}
.tech-card-value{{font-size:18px;font-weight:800;color:#111;margin-bottom:4px;}}
.tech-card-sub{{font-size:13px;color:#aaa;}}
.cvss-row{{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:10px;}}
.cvss-title{{font-size:12px;font-weight:700;color:#bbb;letter-spacing:0.1em;}}
.cvss-score{{font-size:60px;font-weight:900;color:{sev_color};line-height:1;direction:ltr;}}
.cvss-bar-bg{{height:8px;background:#e8e3dc;border-radius:4px;overflow:hidden;}}
.cvss-bar-fill{{height:100%;background:{sev_color};border-radius:4px;width:{cvss_w};}}
.cvss-meta{{display:flex;justify-content:space-between;margin-top:6px;}}
.cvss-meta span{{font-family:'IBM Plex Mono',monospace;font-size:12px;color:#bbb;direction:ltr;}}
.cvss-meta .active{{color:{sev_color};}}
.action-title{{font-size:18px;font-weight:800;color:{sev_color};margin-bottom:16px;}}
.actions-box{{background:rgba(179,38,30,0.03);border-right:3px solid {sev_color};border-radius:0 8px 8px 0;padding:20px 24px;}}
.action-item{{display:flex;align-items:baseline;gap:12px;padding:10px 0;border-bottom:1px solid rgba(0,0,0,0.04);font-size:19px;}}
.action-item:last-child{{border-bottom:none;padding-bottom:0;}}
.action-num{{color:{sev_color};font-weight:800;font-size:16px;min-width:22px;}}
.action-text{{color:#444;font-weight:400;line-height:1.6;}}
.footer{{margin-top:36px;padding-top:20px;border-top:1px solid #e0dcd6;display:flex;justify-content:space-between;align-items:center;}}
.footer-brand{{display:flex;align-items:center;gap:12px;}}
.footer-logo{{width:38px;height:38px;border-radius:7px;}}
.footer-info{{display:flex;flex-direction:column;gap:2px;}}
.footer-name{{font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:500;color:{sev_color};}}
.footer-handle{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#bbb;}}
.footer-meta{{text-align:left;}}
.footer-ref{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#ccc;display:block;direction:ltr;}}
</style></head><body><div class="page">
<div class="header">
  <span class="header-date">{date_str}</span>
  <span class="header-badge">تنبيه أمني</span>
</div>
<div class="main-title">{title}</div>
<div class="main-sub">{category}</div>
<div class="cve-bar">
  <span class="cve-num">{cve if cve and cve not in ('','None') else 'CVE غير محدد'}</span>
  <span class="cve-sev"><span class="cve-dot"></span> الخطورة: {severity}</span>
</div>
<hr class="sep">
<div class="section-label">الوصف</div>
<div class="desc-text">{desc}</div>
<hr class="sep">
<div class="section-label">التفاصيل التقنية</div>
<div class="tech-grid">
  <div class="tech-card"><div class="tech-card-label">التصحيح</div><div class="tech-card-value">{fix}</div><div class="tech-card-sub">{fix_sub}</div></div>
  <div class="tech-card"><div class="tech-card-label">التأثير</div><div class="tech-card-value">{impact}</div><div class="tech-card-sub">{impact_sub}</div></div>
  <div class="tech-card"><div class="tech-card-label">المتجه</div><div class="tech-card-value">{vector}</div><div class="tech-card-sub">{vector_sub}</div></div>
</div>
<hr class="sep">
<div class="cvss-row">
  <div class="cvss-title">تقييم الخطورة</div>
  <div class="cvss-score">{cvss if cvss and cvss not in ('','None') else '—'}</div>
</div>
<div class="cvss-bar-bg"><div class="cvss-bar-fill"></div></div>
<div class="cvss-meta">
  <span>CVSS 3.1  /  10.0</span>
  <span class="active">● نشط</span>
</div>
<hr class="sep">
<div class="action-title">إجراء مطلوب فوراً</div>
<div class="actions-box">{actions_html}</div>
<div class="footer">
  <div class="footer-brand">
    {'<img class="footer-logo" src="' + logo_src + '">' if logo_src else ''}
    <div class="footer-info">
      <span class="footer-name">OffsecAR</span>
      <span class="footer-handle">@OffsecAR  ·  {SITE}</span>
    </div>
  </div>
  <div class="footer-meta">
    <span class="footer-ref">{ref}</span>
    <span class="footer-ref">TLP: CLEAR</span>
  </div>
</div>
</div></body></html>"""


async def _shoot(html, out):
    from playwright.async_api import async_playwright
    with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
        f.write(html); tmp = f.name
    async with async_playwright() as p:
        br = await p.chromium.launch(args=['--no-sandbox','--disable-gpu'])
        pg = await br.new_page(viewport={'width':1040,'height':2000})
        await pg.goto(f'file://{tmp}', wait_until='networkidle')
        await pg.wait_for_timeout(2500)
        h = await pg.evaluate('document.body.scrollHeight')
        await pg.set_viewport_size({'width':1040,'height':h})
        await pg.screenshot(path=str(out), full_page=True)
        await br.close()
    Path(tmp).unlink(missing_ok=True)


def _render(html, out):
    try:
        asyncio.run(_shoot(html, Path(out)))
        print(f'   🖼  {Path(out).name}')
    except Exception as e:
        print(f'   ⚠️ {e}')


def make_advisory(title, category, severity, cvss, cve, desc,
                  actions, fix, fix_sub, impact, impact_sub,
                  vector, vector_sub, date_str, ref, out):
    html = _build_html(title, category, severity, cvss, cve, desc,
                       actions, fix, fix_sub, impact, impact_sub,
                       vector, vector_sub, date_str, ref)
    _render(html, out)
    return Path(out)


# ── واجهات التوافق مع السكريبتات الأخرى ──────────────────────

def make_twitter(title, category, severity, cvss, excerpt, date_str, out):
    actions = [
        'مراجعة الأنظمة المتأثرة فوراً',
        'تطبيق التحديثات الأمنية المتاحة',
        'مراقبة السجلات بحثاً عن نشاط مشبوه',
        'التواصل مع فريق الأمن الداخلي',
    ]
    cve = ''
    return make_advisory(title, category, severity, cvss, cve, excerpt,
                         actions, 'آخر إصدار', 'تحديث مطلوب',
                         'تنفيذ أوامر عن بعد', 'وصول غير مصرح',
                         'الشبكة', 'بدون مصادقة',
                         date_str, f'REF: OFFSEC-{date_str.replace("-","")}', out)


def make_linkedin(title, category, excerpt, date_str, out):
    return make_twitter(title, category, 'عالية', '', excerpt, date_str, out)


def make_whatsapp(title, category, excerpt, date_str, out):
    return make_twitter(title, category, 'عالية', '', excerpt, date_str, out)


def create_news_image_svg(headline, category, severity, cvss, images_dir, date_str):
    images_dir = Path(images_dir)
    out = images_dir / f'{date_str}-advisory.png'
    actions = [
        'مراجعة الأنظمة المتأثرة فوراً',
        'تطبيق التحديثات الأمنية المتاحة',
        'مراقبة السجلات بحثاً عن نشاط مشبوه',
        'عزل الأنظمة حتى اكتمال التحديث',
    ]
    make_advisory(headline, category, severity, cvss, '',
                  f'تم اكتشاف {headline}. الثغرة تؤثر على أنظمة متعددة وتستوجب التحرك الفوري.',
                  actions, 'آخر إصدار', 'تحديث فوري مطلوب',
                  'تنفيذ أوامر عن بعد', 'وصول كامل للنظام',
                  'الشبكة', 'بدون مصادقة',
                  date_str, f'REF: OFFSEC-{date_str.replace("-","")}', out)
    return out


def create_blog_image_svg(title, category, slug, images_dir):
    images_dir = Path(images_dir)
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out = images_dir / f'{slug}-advisory.png'
    actions = [
        'قراءة المقالة كاملة لفهم التقنية',
        'تطبيق المنهجية في بيئة اختبار',
        'مشاركة المعرفة مع فريقك',
        'متابعة OffsecAR لمزيد من المحتوى',
    ]
    make_advisory(title, category, '', '', '',
                  f'مقالة تقنية متخصصة في {category} — اقرأ التحليل الكامل على موقع OffsecAR.',
                  actions, 'مقالة جديدة', 'متاحة الآن',
                  'تقنية متقدمة', 'للمختصين',
                  'موقع OffsecAR', 'مجاني',
                  date_str, f'REF: BLOG-{date_str.replace("-","")}', out)
    return out
