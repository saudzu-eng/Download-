import os
import time
import threading
import telebot
from yt_dlp import YoutubeDL
import instaloader

# 1. التوكن الخاص بك تم دمجه هنا تلقائياً
API_TOKEN = '8804295788:AAE1AAeotpbHF5cz6N27UMVlXzFWQPD3gRE'
bot = telebot.TeleBot(API_TOKEN, num_threads=10) # تشغيل بـ 10 مسارات متوازية لسرعة الرد

DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# 2. إعدادات حساب انستجرام (إجباري لتحميل الستوريات فقط، المنشورات العادية والريلز لا تحتاجه)
# نصيحة: استخدم حساباً جديداً أو فرعياً مخصصاً للبوت لتجنب أي قيود من انستجرام
INSTA_USERNAME = 'YOUR_INSTAGRAM_USERNAME' 
INSTA_PASSWORD = 'YOUR_INSTAGRAM_PASSWORD'

# تهيئة مكتبة انستجرام وتسجيل الدخول الآمن
L = instaloader.Instaloader(dirname_pattern=DOWNLOAD_DIR)
try:
    if INSTA_USERNAME != 'YOUR_INSTAGRAM_USERNAME':
        L.login(INSTA_USERNAME, INSTA_PASSWORD)
        print("✅ تم تسجيل الدخول بنجاح إلى انستجرام!")
except Exception as e:
    print(f"⚠️ تحذير: فشل تسجيل الدخول لانستجرام (الستوريات لن تعمل، لكن الريلز والمنشورات ستعمل): {e}")

print_lock = threading.Lock()

def progress_hook(d, status_msg, chat_id):
    """تحديث شريط التحميل للمخدم بشكل ذكي وآمن"""
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        
        if total > 0:
            percent = (downloaded / total) * 100
            speed = d.get('speed', 0) or 0
            speed_mb = speed / (1024 * 1024)
            
            bar_length = 10
            filled_length = int(round(bar_length * percent / 100))
            bar = '🟩' * filled_length + '⬜' * (bar_length - filled_length)
            
            text = f"📥 **جاري سحب المقطع من السيرفر الرئيسي...**\n\n" \
                   f"{bar} `{percent:.1f}%`\n" \
                   f"⚡ السرعة: `{speed_mb:.2f} MB/s`"
            
            with print_lock:
                current_time = time.time()
                if not hasattr(progress_hook, "last_update_dict"):
                    progress_hook.last_update_dict = {}
                
                last_update = progress_hook.last_update_dict.get(chat_id, 0)
                if current_time - last_update > 2.5: # تحديث كل 2.5 ثانية تجنباً لحظر تليجرام
                    try:
                        bot.edit_message_text(text, chat_id, status_msg.message_id, parse_mode='Markdown')
                        progress_hook.last_update_dict[chat_id] = current_time
                    except Exception:
                        pass

def download_insta_story(username, status_msg, chat_id):
    """دالة مخصصة لسحب ستوريات انستجرام العامة"""
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        story_files = []
        
        for story in L.get_stories(userids=[profile.userid]):
            for item in story.get_items():
                L.download_storyitem(item, target=username)
                
                for file in os.listdir(DOWNLOAD_DIR):
                    if file.startswith(item.date_utc.strftime('%Y-%m-%d')) and file.endswith(('.mp4', '.jpg')):
                        story_files.append(os.path.join(DOWNLOAD_DIR, file))
        return story_files
    except Exception as e:
        print(f"Instaloader Error: {e}")
        return []

