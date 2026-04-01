---
layout: blog
title: "Frida: أداة التحليل الديناميكي لاختراق واختبار التطبيقات على أنظمة التشغيل المختلفة"
date: 2026-04-01T06:26:41Z
category: "أداة"
excerpt: "Frida تمثل نقلة نوعية في مجال Dynamic Instrumentation، حيث تتيح لك التحكم الكامل بسلوك التطبيقات أثناء التشغيل. سواء كنت تختبر أمان تطبيق Android أو تحلل Binary على Windows، فإن Frida تمنحك القدرة على Hook الدوال وتعديل السلوك دون إعادة الترجمة. هذه المقالة تستعرض كيفية استخدام Frida عملياً في سيناريوهات Offensive Security الحقيقية."
read_time: 8
tags: ["Frida", "Dynamic Analysis", "Mobile Security", "Reverse Engineering", "Penetration Testing"]
slug: "frida-dynamic-analysis"
image: "/OffsecAR/assets/images/blogs/frida-dynamic-analysis.png"
---

## ما هي Frida ولماذا تهم المختبر الأمني؟

Frida هي إطار عمل مفتوح المصدر لـ Dynamic Instrumentation، تسمح لك بحقن JavaScript في عمليات تعمل على iOS وAndroid وWindows وmacOS وLinux. القوة الحقيقية لـ Frida تكمن في قدرتها على تعديل سلوك التطبيقات في الوقت الفعلي دون الحاجة للشيفرة المصدرية أو إعادة التصنيف.

على عكس أدوات Static Analysis، تتيح لك Frida رؤية ما يحدث فعلياً أثناء التنفيذ. يمكنك اعتراض المكالمات الدالية، تعديل القيم المُرجعة، استخراج البيانات من الذاكرة، وحتى تجاوز آليات الحماية مثل SSL Pinning وRoot Detection.

## بنية Frida وآلية العمل

تتكون Frida من مكونين رئيسيين:

**Frida Server**: يعمل على الجهاز المستهدف (الهاتف، الجهاز الافتراضي، أو النظام المستهدف) ويكون مسؤولاً عن حقن الكود في العمليات.

**Frida Client**: يعمل على جهازك ويتواصل مع Server عبر TCP. يمكنك استخدام Python API أو Command-line tools مثل `frida` و`frida-trace`.

عندما تستهدف عملية معينة، يقوم Frida بحقن مكتبة ديناميكية (Gadget) في مساحة عنوان العملية. بعدها، يمكنك تنفيذ JavaScript code يتفاعل مع Runtime الخاص بالتطبيق، سواء كان Dalvik/ART على Android أو Native code على منصات أخرى.

## سيناريو عملي: تجاوز Root Detection

لنأخذ مثالاً واقعياً: تطبيق بنكي يكتشف Root ويرفض العمل. نريد تحديد الدالة المسؤولة وتعديل سلوكها.

أولاً، نبحث عن الدوال المشبوهة:

```bash
frida-trace -U -f com.bank.app -i '*root*' -i '*Root*'
```

هذا الأمر يبدأ التطبيق ويعترض أي دالة تحتوي على كلمة "root". بعد تحديد الدالة المستهدفة، نكتب Script بسيط:

```javascript
Java.perform(function() {
    var RootDetection = Java.use('com.bank.security.RootDetection');
    
    RootDetection.isRooted.implementation = function() {
        console.log('[+] isRooted() called - Bypassing!');
        return false; // دائماً نرجع false
    };
    
    console.log('[*] Root detection bypassed successfully');
});
```

نحفظ Script في ملف `bypass.js` ونشغله:

```bash
frida -U -f com.bank.app -l bypass.js --no-pause
```

الآن التطبيق يعتقد أن الجهاز غير مكسور الصلاحيات.

## تقنيات متقدمة: Hooking Native Functions

التطبيقات الحديثة تستخدم Native libraries (C/C++) لتنفيذ العمليات الحساسة. Frida تتيح لك Hook هذه الدوال أيضاً:

```javascript
Interceptor.attach(Module.findExportByName('libnative.so', 'validateLicense'), {
    onEnter: function(args) {
        console.log('[+] validateLicense called');
        console.log('[+] License key: ' + Memory.readUtf8String(args[0]));
    },
    onLeave: function(retval) {
        console.log('[+] Original return value: ' + retval);
        retval.replace(1); // نغير القيمة لـ 1 (valid)
        console.log('[+] Modified to: ' + retval);
    }
});
```

هذا Script يعترض دالة `validateLicense` في مكتبة Native، يعرض المفتاح المُمرر لها، ثم يعدل القيمة المُرجعة لتكون دائماً صحيحة.

## استخراج البيانات من الذاكرة

أحد أقوى استخدامات Frida هو استخراج البيانات الحساسة من الذاكرة. مثلاً، لاستخراج مفاتيح التشفير:

```javascript
Java.perform(function() {
    var SecretKeySpec = Java.use('javax.crypto.spec.SecretKeySpec');
    
    SecretKeySpec.$init.overload('[B', 'java.lang.String').implementation = function(key, algorithm) {
        console.log('[+] Encryption key detected!');
        console.log('[+] Algorithm: ' + algorithm);
        console.log('[+] Key (hex): ' + bytesToHex(key));
        
        return this.$init(key, algorithm);
    };
});

function bytesToHex(bytes) {
    var hex = '';
    for(var i = 0; i < bytes.length; i++) {
        hex += ('0' + (bytes[i] & 0xFF).toString(16)).slice(-2);
    }
    return hex;
}
```

## نصائح عملية للاستخدام الاحترافي

**استخدم Frida-Server المناسب**: تأكد من تطابق إصدار Server مع Client وarchitecture الجهاز المستهدف (arm64، x86، إلخ).

**تعامل مع Anti-Frida**: بعض التطبيقات تكتشف وجود Frida عبر فحص Ports أو أسماء Processes. استخدم تقنيات مثل إعادة تسمية Server أو استخدام Frida Gadget المدمج.

**استفد من Frida Codeshare**: مجتمع Frida يوفر Scripts جاهزة لسيناريوهات شائعة على https://codeshare.frida.re - لا حاجة لإعادة اختراع العجلة.

**دمج Frida مع Burp Suite**: يمكنك استخدام Frida لتجاوز SSL Pinning ثم تحليل Traffic عبر Burp، وهو Workflow قياسي في Mobile Pentesting.

**احترس من Detection**: التطبيقات الحساسة تستخدم آليات معقدة للكشف عن Instrumentation. فهم كيفية عمل هذه الآليات أساسي لتجاوزها بنجاح.

Frida ليست مجرد أداة، بل منصة كاملة تفتح آفاقاً واسعة في Reverse Engineering وPentesting. إتقانها يتطلب فهماً عميقاً لـ Application Runtime وMemory Management، لكن العائد يستحق الاستثمار.
