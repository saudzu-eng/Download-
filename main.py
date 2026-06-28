import os
import time
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# التوكن الخاص بك
API_TOKEN = '8804295788:AAE1AAeotpbHF5cz6N27UMVlXzFWQPD3gRE'
bot = telebot.TeleBot(API_TOKEN, num_threads=15)

DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def format_number(num):
    if not num: return "0"
    try:
        num = int(num)
        if num >= 1_000_000: return f"{num / 1_000_000:.1f}M"
        if num >= 1_000: return f"{num / 1_000:.1f}K"
        return str(num)
    except:
        return str(num)

def process_tiktok_thread(message, url, status_msg):
    video_path = None
    try:
        # 🛠️ استخدام API وسيط خارجي لتخطي حظر تيك توك بالكامل وجلب الرابط المباشر
        api_url = f"https://tikwm.com/api/?url={url}"
        response = requests.get(api_url, timeout=15).json()
        
        if response.get('code') != 0:
            # محاولة باستخدام API بديل في حال فشل الأول
            api_url = f"https://www.tikwm.com/api/?url={url}"
            response = requests.get(api_url, timeout=15).json()
            
        if response.get('code') != 0:
            raise Exception("API Error")

        data = response['data']
        
        # استخراج البيانات والإحصائيات الحقيقية
        title = data.get('title', 'TikTok Video')
        video_url = data.get('play', '') # رابط الفيديو بدون علامة مائية
        music_url = data.get('music', '') # رابط الصوت المباشر
        
        uploader = data.get('author', {}).get('nickname', 'Unknown')
        uploader_id = data.get('author', {}).get('unique_id', '')
        
        view_count = format_number(data.get('play_count', 0))
        like_count = format_number(data.get('digg_count', 0))
        comment_count = format_number(data.get('comment_count', 0))
        repost_count = format_number(data.get('share_count', 0))
        duration = data.get('duration', 0)

        bot.edit_message_text("📥 **جاري سحب المقطع ومعالجة الجودة الأصلية...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

        # تحميل الفيديو إلى السيرفر مؤقتاً لتمرير الأبعاد الدقيقة وحل مشكلة التقطيع
        video_path = f"{DOWNLOAD_DIR}/tk_{message.chat.id}_{int(time.time())}.mp4"
        with requests.get(video_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(video_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        bot.edit_message_text("🚀 **اكتملت المعالجة بنجاح! جاري الرفع...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

        caption_text = (
            f"👤 **المستخِدم:** [{uploader}](https://www.tiktok.com/@{uploader_id})\n"
            f"📝 **الوصف:** {title}\n\n"
            f"📊 **الإحصائيات:**\n"
            f"👁‍🗨 المشاهدات: `{view_count}`  |  ❤️ الإعجابات: `{like_count}`\n"
            f"💬 التعليقات: `{comment_count}`  |  🔄 المشاركات: `{repost_count}`\n\n"
            f"✨ بدون علامة مائية وبأعلى جودة HD أصلية."
        )

        markup = InlineKeyboardMarkup()
        # نمرر رابط الموسيقى المباشر لتوفير استجابة سريعة جداً عند طلب الصوت
        markup.add(InlineKeyboardButton("🎵 تحميل الصوت (MP3) 🎵", callback_data=f"aud_dir|{music_url}"))

        with open(video_path, 'rb') as video:
            bot.send_video(
                chat_id=message.chat.id,
                video=video,
                caption=caption_text,
                duration=int(duration) if duration else None,
                supports_streaming=True, # يضمن تفعيل ميزة انسيابية التشغيل الفوري
                reply_markup=markup,
                reply_to_message_id=message.message_id,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        bot.delete_message(message.chat.id, status_msg.message_id)
            
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text("❌ **فشل جلب المقطع!**\n\nتأكد من أن الرابط صحيح، أو أن المقطع ليس خاصاً أو محذوفاً.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
    finally:
        if video_path and os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('aud_dir|'))
def handle_audio_direct(call):
    """رفع الصوت مباشرة وسرياً عبر رابط الـ MP3 المستخرج بدون استهلاك موارد السيرفر"""
    music_url = call.data.split('|')[1]
    bot.answer_callback_query(call.id, "📥 جاري إرسال الصوت النقي...")
    
    try:
        # إرسال الصوت مباشرة عبر الرابط دون الحاجة لتحميله وإعادة رفعه لتسريع العملية
        bot.send_audio(
            chat_id=call.message.chat.id,
            audio=music_url,
            title="TikTok Audio",
            performer="TikTok Bot",
            reply_to_message_id=call.message.message_id
        )
    except Exception as e:
        print(f"Audio Direct Error: {e}")
        bot.send_message(call.message.chat.id, "❌ نعتذر، فشل إرسال ملف الصوت لهذا المقطع.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **مرحباً بك في بوت تيك توك الاحترافي الشامل!**\n\n"
        "أرسل لي أي رابط فيديو من تيك توك وسأقوم بـ:\n"
        "🔹 تحميل الفيديو بجودته الأصلية الـ HD وبدون علامة مائية.\n"
        "🔹 استخراج وتحليل إحصائيات المقطع الكاملة.\n"
        "🔹 توفير زر خاص لتحميل الصوت الأصلي للمقطع بصيغة MP3 نقي.\n\n"
        "🚀 أرسل الرابط الآن ودعنا نبدأ!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    url = message.text
    if "tiktok.com" not in url:
        bot.reply_to(message, "⚠️ **من فضلك أرسل رابط تيك توك صحيح فقط!**", parse_mode='Markdown')
        return

    status_msg = bot.reply_to(message, "🔍 جاري الاتصال الآمن وسحب إحصائيات المقطع وفحص الجودة...", parse_mode='Markdown')
    t = threading.Thread(target=process_tiktok_thread, args=(message, url, status_msg))
    t.start()

if __name__ == '__main__':
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
