import telebot
import requests

API_TOKEN = '8804295788:AAE1AAeotpbHF5cz6N27UMVlXzFWQPD3gRE'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(func=lambda message: "tiktok.com" in message.text)
def handle_tiktok(message):
    url = message.text
    # إرسال رسالة "جاري المعالجة"
    msg = bot.reply_to(message, "⏳ جاري استخراج رابط الفيديو...")
    
    try:
        # هذا الـ API من أقوى المصادر حالياً ولا يتطلب بروكسي
        api = f"https://api.douyin.wtf/api?url={url}"
        response = requests.get(api, timeout=10).json()
        
        # التأكد من نجاح العملية
        if response.get('status') == 'success':
            video_url = response['video_data']['nwm_video_url_HQ']
            
            # إرسال الفيديو مباشرة من الرابط (تليجرام سيقوم بالتحميل من تيك توك للسيرفر الخاص به)
            bot.delete_message(message.chat.id, msg.message_id)
            bot.send_video(message.chat.id, video_url, caption="✅ تم التحميل بنجاح!")
        else:
            bot.edit_message_text("❌ لم يتم العثور على الفيديو. تأكد من الرابط.", message.chat.id, msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ: {str(e)}", message.chat.id, msg.message_id)

bot.infinity_polling()
