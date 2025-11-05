import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из переменных окружения
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Создаем бота и диспетчер
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Обработчики команд
def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    update.message.reply_html(
        f"Привет, {user.mention_html()}! 👋\n"
        f"Я простой телеграм бот, развернутый на Render.com\n\n"
        f"Доступные команды:\n"
        f"/start - начать работу\n"
        f"/help - помощь\n"
        f"/info - информация о боте"
    )

def help_command(update, context):
    """Обработчик команды /help"""
    update.message.reply_text(
        "Я могу ответить на следующие команды:\n\n"
        "/start - начать работу\n"
        "/help - показать эту справку\n"
        "/info - информация о боте\n\n"
        "Также я могу эхо-сообщения!"
    )

def info(update, context):
    """Обработчик команды /info"""
    update.message.reply_text(
        "🤖 Информация о боте:\n\n"
        "• Развернут на Render.com\n"
        "• Использует Python и python-telegram-bot\n"
        "• Исходный код на GitHub\n"
        "• Версия: 1.0"
    )

def echo(update, context):
    """Эхо-ответ на текстовые сообщения"""
    text = update.message.text
    update.message.reply_text(f"Вы сказали: {text}")

# Настройка обработчиков
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("info", info))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

# Создаем Flask приложение
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Эндпоинт для вебхука от Telegram"""
    if request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Установка вебхука (вызовите этот URL один раз после деплоя)"""
    webhook_url = os.environ.get('RENDER_EXTERNAL_URL') + '/webhook'
    
    if not webhook_url or webhook_url == '/webhook':
        return "Ошибка: RENDER_EXTERNAL_URL не установлен"
    
    success = bot.set_webhook(webhook_url)
    if success:
        return f"Вебхук установлен: {webhook_url}"
    else:
        return "Ошибка установки вебхука"

if __name__ == '__main__':
    # Локальный запуск для разработки
    app.run(host='0.0.0.0', port=5000, debug=True)