# telegram_forwarder_bot/config.py

# --- إعدادات حساب تيليجرام (Telethon Client) ---
# هذه البيانات ضرورية لتشغيل البوت كـ "مستخدم" ليتمكن من قراءة القنوات الخاصة.
# يجب على المستخدم الحصول عليها من https://my.telegram.org
API_ID = 35705851  # استبدل هذا برقم API ID الخاص بك
API_HASH = "cd7109880bb4b9cbb5282f16415df285"  # استبدل هذا برمز API Hash الخاص بك

# --- إعدادات البوت (Bot API) ---
# هذا التوكن خاص بالبوت الذي تم إنشاؤه عبر BotFather
BOT_TOKEN = "8583413219:AAEcxZ_87oRIMcf_iPiIZeM-rZIeLp8M4T8"  # استبدل هذا بتوكن البوت الخاص بك

# --- إعدادات قاعدة البيانات ---
DB_NAME = "forwarder_bot.db"

# --- إعدادات الحقوق والترجمة ---
# الحقوق المخصصة التي سيتم إضافتها في نهاية الرسالة
CUSTOM_FOOTER = "\n\nModed by @melo00n\nJoin @melo0n3"

# اللغة المستهدفة للترجمة
TARGET_LANG = "ar"

# التأخير الافتراضي بين الرسائل المحولة (بالثواني)
DEFAULT_DELAY = 3

# --- قائمة الكلمات المفتاحية لاستثناء الترجمة (أسماء الألعاب/التطبيقات) ---
# هذه القائمة يمكن توسيعها لاحقاً عبر واجهة التحكم
EXCLUDED_WORDS = [
    "PSP", "PPSSPP", "APK", "ISO", "CSO", "Android", "iOS", "FIFA", "PES",
    "God of War", "Tekken", "GTA", "Efootball", "WWE", "2K", "Netflix"
]
