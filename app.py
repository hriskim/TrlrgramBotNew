import os
import requests
import telebot
from flask import Flask, request, abort
import logging

# Включаем подробное логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")  
SETUP_TOKEN = os.getenv("SETUP_TOKEN", "")        

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# Глобальная переменная для хранения последнего сообщения
last_message = None

@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"🎯 START command from: {message.from_user.first_name}")
    try:
        response = bot.reply_to(message, "✅ Я запущен на Render (webhook). Работаю корректно!")
        logger.info(f"✅ START reply sent: {response}")
    except Exception as e:
        logger.error(f"❌ Error sending START reply: {e}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.info(f"💬 Message: '{message.text}' from {message.from_user.first_name}")
    global last_message
    last_message = message.text
    
    try:
        response = bot.reply_to(message, f"🔁 Вы сказали: {message.text}")
        logger.info(f"✅ ECHO reply sent successfully, message_id: {response.message_id}")
    except Exception as e:
        logger.error(f"❌ Error sending ECHO reply: {e}")

@app.post(f"/webhook/{TOKEN}")
def tg_webhook():
    logger.info("🔄 Processing webhook request...")
    
    # проверяем секретный заголовок от Telegram
    if WEBHOOK_SECRET and request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        logger.error("❌ Invalid secret token")
        abort(403)
    
    if request.get_data():
        try:
            json_data = request.get_data().decode('utf-8')
            logger.debug(f"📦 Raw data: {json_data[:200]}...")
            
            update = telebot.types.Update.de_json(json_data)
            bot.process_new_updates([update])
            logger.info("✅ Message processed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error processing update: {e}")
            return "error", 500
    
    return "ok", 200

@app.get("/")
def health():
    return f"✅ Бот работает! Последнее сообщение: {last_message or 'нет'}", 200

@app.get("/init")
def init():
    if SETUP_TOKEN and request.args.get("token") != SETUP_TOKEN:
        abort(403)
    
    proto = request.headers.get("X-Forwarded-Proto", "https")
    host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host")
    
    if not host:
        return "Error: Cannot determine host", 500
    
    url = f"{proto}://{host}/webhook/{TOKEN}"

    params = {"url": url}
    if WEBHOOK_SECRET:
        params["secret_token"] = WEBHOOK_SECRET
    
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", json=params)
        result = r.json()
        logger.info(f"🌐 Webhook set: {result}")
        return {
            "status": "success" if result.get("ok") else "error",
            "url": url,
            "response": result
        }, 200
    except Exception as e:
        logger.error(f"❌ Webhook setup error: {e}")
        return {"error": str(e)}, 500

@app.get("/webhook-info")
def webhook_info():
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo")
        return r.json(), 200
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
