import asyncio
import re
import os
from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
from googletrans import Translator
from config import API_ID, API_HASH, BOT_TOKEN, TARGET_LANG, EXCLUDED_WORDS
from db import Database

# --- إعدادات العميل والبوت ---
client = TelegramClient('session_name', API_ID, API_HASH)
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
db = Database()
translator = Translator()

# --- وظيفة الترجمة المتقدمة (كما في المرحلة 4) ---
def translate_text(text, target_lang=TARGET_LANG):
    # 1. تحديد الكلمات التي يجب استثناؤها من الترجمة
    placeholders = {}
    temp_text = text
    
    for i, word in enumerate(EXCLUDED_WORDS):
        pattern = r'\b' + re.escape(word) + r'\b'
        placeholder = f"__PLACEHOLDER_{i}__"
        
        if re.search(pattern, temp_text, re.IGNORECASE):
            placeholders[placeholder] = word
            temp_text = re.sub(pattern, placeholder, temp_text, flags=re.IGNORECASE)

    # 2. الترجمة
    try:
        if temp_text.strip() and any(c.isalpha() for c in temp_text):
            translated_result = translator.translate(temp_text, dest=target_lang)
            translated_text = translated_result.text
        else:
            translated_text = temp_text
    except Exception as e:
        print(f"Translation Error: {e}")
        translated_text = text

    # 3. إعادة الكلمات المستثناة
    for placeholder, original_word in placeholders.items():
        translated_text = translated_text.replace(placeholder, original_word)
        
    return translated_text

# --- وظيفة معالجة النص (إزالة الروابط واليوزرات وإضافة الحقوق) ---
def process_text(text):
    footer = db.get_setting('custom_footer')
    
    # 1. إزالة الروابط (URLs)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # 2. إزالة يوزرات تيليجرام (@username)
    text = re.sub(r'@\w+', '', text)
    
    # 3. إزالة المسافات الزائدة
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 4. إضافة الحقوق
    return text + footer

# --- وظيفة معالجة الرسالة وتحويلها ---
async def forward_message(message):
    target_channel_id = db.get_setting('target_channel_id')
    if not target_channel_id:
        print("Target channel ID is not set.")
        return False
        
    # 1. استخراج النص
    text = message.text or message.caption
    
    # 2. معالجة النص (ترجمة + تعديل الحقوق)
    new_text = ""
    if text:
        translated_text = translate_text(text)
        new_text = process_text(translated_text)

    # 3. تطبيق التأخير
    delay = int(db.get_setting('default_delay'))
    await asyncio.sleep(delay)
    
    # 4. إرسال الرسالة
    try:
        if message.media:
            file_path = await message.download_media()
            
            await bot.send_file(
                int(target_channel_id),
                file_path,
                caption=new_text,
                force_document=True if isinstance(message.media, MessageMediaDocument) else False
            )
            
            os.remove(file_path)
            
        elif new_text:
            await bot.send_message(int(target_channel_id), new_text)
            
        print(f"Forwarded message {message.id} from {message.chat_id} to {target_channel_id}")
        return True
    except Exception as e:
        print(f"Error forwarding message {message.id}: {e}")
        return False

# --- معالج الأحداث (Event Handler) ---
@client.on(events.NewMessage)
async def handler_new_message(event):
    # تجاهل الرسائل المرسلة من البوت نفسه
    if event.is_private or event.is_group:
        return

    # تحقق من حالة البوت
    if db.get_setting('bot_status') != 'Running':
        return

    # الحصول على القنوات النشطة
    active_channels = db.get_active_channels()
    
    for channel_id, last_message_id in active_channels:
        if event.chat_id == channel_id and event.message.id > last_message_id:
            
            success = await forward_message(event.message)
            
            if success:
                db.update_last_message_id(channel_id, event.message.id)
            
            break

# --- واجهة التحكم (لوحة الإدارة) ---