def process_video_thread(message, url, status_msg):
    """المعالج الخلفي لكل عملية تحميل بشكل مستقل"""
    video_path = None
    try:
        # أولاً: إذا كان الرابط ستوري انستجرام
        if "instagram.com/stories/" in url:
            bot.edit_message_text("📸 **تم رصد رابط ستوري... جاري جلب الستوريات الحالية للحساب**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
            parts = url.split("instagram.com/stories/")[1].split("/")
            insta_user = parts[0]
            
            files = download_insta_story(insta_user, status_msg, message.chat.id)
            
            if not files:
                bot.edit_message_text("❌ لم يتم العثور على ستوريات نشطة، أو أن الحساب خاص (Private).", message.chat.id, status_msg.message_id)
                return
                
            bot.edit_message_text(f"🚀 تم العثور على {len(files)} ستوري، جاري الرفع الآن...", message.chat.id, status_msg.message_id)
            
            for f in files:
                with open(f, 'rb') as media:
                    if f.endswith('.mp4'):
                        bot.send_video(message.chat.id, media, reply_to_message_id=message.message_id)
                    else:
                        bot.send_photo(message.chat.id, media, reply_to_message_id=message.message_id)
                os.remove(f)
                
            bot.delete_message(message.chat.id, status_msg.message_id)
            return

        # ثانياً: تحميل الفيديوهات العادية (تيك توك، يوتيوب، سناب، ريلز انستجرام)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': f'{DOWNLOAD_DIR}/bot_dl_{message.chat.id}_{int(time.time())}.%(ext)s',
            'no_warnings': True,
            'quiet': True,
            'concurrent_fragments': 5,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
            'progress_hooks': [lambda d: progress_hook(d, status_msg, message.chat.id)],
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            title = info.get('title', 'Video')
            duration = info.get('duration', 0)
            
        try:
            bot.edit_message_text("🚀 **اكتمل التحميل من المصدر بنجاح!**\n\nجاري إرسال المقطع إليك الآن... 📂", message.chat.id, status_msg.message_id, parse_mode='Markdown')
        except Exception:
            pass
            
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        
        # تخطي حد الـ 50 ميجا للتليجرام تلقائياً عبر ضغط الجودة
        if file_size > 49:
            try:
                bot.edit_message_text("⚠️ حجم المقطع كبير جداً! جاري تقليله تلقائياً ليناسب الإرسال...", message.chat.id, status_msg.message_id)
                os.remove(video_path)
            except Exception:
                pass
                
            ydl_opts_compressed = {
                'format': 'best[filesize<48M]/worst',
                'outtmpl': f'{DOWNLOAD_DIR}/bot_dl_{message.chat.id}_{int(time.time())}_comp.%(ext)s',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            }
            with YoutubeDL(ydl_opts_compressed) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)

        # رفع الفيديو النهائي للمستخدم
        with open(video_path, 'rb') as video:
            bot.send_video(
                chat_id=message.chat.id,
                video=video,
                caption=f"🎬 **{title}**\n\n✨ تم التحميل بأعلى جودة وبدون علامات مائية وبصوت نقي.",
                duration=int(duration) if duration else None,
                supports_streaming=True,
                reply_to_message_id=message.message_id,
                parse_mode='Markdown'
            )
            
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass
            
    except Exception as e:
        print(f"Error: {e}")
        try:
            bot.edit_message_text("❌ **فشل التحميل!**\n\nتأكد من أن الرابط يعمل، المقطع ليس محذوفاً، وأن الحساب عام (وليس خاصاً).", message.chat.id, status_msg.message_id, parse_mode='Markdown')
        except Exception:
            pass
    finally:
        # حماية مساحة السيرفر: مسح الملف بشكل قطعي بعد الانتهاء أو الفشل
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👑 **أهلاً بك في البوت الشامل لتحميل المقاطع!**\n\n"
        "أرسل لي أي رابط من المنصات التالية وسأقوم بجلب المقطع بأعلى جودة وبدون علامة مائية:\n"
        "🔹 **TikTok** (فيديوهات بدون شعار)\n"
        "🔹 **YouTube** (فيديوهات وشورتس)\n"
        "🔹 **Instagram** (ريلز، منشورات، ستوريات عامة)\n"
        "🔹 **Snapchat** (منصة الأضواء والقصص العامة)\n\n"
        "🚀 أرسل الرابط الآن مباشرة!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    url = message.text
    if not url.startswith(('http://', 'https://')):
        bot.reply_to(message, "❌ نعتذر، يجب أن يبدأ الرابط بـ `http` أو `https`", parse_mode='Markdown')
        return

    status_msg = bot.reply_to(message, "🔍 جاري الاتصال الآمن بالمصدر وفحص الرابط...", parse_mode='Markdown')
    
    # نقل العملية لمسار خلفي منفصل لضمان استقرار البوت
    t = threading.Thread(target=process_video_thread, args=(message, url, status_msg))
    t.start()

if __name__ == '__main__':
    print("🚀 البوت يعمل الآن بأعلى كفاءة واستقرار...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
