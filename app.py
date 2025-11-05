import os
import requests
import telebot
from flask import Flask, request, abort
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")  
SETUP_TOKEN = os.getenv("SETUP_TOKEN", "")        

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"START from: {message.from_user.first_name}")
    bot.reply_to(message, "✅ Бот работает на Render!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.info(f"Message: {message.text}")
    bot.reply_to(message, f"🔁 Эхо: {message.text}")

@app.post(f"/webhook/{TOKEN}")
def tg_webhook():
    if WEBHOOK_SECRET and request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        abort(403)
    
    if request.get_data():
        json_data = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    
    return "ok", 200

@app.get("/")
def health():
    return "✅ Бот активен", 200

@app.get("/init")
def init():
    if SETUP_TOKEN and request.args.get("token") != SETUP_TOKEN:
        abort(403)
    
    proto = request.headers.get("X-Forwarded-Proto", "https")
    host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host")
    url = f"{proto}://{host}/webhook/{TOKEN}"
    
    params = {"url": url}
    if WEBHOOK_SECRET:
        params["secret_token"] = WEBHOOK_SECRET
    
    r = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", json=params)
    return r.json(), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
