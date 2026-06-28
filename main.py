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
    if not num: return "0"
    if num >= 1_000_000: return f"{num / 1_000_000:.1f}M"
    if num >= 1_000: return f"{num / 1_000:.1f}K"
    return str(num)

def process_tiktok_thread(message, url, status_msg):
    video_path = None
    try:
        # الإعدادات الفولاذية الجديدة لتخطي حظر السيرفرات (Anti-Bot Bypass)
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', 
            'outtmpl': f'{DOWNLOAD_DIR}/tk_{message.chat.id}_{int(time.time())}.%(ext)s',
            'no_warnings': True,
            'quiet': True,
            'merge_output_format': 'mp4',
            
            # إصلاح التقطيع
            'postprocessor_args': {
                'merger': ['-vcodec', 'libx264', '-acodec', 'aac', '-movflags', 'faststart', '-pix_fmt', 'yuv420p']
            },
            
            # 🛠️ دمج ترويسات تطبيق تيك توك الرسمي لخداع الفلتر وتجنب الحظر
            'user_agent': 'com.zhiliaoapp.musically/2022603030 (Linux; U; Android 12; en_US; POCO F3; Build/SP1A.210812.016; Cronet/TTNetVersion:53f4a3de 2022-04-26 QuicVersion:4690623a 2022-04-19)',
            'headers': {
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'ar-AE,en-US;q=0.9',
                'X-Seconds-Sign': 'none',
            },
            'extractor_args': {
                'tiktok': {
                    'api_hostname': 'api16-normal-c-useast1a.tiktokv.com', # استخدام سيرفر تطبيق الهاتف بدلاً من موقع الويب
                    'app_version': '26.3.3',
                    'manifest_app_name': 'aweme',
                }
            },
            'nocheckcertificate': True,
            'ignoreerrors': True,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                # محاولة ثانية سريعة بإعدادات مخففة جداً في حال فشل السيرفر الأول
                ydl_opts['user_agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1'
                info = ydl.extract_info(url, download=True)
                
            video_path = ydl.prepare_filename(info)
            title = info.get('title', 'TikTok Video')
            duration = info.get('duration', 0)
            width = info.get('width')
            height = info.get('height')
            uploader = info.get('uploader', 'Unknown')
            uploader_id = info.get('uploader_id', '')
            
            view_count = format_number(info.get('view_count', 0))
            like_count = format_number(info.get('like_count', 0))
            comment_count = format_number(info.get('comment_count', 0))
            repost_count = format_number(info.get('repost_count', 0))
            
        bot.edit_message_text("🚀 **اكتملت المعالجة بنجاح! جاري الرفع...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
        
        if not video_path.endswith('.mp4'):
            base, _ = os.path.splitext(video_path)
            os.rename(video_path, base + '.mp4')
            video_path = base + '.mp4'

        caption_text = (
            f"👤 **المستخِدم:** [{uploader}](https://www.tiktok.com/@{uploader_id})\n"
            f"📝 **الوصف:** {title}\n\n"
            f"📊 **الإحصائيات:**\n"
            f"👁‍🗨 المشاهدات: `{view_count}`  |  ❤️ الإعجابات: `{like_count}`\n"
            f"💬 التعليقات: `{comment_count}`  |  🔄 المشاركات: `{repost_count}`\n\n"
            f"✨ بدون علامة مائية وبأعلى جودة HD."
        )

        markup = InlineKeyboardMarkup()
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
        bot.edit_message_text("❌ **فشل جلب المقطع من خوادم تيك توك!**\n\nالرابط قد يكون غير صحيح، أو المقطع تم حذفه أو تقييده.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
    finally:
        if video_path and os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('audio|'))
def handle_audio_download(call):
    url = call.data.split('|')[1]
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
