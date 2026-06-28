import os
import time
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

# التوكن الخاص بك
API_TOKEN = '8804295788:AAE1AAeotpbHF5cz6N27UMVlXzFWQPD3gRE'
bot = telebot.TeleBot(API_TOKEN, num_threads=15)

DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

print_lock = threading.Lock()

def format_number(num):
    """تنسيق الأرقام الكبيرة لتظهر بشكل جذاب (مثل 1.2M أو 500K)"""
    if not num: return "0"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)

def process_tiktok_thread(message, url, status_msg):
    video_path = None
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', 
            'outtmpl': f'{DOWNLOAD_DIR}/tk_{message.chat.id}_{int(time.time())}.%(ext)s',
            'no_warnings': True,
            'quiet': True,
            'merge_output_format': 'mp4',
            'postprocessor_args': {
                'merger': ['-vcodec', 'libx264', '-acodec', 'aac', '-movflags', 'faststart', '-pix_fmt', 'yuv420p']
            },
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'referer': 'https://www.tiktok.com/',
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            
            # استخراج البيانات التحليلية المتقدمة مثل البوت المطلوب تماماً
            title = info.get('title', 'TikTok Video')
            duration = info.get('duration', 0)
            width = info.get('width')
            height = info.get('height')
            uploader = info.get('uploader', 'Unknown')
            uploader_id = info.get('uploader_id', '')
            
            # الإحصائيات
            view_count = format_number(info.get('view_count', 0))
            like_count = format_number(info.get('like_count', 0))
            comment_count = format_number(info.get('comment_count', 0))
            repost_count = format_number(info.get('repost_count', 0))
            
        bot.edit_message_text("🚀 **اكتملت المعالجة الفولاذية! جاري الرفع...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
        
        if not video_path.endswith('.mp4'):
            base, _ = os.path.splitext(video_path)
            os.rename(video_path, base + '.mp4')
            video_path = base + '.mp4'

        # تجهيز نص الوصف الغني بالإحصائيات والمعلومات
        caption_text = (
            f"👤 **المستخِدم:** [{uploader}](https://www.tiktok.com/@{uploader_id})\n"
            f"📝 **الوصف:** {title}\n\n"
            f"📊 **الإحصائيات:**\n"
            f"👁‍🗨 المشاهدات: `{view_count}`  |  ❤️ الإعجابات: `{like_count}`\n"
            f"💬 التعليقات: `{comment_count}`  |  🔄 المشاركات: `{repost_count}`\n\n"
            f"✨ تم التحميل بأعلى جودة وبدون علامة مائية بواسطة بوتك."
        )

        # إنشاء الأزرار التفاعلية أسفل الفيديو (تحميل الصوت منفصل)
        markup = InlineKeyboardMarkup()
        # نقوم بتمرير رابط الفيديو في البيانات ليعرف البوت أي صوت يسحب عند الضغط
        markup.add(InlineKeyboardButton("🎵 تحميل الصوت (MP3) 🎵", callback_data=f"audio|{url}"))

        with open(video_path, 'rb') as video:
            bot.send_video(
                chat_id=message.chat.id,
                video=video,
                caption=caption_text,
                duration=int(duration) if duration else None,
                width=width,   
                height=height, 
                supports_streaming=True,
                reply_markup=markup,
                reply_to_message_id=message.message_id,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        bot.delete_message(message.chat.id, status_msg.message_id)
            
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text("❌ **فشل جلب المقطع!** تأكد من أن الرابط صحيح والمقطع ليس خاصاً أو محذوفاً.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
    finally:
        if video_path and os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('audio|'))
def handle_audio_download(call):
    """دالة مخصصة لتحميل الصوت فقط وتحويله لـ MP3 عند ضغط المستخدم على الزر"""
    url = call.data.split('|')[1]
    # إرسال إشعار للمستخدم بأن جاري العمل
    bot.answer_callback_query(call.id, "📥 جاري استخراج الصوت النقي بصيغة MP3...")
    
    audio_path = None
    try:
        ydl_opts_audio = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_DIR}/audio_{call.message.chat.id}_{int(time.time())}.%(ext)s',
            'no_warnings': True,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        }
        
        with YoutubeDL(ydl_opts_audio) as ydl:
            info = ydl.extract_info(url, download=True)
            # بما أن الامتداد يتغير لـ mp3 تلقائياً بسبب الفلتر
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            audio_path = base + '.mp3'
            title = info.get('title', 'TikTok Audio')
            uploader = info.get('uploader', 'TikTok')

        with open(audio_path, 'rb') as audio:
            bot.send_audio(
                chat_id=call.message.chat.id,
                audio=audio,
                title=title,
                performer=uploader,
                reply_to_message_id=call.message.message_id
            )
    except Exception as e:
        print(f"Audio Error: {e}")
        bot.send_message(call.message.chat.id, "❌ نعتذر، فشل استخراج ملف الصوت لهذا المقطع.")
    finally:
        if audio_path and os.path.exists(audio_path):
            try: os.remove(audio_path)
            except: pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **مرحباً بك في بوت تيك توك الاحترافي الشامل الفولاذي!**\n\n"
        "أرسل لي أي رابط فيديو من تيك توك وسأقوم بـ:\n"
        "🔹 تحميل الفيديو بجودته الأصلية الـ HD وبدون علامة مائية.\n"
        "🔹 استخراج وتحليل إحصائيات المقطع الكاملة (إعجابات، مشاهدات، إلخ).\n"
        "🔹 توفير زر خاص لتحميل الصوت الأصلي للمقطع بصيغة MP3 نقية.\n\n"
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