# وظيفة إنشاء لوحة التحكم الرئيسية
def get_main_menu():
    status = db.get_setting('bot_status')
    status_text = "🟢 يعمل" if status == 'Running' else "🔴 متوقف"
    
    return [
        [Button.inline(f"حالة البوت: {status_text}", data='status')],
        [Button.inline("تشغيل البوت", data='start_bot'), Button.inline("إيقاف البوت", data='stop_bot')],
        [Button.inline("إدارة القنوات المصدر", data='manage_sources')],
        [Button.inline("إعدادات التأخير والحقوق", data='settings')],
        [Button.inline("إعداد قناة الهدف", data='set_target')]
    ]

# معالج أمر /start
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond("مرحباً بك في لوحة تحكم بوت النسخ المتقدم.\n\nيرجى استخدام الأزرار أدناه لإدارة البوت.", buttons=get_main_menu())

# معالج الأزرار المضمنة (Inline Buttons)
@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    
    if data == 'start_bot':
        db.set_setting('bot_status', 'Running')
        await event.edit("تم تشغيل البوت بنجاح. سيبدأ النسخ الآن.", buttons=get_main_menu())
    
    elif data == 'stop_bot':
        db.set_setting('bot_status', 'Stopped')
        await event.edit("تم إيقاف البوت بنجاح. لن يتم نسخ أي رسائل جديدة.", buttons=get_main_menu())
        
    elif data == 'manage_sources':
        channels = db.get_all_channels()
        text = "قنوات المصدر الحالية:\n"
        if channels:
            for _, name, active in channels:
                status = "✅" if active else "❌"
                text += f"- {status} {name}\n"
        else:
            text += "لا توجد قنوات مصدر مضافة بعد."
            
        await event.edit(text, buttons=[
            [Button.inline("إضافة قناة جديدة", data='add_source')],
            [Button.inline("حذف قناة", data='remove_source')],
            [Button.inline("▶️ العودة للقائمة الرئيسية", data='main_menu')]
        ])
        
    elif data == 'settings':
        delay = db.get_setting('default_delay')
        footer = db.get_setting('custom_footer')
        await event.edit(f"إعدادات البوت الحالية:\n\n**التأخير:** {delay} ثواني\n**الحقوق:** {footer}", buttons=[
            [Button.inline("تغيير التأخير", data='change_delay')],
            [Button.inline("تغيير الحقوق", data='change_footer')],
            [Button.inline("▶️ العودة للقائمة الرئيسية", data='main_menu')]
        ])
        
    elif data == 'set_target':
        target_id = db.get_setting('target_channel_id')
        await event.edit(f"معرف قناة الهدف الحالية: `{target_id}`\n\n**لتغيير قناة الهدف:**\n1. أضف البوت كمسؤول في قناتك.\n2. أرسل لي معرف القناة (Channel ID) أو اسم المستخدم (@username) الخاص بها.", buttons=[
            [Button.inline("▶️ العودة للقائمة الرئيسية", data='main_menu')]
        ])
        
    elif data == 'main_menu':
        await event.edit("القائمة الرئيسية:", buttons=get_main_menu())
        
    # يجب إضافة معالجات لإضافة وحذف القنوات وتغيير الإعدادات النصية (تتطلب حالة انتظار)
    # سيتم تبسيطها هنا لتجنب تعقيد حالة الانتظار في هذا المثال
    
    else:
        await event.answer("غير مدعوم حالياً.")

# --- وظيفة تشغيل البوت ---
async def main():
    print("Starting Telethon client...")
    await client.start()
    
    # يجب على المستخدم تسجيل الدخول أولاً
    if not await client.is_user_authorized():
        print("User not authorized. Please run the script once to log in.")
        # هنا يجب أن يتم طلب رقم الهاتف ورمز التحقق
        # لكن في بيئة Sandbox، سنفترض أن المستخدم سيقوم بذلك يدوياً أو أن الجلسة موجودة.
        
    print("Client is running. Listening for new messages...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    # يجب تشغيل البوت في حلقة الأحداث
    try:
        print("Starting Bot API...")
        bot.run_until_disconnected()
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    finally:
        db.close()
        # يجب فصل العميل والبوت بشكل صحيح
        # client.loop.run_until_complete(client.disconnect())
        # client.loop.run_until_complete(bot.disconnect())
