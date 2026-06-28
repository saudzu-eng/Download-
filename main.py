import os
import time
import threading
import telebot
from yt_dlp import YoutubeDL
import instaloader

API_TOKEN = '8804295788:AAE1AAeotpbHF5cz6N27UMVlXzFWQPD3gRE'
bot = telebot.TeleBot(API_TOKEN, num_threads=12)

DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

INSTA_USERNAME = 'YOUR_INSTAGRAM_USERNAME' 
INSTA_PASSWORD = 'YOUR_INSTAGRAM_PASSWORD'

L = instaloader.Instaloader(dirname_pattern=DOWNLOAD_DIR)
try:
    if INSTA_USERNAME != 'YOUR_INSTAGRAM_USERNAME':
        L.login(INSTA_USERNAME, INSTA_PASSWORD)
        print("✅ تم تسجيل الدخول بنجاح إلى انستجرام!")
except Exception as e:
    print(f"⚠️ تحذير انستجرام: {e}")

print_lock = threading.Lock()

def progress_hook(d, status_msg, chat_id):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        
        if total > 0:
            percent = (downloaded / total) * 100
            speed = d.get('speed', 0) or 0
            speed_mb = speed / (1024 * 1024)
            
            bar = '🟩' * int(percent // 10) + '⬜' * (10 - int(percent // 10))
            text = f"📥 **جاري معالجة وتحميل المقطع...**\n\n{bar} `{percent:.1f}%`\n⚡ السرعة: `{speed_mb:.2f} MB/s`"
            
            with print_lock:
                current_time = time.time()
                if not hasattr(progress_hook, "last_update_dict"):
                    progress_hook.last_update_dict = {}
                if current_time - progress_hook.last_update_dict.get(chat_id, 0) > 3.0:
                    try:
                        bot.edit_message_text(text, chat_id, status_msg.message_id, parse_mode='Markdown')
                        progress_hook.last_update_dict[chat_id] = current_time
                    except: pass

def process_video_thread(message, url, status_msg):
    video_path = None
    try:
        # حل مشكلة الستوريات
        if "instagram.com/stories/" in url:
            bot.edit_message_text("📸 **جاري سحب الستوري...**", message.chat.id, status_msg.message_id)
            parts = url.split("instagram.com/stories/")[1].split("/")
            insta_user = parts[0]
            profile = instaloader.Profile.from_username(L.context, insta_user)
            files = []
            for story in L.get_stories(userids=[profile.userid]):
                for item in story.get_items():
                    L.download_storyitem(item, target=insta_user)
                    for file in os.listdir(DOWNLOAD_DIR):
                        if file.startswith(item.date_utc.strftime('%Y-%m-%d')) and file.endswith(('.mp4', '.jpg')):
                            files.append(os.path.join(DOWNLOAD_DIR, file))
            
            if not files:
                bot.edit_message_text("❌ لم يتم العثور على ستوريات عامة نشطة لهذا الحساب.", message.chat.id, status_msg.message_id)
                return
                
            for f in files:
                with open(f, 'rb') as media:
                    if f.endswith('.mp4'): bot.send_video(message.chat.id, media)
                    else: bot.send_photo(message.chat.id, media)
                os.remove(f)
            bot.delete_message(message.chat.id, status_msg.message_id)
            return

        # إعدادات متطورة جداً لحل مشكلة الصوت والتعليق والحظر
        ydl_opts = {
            # التعديل الذهبي: اختيار أفضل جودة مدمجة صوت وصورة بصيغة mp4 مباشرة لضمان الصوت
            'format': 'best[ext=mp4]/bestvideo+bestaudio/best',
            'outtmpl': f'{DOWNLOAD_DIR}/vid_{message.chat.id}_{int(time.time())}.%(ext)s',
            'no_warnings': True,
            'quiet': True,
            # إضافة بيانات متصفح حقيقي لتخطي حظر تيك توك وانستجرام وسناب
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
            'progress_hooks': [lambda d: progress_hook(d, status_msg, message.chat.id)],
            'ext': 'mp4', # إجبار الصيغة لتكون متوافقة مع مشغلات التليجرام بدون تعليق
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            title = info.get('title', 'Video')
            duration = info.get('duration', 0)
            
        bot.edit_message_text("🚀 **اكتمل التحميل! جاري الرفع إلى تليجرام...**", message.chat.id, status_msg.message_id)
        
        # التأكد من الصيغة لتجنب تعليق الفيديو في المشغل
        if not video_path.endswith('.mp4'):
            base, _ = os.path.splitext(video_path)
            os.rename(video_path, base + '.mp4')
            video_path = base + '.mp4'

        file_size = os.path.getsize(video_path) / (1024 * 1024)
        if file_size > 49:
            bot.edit_message_text("⚠️ حجم الفيديو كبير، جاري ضبط الحجم تلقائياً...", message.chat.id, status_msg.message_id)
            os.remove(video_path)
            ydl_opts['format'] = 'worst[ext=mp4]/worst'
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)

        with open(video_path, 'rb') as video:
            bot.send_video(
                chat_id=message.chat.id,
                video=video,
                caption=f"🎬 **{title}**\n\n✨ تم التحميل بنجاح.",
                duration=int(duration) if duration else None,
                supports_streaming=True,
                reply_to_message_id=message.message_id,
                parse_mode='Markdown'
            )
        bot.delete_message(message.chat.id, status_msg.message_id)
            
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text("❌ **عذراً، فشل تحميل هذا الرابط!**\n\nقد يكون الحساب خاصاً، أو أن السيرفر محظور مؤقتاً من هذه المنصة.", message.chat.id, status_msg.message_id)
    finally:
        if video_path and os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👑 **مرحباً بك في بوت التحميل المطور!**\n\nأرسل الرابط مباشرة (تيك توك، يوتيوب، سناب، انستجرام) وسأقوم بمعالجته فوراً.", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    url = message.text
    if not url.startswith(('http://', 'https://')): return
    status_msg = bot.reply_to(message, "🔍 جاري فحص الرابط والاتصال بالسيرفر...")
    t = threading.Thread(target=process_video_thread, args=(message, url, status_msg))
    t.start()

if __name__ == '__main__':
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
