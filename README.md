# OffsecAR

نظام نشر يومي تلقائي لأخبار Offensive Security بالعربي.

## كيف يعمل

```
كل يوم الساعة 8 صباحاً (الرياض)
     │
     ▼
🔍 يجمع أخبار من: Exploit-DB، BleepingComputer، NVD، HackerNews...
     │
     ▼
✍️  Claude يختار الخبر الأبرز ويكتبه بأسلوب ثمانية بالعربي
     │
     ▼
🎨  يصمم صورة 1080×1080 بأسلوب editorial داكن
     │
     ▼
🐦  ينشر على Twitter / X
     │
     ▼
📝  يضيف المنشور لموقع GitHub Pages
```

---

## الإعداد (خطوة بخطوة)

### 1. انشئ الريبو على GitHub
```bash
git clone https://github.com/YourUsername/OffsecAR
cd OffsecAR
```

### 2. فعّل GitHub Pages
- اذهب لـ Settings → Pages
- اختر: Source → **GitHub Actions**

### 3. أضف الـ Secrets
اذهب لـ Settings → Secrets and variables → Actions، أضف:

| Secret | القيمة |
|--------|--------|
| `ANTHROPIC_API_KEY` | مفتاح Anthropic |
| `TWITTER_API_KEY` | من developer.twitter.com |
| `TWITTER_API_SECRET` | من developer.twitter.com |
| `TWITTER_ACCESS_TOKEN` | من developer.twitter.com |
| `TWITTER_ACCESS_TOKEN_SECRET` | من developer.twitter.com |
| `TWITTER_HANDLE` | مثال: `@YourHandle` |

### 4. Twitter Developer Account
- اشترك في **Basic Plan** (~$100/شهر) — ضروري للنشر التلقائي
- أنشئ App وفعّل **Read and Write** permissions
- أنشئ Access Tokens

### 5. ارفع الكود
```bash
git add .
git commit -m "initial setup"
git push origin main
```

---

## تشغيل يدوي

من Actions → "نشر يومي" → **Run workflow**

---

## هيكل الملفات

```
OffsecAR/
├── .github/workflows/daily_post.yml   # الجدولة اليومية
├── scripts/daily_post.py              # السكريبت الرئيسي
├── _posts/                            # المنشورات (تُنشأ تلقائياً)
├── assets/images/                     # صور تويتر (تُنشأ تلقائياً)
├── _layouts/post.html                 # قالب المنشور
├── index.html                         # الصفحة الرئيسية
└── _config.yml                        # إعدادات Jekyll
```
