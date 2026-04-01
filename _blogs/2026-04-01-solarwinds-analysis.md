---
layout: blog
title: "تشريح هجوم SolarWinds: كيف اخترقت APT29 آلاف الشركات عبر Supply Chain Attack واحد"
date: 2026-04-01T04:53:41Z
category: "تحليل"
excerpt: "في ديسمبر 2020، اكتُشف أحد أخطر الهجمات السيبرانية في التاريخ. هجوم SolarWinds لم يكن مجرد اختراق عادي، بل كان عملية استخباراتية معقدة استهدفت سلسلة التوريد البرمجية. آلاف المؤسسات الحكومية والخاصة وجدت نفسها مخترقة دون أن تدري، والمهاجم كان داخل أنظمتهم لأشهر."
read_time: 8
tags: ["Supply Chain Attack", "APT Analysis", "Threat Hunting", "SolarWinds", "SUNBURST"]
slug: "solarwinds-analysis"
image: "/OffsecAR/assets/images/blogs/solarwinds-analysis.png"
---

## التشريح الفني للهجوم

استهدفت مجموعة APT29 (المعروفة بـ Cozy Bear) منصة Orion الخاصة بشركة SolarWinds. الهجوم بدأ بالتسلل إلى بيئة التطوير Build Environment الخاصة بالشركة، حيث تمكن المهاجمون من حقن backdoor داخل التحديثات الرسمية.

الـ payload الخبيث كان عبارة عن DLL باسم `SolarWinds.Orion.Core.BusinessLayer.dll` يحتوي على كود ضار مموّه ببراعة. هذا الملف تم توقيعه رقميًا بشهادة SolarWinds الشرعية، مما جعله يمر عبر كل أدوات الحماية دون اكتشاف.

```csharp
// المنطق المبسط للـ backdoor (SUNBURST)
public class OrionImprovementBusinessLayer
{
    private void Update()
    {
        // فترة سكون لمدة أسبوعين لتجنب الكشف
        if (GetCurrentTime() < installTime.AddDays(14))
            return;
        
        // التحقق من بيئة الضحية
        if (IsSecurityToolRunning() || IsDebuggerPresent())
            return;
            
        // Domain Generation Algorithm للاتصال بـ C2
        string c2Domain = GenerateDomain();
        ExecuteCommand(GetCommandFromC2(c2Domain));
    }
}
```

## سلسلة الإصابة: من Build Server إلى الضحية

المهاجمون اتبعوا منهجية دقيقة على مراحل. أولاً، اخترقوا بيئة التطوير في سبتمبر 2019. ثم زرعوا الـ backdoor في نسخة Orion 2019.4 حتى 2020.2.1 التي صدرت في مارس 2020.

حوالي 18,000 عميل قاموا بتحميل التحديث المصاب. لكن المهاجمين كانوا انتقائيين للغاية - فقط حوالي 100 مؤسسة تم استهدافها فعليًا في المرحلة الثانية.

الـ SUNBURST backdoor كان يتصل بخوادم C2 عبر تقنية DNS tunneling ذكية:

```python
# مثال على فك تشفير DNS subdomain المستخدم
def decode_sunburst_dns(subdomain):
    # SUNBURST كان يستخدم Base32 مخصص
    custom_alphabet = "ph2eifo3n5utg1j8d94qrvbmk0sal76c"
    
    decoded = ""
    for chunk in subdomain.split('.'):
        # فك التشفير وإرجاع البيانات المسربة
        data = base32_decode(chunk, custom_alphabet)
        decoded += data
    
    return {
        'domain': extract_domain(decoded),
        'username': extract_username(decoded),
        'ip': extract_ip(decoded)
    }
```

## التقنيات المتقدمة للتخفي

ما يميز هذا الهجوم هو مستوى الـ stealth المذهل. المهاجمون استخدموا:

**Dormancy Period**: فترة سكون 12-14 يوم بعد التثبيت لتجنب sandboxes.

**Environment Checks**: فحص دقيق لأدوات الأمن والتحليل قبل التنفيذ.

**Legitimate Infrastructure Abuse**: استخدام خدمات شرعية مثل AWS و GCP لإخفاء C2 traffic.

**CNAME Records Manipulation**: استخدام سجلات DNS CNAME بدلاً من A records لإخفاء البنية التحتية الحقيقية.

الـ indicators كانت ضئيلة جدًا. حتى أن الـ backdoor كان يحذف نفسه إذا اكتشف بيئة تحليل أو أدوات forensics محددة.

## Detection والـ Indicators الحرجة

اكتشاف الهجوم جاء متأخرًا من FireEye في ديسمبر 2020. الـ IOCs الرئيسية كانت:

```yaml
# Sigma Rule مبسطة للكشف عن SUNBURST
title: SolarWinds SUNBURST Backdoor DNS Request
status: critical
logsource:
  category: dns
detection:
  selection:
    query|contains:
      - '.avsvmcloud.com'
      - '.appsync-api.'
  condition: selection
fields:
  - query
  - answers
  - client_ip
```

العلامات الأخرى شملت:
- ملفات DLL بتواقيع زمنية مشبوهة
- Registry keys غير عادية تحت `HKEY_LOCAL_MACHINE\SOFTWARE\SolarWinds`
- Network connections إلى domains تبدو شرعية لكنها حديثة الإنشاء
- استخدام legitimate accounts بطرق غير معتادة (Credential Abuse)

## الدروس الاستراتيجية للـ Blue Teams

**أولاً**: Supply Chain Security لم تعد اختيارية. يجب تطبيق Software Bill of Materials (SBOM) لكل مكون في البنية التحتية.

**ثانياً**: Code Signing ليس ضماناً. حتى التوقيعات الشرعية يمكن استغلالها إذا تم اختراق البنية التحتية للتطوير.

**ثالثاً**: Network Segmentation الصارم. حتى لو تم الاختراق، يجب أن يكون الـ lateral movement صعباً قدر الإمكان.

**رابعاً**: Behavioral Analysis أهم من Signature-based Detection. الـ EDR يجب أن يركز على الأنماط غير الطبيعية، ليس فقط على signatures معروفة.

```bash
# مثال على hunting query للبحث عن anomalies
# في PowerShell commands من SolarWinds processes
DeviceProcessEvents
| where InitiatingProcessFileName == "SolarWinds.BusinessLayerHost.exe"
| where FileName in ("powershell.exe", "cmd.exe", "rundll32.exe")
| where ProcessCommandLine has_any ("Invoke", "WebClient", "EncodedCommand")
| project Timestamp, DeviceName, ProcessCommandLine, AccountName
```

الهجوم أثبت أن الـ Advanced Persistent Threats تطورت لمستوى جديد. لم يعد الدفاع عن محيط الشبكة كافياً. نحتاج إلى Zero Trust Architecture حقيقية، مع مراقبة مستمرة لكل مكون داخل البيئة، حتى لو كان من vendors موثوقين.
