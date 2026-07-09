# 🩹 SmartStitch Discord Bot

بوت ديسكورد بيدمج ويقطع صور فصول المانجا/المانهوا (زي أداة [SmartStitch](https://github.com/MechTechnology/SmartStitch) الأصلية) بأمر واحد `/stitch`، وبيرفع الناتج تلقائيًا على جوجل درايف.

## ✨ المميزات

- أمر واحد بس: **`/stitch`**
- بيقبل الإدخال بأي طريقة من دول:
  1. رفع ملف **ZIP** مباشرة في الأمر
  2. لينك **ZIP** (مثلاً لينك ملف اترفع في ديسكورد)
  3. لينك **ملف ZIP على جوجل درايف**
  4. لينك **فولدر على جوجل درايف** فيه صور الفصل
- الإعدادات الافتراضية مضبوطة زي اللقطة اللي بعتها بالظبط:
  - الصيغة: `.jpg`
  - الجودة: `95%`
  - الارتفاع التقريبي للصورة: `12000px`
  - عرض ثابت للصور: `720px` (Manual Custom Width)
  - وتقدر تغيرهم وقت ما تستخدم الأمر لو حبيت (اختياري)
- بعد ما يخلص، بيعمل **فولدر على جوجل درايف بنفس اسم الفصل**، ويحط الصور الناتجة جواه، ويديك اللينك في زرار جاهز.
- **Progress Bar** حي بيتحدث لحظيًا جوه رسالة الديسكورد من أول ما يبدأ التحميل لحد ما يخلص الرفع.
- معالجة أخطاء واضحة بالعربي (ملف مش zip، لينك درايف غلط، الفولدر فاضي...إلخ).

---

## 📁 هيكل المشروع

```
smartstitch-bot/
├── bot.py                     ← نقطة تشغيل البوت + أمر /stitch
├── config.py                  ← تحميل الإعدادات من .env
├── requirements.txt
├── .env.example                ← انسخه وسمّيه .env واملأ بياناتك
├── core/                       ← مكتبة SmartStitch الأصلية (الدمج والتقطيع) بدون تعديل في المنطق
│   ├── detectors/
│   ├── models/
│   ├── services/
│   └── utils/
├── services/
│   ├── drive_service.py        ← التعامل مع Google Drive API (تحميل/رفع/مشاركة)
│   ├── input_resolver.py       ← تحديد مصدر الإدخال (رفع/لينك) وتجهيزه
│   ├── stitch_service.py       ← تشغيل عملية الدمج والتقطيع مع تقرير تقدّم
│   └── progress_view.py        ← بناء الـ Progress Bar داخل رسالة ديسكورد
└── utils/
    └── zip_utils.py            ← فك/ضغط الملفات بأمان
```

---

## 🚀 خطوات التشغيل

### 1) تثبيت المتطلبات

```bash
cd smartstitch-bot
python -m venv .venv
source .venv/bin/activate   # على ويندوز: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) إنشاء بوت الديسكورد

1. روح على https://discord.com/developers/applications وسوي **New Application**.
2. من تبويب **Bot** فعّل البوت وانسخ الـ **Token**.
3. من نفس الصفحة فعّل:
   - `Message Content Intent` (اختياري، مش ضروري للأوامر السلاش)
4. من تبويب **OAuth2 → URL Generator** اختار `bot` + `applications.commands`، وأدي البوت صلاحيات:
   - `Send Messages`, `Embed Links`, `Attach Files`, `Use Slash Commands`
5. افتح اللينك اللي هيتولد وضيف البوت لسيرفرك.

### 3) إعداد Google Drive API

⚠️ **ملحوظة مهمة:** لو حساب جوجل بتاعك حساب Gmail عادي (مش Google Workspace مدفوع)، **متستخدمش Service Account للرفع** — جوجل بتمنعه بخطأ `storageQuotaExceeded` لأن الـ Service Account مالوش مساحة تخزين خاصة بيه. الطريقة الصح لحساب Gmail عادي هي **OAuth** (البوت بيرفع الملفات باسمك إنت، وبتستخدم مساحة التخزين بتاعتك).

#### الطريقة الموصى بيها (OAuth) — لحساب Gmail عادي

1. روح على [Google Cloud Console](https://console.cloud.google.com/) وسوي مشروع جديد (أو استخدم موجود).
2. من **APIs & Services → Library** فعّل **Google Drive API**.
3. من **APIs & Services → OAuth consent screen**:
   - اختار **External**
   - املأ اسم التطبيق وإيميلك، واحفظ
   - في خطوة **Test users** ضيف إيميل جوجل بتاعك (نفس الحساب اللي هترفع عليه)
4. من **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - النوع: **Desktop app**
   - أنشئه ونزّل ملف الـ JSON
5. سمّي الملف `oauth_client.json` وحطه جنب `bot.py`.
6. شغّل الأمر ده **مرة واحدة بس** من نفس الجهاز (هيفتحلك المتصفح تسجل دخول وتوافق):
   ```bash
   python authorize_drive.py
   ```
   بعد الموافقة، هيتعمل ملف `token.json` أوتوماتيك — ده اللي البوت هيستخدمه بعد كده (وبيجدد نفسه لوحده، مش هتحتاج تكرر الخطوة دي).
7. كده خلاص، الفصول اللي هتتعمل هتتحط في **My Drive** بتاعك مباشرة.

#### الطريقة البديلة (Service Account) — لو عندك Google Workspace + Shared Drive

1. من **APIs & Services → Credentials → Create Credentials → Service Account** أنشئ Service Account.
2. من صفحة الـ Service Account، تبويب **Keys → Add Key → Create New Key → JSON**، وهينزلك ملف JSON.
3. سمّي الملف `service_account.json` وحطه جنب `bot.py`.
4. اعمل **Shared Drive** (مش فولدر عادي) من درايفك، وضيف إيميل الـ Service Account
   (شكله `xxx@xxx.iam.gserviceaccount.com`) كـ **Manager/Content Manager** جواه.
5. حط آيدي فولدر جوه الـ Shared Drive ده في `GOOGLE_DRIVE_PARENT_FOLDER_ID` بملف `.env`.
6. لو عندك `token.json` من الطريقة الأولى، امسحه أو سيب `GOOGLE_TOKEN_FILE` مش موجود عشان البوت يستخدم الـ Service Account.

### 4) ملف الإعدادات `.env`

```bash
cp .env.example .env
```

افتحه واملأ:
```
DISCORD_TOKEN=توكن_البوت
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
GOOGLE_DRIVE_PARENT_FOLDER_ID=آيدي_الفولدر_الرئيسي   # اختياري
```

### 5) تشغيل البوت

```bash
python bot.py
```

هيظهرلك في التيرمنال: `✅ البوت شغال باسم: ...`

---

## 🎮 طريقة الاستخدام

في أي روم البوت موجود فيها، اكتب:

```
/stitch
```

هتلاقي خيارين (اختار واحد منهم بس):
- **file**: ارفق ملف ZIP فيه صور الفصل
- **link**: حط لينك (ZIP من ديسكورد / ZIP من درايف / فولدر درايف فيه صور)

وفيه خيارات اختيارية لو حبيت تغيّر عن الإعدادات الافتراضية:
- `output_format` (jpg / png / webp)
- `quality` (1-100)
- `rough_height` (بالبكسل)
- `custom_width` (بالبكسل، حط 0 لتعطيل تثبيت العرض)

هيظهرلك **Progress Bar** بيتحدث لحظيًا، وفي الآخر هتاخد:
- ✅ رسالة نجاح فيها اسم الفصل وعدد الصور الناتجة
- 🔘 زرار **"افتح الفصل على درايف"** يودّيك على الفولدر مباشرة

---

## ⚙️ ملاحظات تقنية

- عملية الدمج والتقطيع بتستخدم نفس منطق SmartStitch الأصلي (Pixel Comparison Detector) لتحديد أفضل نقاط تقطيع تتفادى قص النص أو أي عنصر في نص الصورة.
- الملفات المؤقتة بتتحط في فولدر `temp_jobs/<job_id>` وبتتمسح تلقائيًا بعد كل عملية (نجحت أو فشلت).
- لو الملف اللي هترفعه/اللينك كبير جدًا وبياخد وقت، الـ Progress Bar هيفضل يتحدث لحد ما يخلص (البوت مش هيعمل timeout لأنه بيستخدم `interaction.edit_original_response`).
- تقدر تشغّل أكتر من `/stitch` في نفس الوقت من ناس مختلفة، كل عملية ليها فولدر مؤقت خاص بيها.

## 🛠️ مشاكل شائعة

| المشكلة | الحل |
|---|---|
| `ملف الـ Service Account مش موجود` | تأكد إن `service_account.json` موجود في نفس فولدر `bot.py` أو المسار مظبوط في `.env` |
| `مقدرتش أفهم لينك جوجل درايف ده` | تأكد إن اللينك لينك فولدر (`.../drive/folders/...`) أو لينك ملف (`.../file/d/...`) |
| الفولدر على درايف مبيرجعش صور | تأكد إنك شاركت الفولدر مع إيميل الـ Service Account |
| الأمر `/stitch` مش ظاهر في ديسكورد | استنى شوية بعد أول تشغيل (Discord بياخد وقت يعمل sync للأوامر)، أو اعمل Kick/Invite تاني للبوت بصلاحية `applications.commands` |

---

صنع بالاستعانة بمكتبة [SmartStitch](https://github.com/MechTechnology/SmartStitch) الأصلية (نفس منطق الدمج والتقطيع بدون تعديل).
