import os
import time
import threading
import telebot
from yt_dlp import YoutubeDL

# التوكن الخاص بك
API_TOKEN = '8804295788:AAE1AAeotpbHF5cz6N27UMVlXzFWQPD3gRE'
bot = telebot.TeleBot(API_TOKEN, num_threads=15)

DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

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
            text = f"📥 **جاري سحب المقطع ومعالجة الإطارات بدقة...**\n\n{bar} `{percent:.1f}%`\n⚡ السرعة: `{speed_mb:.2f} MB/s`"
            
            with print_lock:
                current_time = time.time()
                if not hasattr(progress_hook, "last_update_dict"):
                    progress_hook.last_update_dict = {}
                if current_time - progress_hook.last_update_dict.get(chat_id, 0) > 3.0:
                    try:
                        bot.edit_message_text(text, chat_id, status_msg.message_id, parse_mode='Markdown')
                        progress_hook.last_update_dict[chat_id] = current_time
                    except: pass

def process_tiktok_thread(message, url, status_msg):
    video_path = None
    try:
        # الإعدادات الخارقة لإصلاح التقطيع وتثبيت معدل الإطارات
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', 
            'outtmpl': f'{DOWNLOAD_DIR}/tk_{message.chat.id}_{int(time.time())}.%(ext)s',
            'no_warnings': True,
            'quiet': True,
            'merge_output_format': 'mp4',
            
            # 🛠️ التعديل السحري: إجبار ffmpeg على إعادة ترميز وتثبيت البث لمنع التقطيع (Fix Lag & Stutter)
            'postprocessor_args': {
                'merger': ['-vcodec', 'libx264', '-acodec', 'aac', '-movflags', 'faststart', '-pix_fmt', 'yuv420p']
            },
            
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'headers': {
                'Accept': 'video/webm,video/mp4,video/*;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
            },
            'referer': 'https://www.tiktok.com/',
            'progress_hooks': [lambda d: progress_hook(d, status_msg, message.chat.id)],
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            title = info.get('title', 'TikTok Video')
            duration = info.get('duration', 0)
            width = info.get('width')
            height = info.get('height')
            
        bot.edit_message_text("🚀 **اكتملت معالجة الفيديو بسلاسة! جاري الرفع...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
        
        if not video_path.endswith('.mp4'):
            base, _ = os.path.splitext(video_path)
            os.rename(video_path, base + '.mp4')
            video_path = base + '.mp4'

        with open(video_path, 'rb') as video:
            bot.send_video(
                chat_id=message.chat.id,
                video=video,
                caption=f"🎬 **{title}**\n\n✨ جودة HD أصلية - تشغيل سلس بدون تقطيع.",
                duration=int(duration) if duration else None,
                width=width,   
                height=height, 
                supports_streaming=True, # تشغيل فوري أثناء التحميل داخل تليجرام
                reply_to_message_id=message.message_id,
                parse_mode='Markdown'
            )
            
        bot.delete_message(message.chat.id, status_msg.message_id)
            
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text("❌ **فشل معالجة المقطع!**\n\nيرجى إعادة المحاولة مرة أخرى.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
    finally:
        if video_path and os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 **مرحباً بك في بوت تيك توك المطور ضد التقطيع!**\n\nأرسل الرابط الآن وسيقوم البوت بضبط إطارات المقطع ليعمل لديك بأعلى سلاسة ممكنة وبدون علامة مائية 🎬", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    url = message.text
    if "tiktok.com" not in url:
        bot.reply_to(message, "⚠️ **من فضلك أرسل رابط تيك توك صحيح فقط!**", parse_mode='Markdown')
        return

    status_msg = bot.reply_to(message, "🔍 جاري الاتصال الآمن وفحص دقة وإطارات الفيديو...", parse_mode='Markdown')
    t = threading.Thread(target=process_tiktok_thread, args=(message, url, status_msg))
    t.start()

if __name__ == '__main__':
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
