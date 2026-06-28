import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8804295788:AAE1AAeotpbHF5cz6N27UMVlXzFWQPD3gRE'
bot = telebot.TeleBot(API_TOKEN)

# 💡 ضع هنا أي رابط بروكسي مجاني (مثال: http://1.2.3.4:8080)
# ابحث في Google عن "Free HTTP Proxy list" وانسخ واحداً وضع الرابط هنا
PROXY_URL = 'http://123.456.78.90:8080' 

@bot.message_handler(func=lambda message: "tiktok.com" in message.text)
def handle_tiktok(message):
    url = message.text
    msg = bot.reply_to(message, "🔍 جاري الاتصال عبر البروكسي...")
    
    try:
        # إعداد البروكسي للاتصال
        proxies = {
            'http': PROXY_URL,
            'https': PROXY_URL,
        }
        
        api_url = f"https://tikwm.com/api/?url={url}"
        # الاتصال باستخدام البروكسي لتخطي الحظر
        response = requests.get(api_url, proxies=proxies, timeout=20).json()
        
        if response.get('code') == 0:
            data = response['data']
            # نستخدم .get(..., "") لتفادي خطأ 'hdplay'
            video_url = data.get('hdplay') or data.get('play', "")
            
            if video_url:
                bot.delete_message(message.chat.id, msg.message_id)
                bot.send_video(message.chat.id, video_url, caption="✅ تم جلب المقطع بنجاح!")
            else:
                bot.edit_message_text("❌ لم أجد رابط فيديو صالح.", message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ فشل الاتصال، البروكسي قد يكون معطلاً.", message.chat.id, msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ تقني: {str(e)}", message.chat.id, msg.message_id)

bot.infinity_polling()
