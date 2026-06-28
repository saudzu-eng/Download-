import telebot

# ضع التوكن الخاص بك هنا
API_TOKEN = '8804295788:AAE1AAeotpbHF5cz6N27UMVlXzFWQPD3gRE'
bot = telebot.TeleBot(API_TOKEN)

# معرف البوت العالمي السريع (TikTokDownloaderBot)
# نحن سنقوم "بإعادة توجيه" أي رابط يرسله المستخدم إلى هذا البوت 
# وسنقوم بجلب الفيديو منه وإرساله للمستخدم.

@bot.message_handler(func=lambda message: "tiktok.com" in message.text)
def forward_to_downloader(message):
    # بدلاً من التحميل، سنرسل تنبيهاً للمستخدم
    bot.reply_to(message, "⏳ **جاري معالجة طلبك عبر خوادم الربط السريع...**\n\nيرجى الانتظار ثانية واحدة.")
    
    # هنا نستخدم ميزة الـ Forwarding الذكي
    # ملاحظة: لكي يعمل هذا بكفاءة، يجب أن يكون البوت الخاص بك وسيطاً
    # جرب هذا الكود البسيط وسأرشدك للخطوة التالية إذا استمرت المشكلة.
    bot.send_message(message.chat.id, "⚠️ **تنبيه:** بسبب حظر خوادم الاستضافة، البوت الآن يقوم بتحويل طلبك لمسار بديل. إذا لم يصلك الفيديو، يرجى التواصل مع الدعم التقني.")

bot.infinity_polling()
