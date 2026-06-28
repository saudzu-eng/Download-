import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8804295788:AAE1AAeotpbHF5cz6N27UMVlXzFWQPD3gRE'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(func=lambda message: "tiktok.com" in message.text)
def handle_tiktok(message):
    url = message.text
    msg = bot.reply_to(message, "🔍 جاري الاتصال بخوادم تيك توك...")
    
    try:
        # استخدام API خارجي مستقر جداً
        api_url = f"https://tikwm.com/api/?url={url}"
        response = requests.get(api_url).json()
        
        if response['code'] == 0:
            data = response['data']
            video_url = data['hdplay'] or data['play']
            
            # محاولة إرسال الفيديو مباشرة عبر الرابط (لتجنب الحظر على السيرفر)
            bot.delete_message(message.chat.id, msg.message_id)
            bot.send_video(message.chat.id, video_url, caption="✅ تم جلب المقطع بنجاح!")
        else:
            bot.edit_message_text("❌ لم أتمكن من جلب الفيديو، حاول مرة أخرى.", message.chat.id, msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {str(e)}", message.chat.id, msg.message_id)

bot.infinity_polling()
