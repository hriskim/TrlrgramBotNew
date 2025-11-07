"""
🧠 user_bot.py — вся логика бота (команды и обработчики)

КАК ЭТО РАБОТАЕТ:
• Этот файл импортируется из app.py.
• Функция register(application) «вешает» хендлеры на PTB-приложение.
• Добавляйте свои команды/кнопки ниже — и регистрируйте их в register().

ПРАВИЛА:
• Все обработчики для python-telegram-bot v20+ — async def.
• Токены/секреты не храним здесь (они в окружении и читаются в app.py).
• Хотите модульность — смело выносите большие куски в свои модули и импортируйте их сюда.

БЫСТРЫЙ СТАРТ:
• /start, /help — базовые команды
• /menu — пример ReplyKeyboard
• Inline-кнопки (callback)
• /crypto, /convert, /weather — демо-заглушки под реальные API
"""

from typing import Optional

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ─────────────────────────────────────────────────────────
# 🔹 БАЗОВЫЕ КОМАНДЫ /start /help
# ─────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👋 /start — проверка связи и мини-справка."""
    text = (
        "✨ Привет! Я живу на Render через WEBHOOK.\n"
        "🗣️ Пришли текст — я повторю (эхо).\n\n"
        "📜 Команды:\n"
        "• /start — проверить, что бот отвечает\n"
        "• /help  — подсказка по функциям\n"
        "• /menu  — показать кнопки\n"
        "• /crypto BTC — демо котировка (заглушка)\n"
        "• /convert 100 usd rub — демо конвертер (заглушка)\n"
        "• /weather Phuket — демо погода (заглушка)\n"
    )
    await update.message.reply_text(text)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🆘 /help — список доступных команд (дополняйте своими)."""
    text = (
        "🧭 Доступные команды:\n"
        "• /start — проверка связи\n"
        "• /help — помощь\n"
        "• /menu — кнопки\n"
        "• /crypto <SYMBOL> — демо крипто-ответ\n"
        "• /convert <AMOUNT> <FROM> <TO> — демо конвертер\n"
        "• /weather <CITY> — демо погода\n\n"
        "💡 В проде подключайте реальные API/БД в соответствующие хендлеры."
    )
    await update.message.reply_text(text)


# ─────────────────────────────────────────────────────────
# 🔹 КНОПКИ: ReplyKeyboard + Inline
# ─────────────────────────────────────────────────────────

async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🗂️ /menu — пример обычной клавиатуры (ReplyKeyboard).
    Удобно «для чайников»: можно нажимать кнопки вместо команд.
    """
    keyboard = [
        ["Курс 💱", "Погода 🌤"],
        ["Конвертер 🔁", "Справка 📘"],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери действие:", reply_markup=markup)


async def show_inline_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔳 Inline-кнопки под сообщением (callback_data)."""
    kb = [
        [
            InlineKeyboardButton("Курс BTC ₿", callback_data="rate:BTC"),
            InlineKeyboardButton("Курс ETH ♦", callback_data="rate:ETH"),
        ],
        [InlineKeyboardButton("Помощь 🆘", callback_data="help")],
    ]
    await update.message.reply_text(
        "Inline-меню (демо):",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🖱️ Обработка нажатий на inline-кнопки."""
    query = update.callback_query
    data = query.data if query else ""
    await query.answer()  # закрыть «часики» на кнопке

    if data.startswith("rate:"):
        symbol = data.split(":", 1)[1]
        # TODO: подключить реальный источник (биржа/CG/CMC и т.д.)
        await query.edit_message_text(f"Демо: {symbol} ≈ 68000 USDT ⚠️ (подключи реальное API).")
    elif data == "help":
        await query.edit_message_text("Помощь: /start, /help, /menu, /crypto, /convert, /weather")
    else:
        await query.edit_message_text(f"Неизвестный callback: {data}")


# ─────────────────────────────────────────────────────────
# 🔹 ДЕМО «КРИПТА / КОНВЕРТЕР / ПОГОДА»
# ─────────────────────────────────────────────────────────

async def cmd_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    💱 /crypto <SYMBOL> — демо-хендлер.
    ℹ️ В проде подключите реальный API (CoinGecko/CoinMarketCap/Binance и т.п.).
    """
    args = context.args or []
    symbol = (args[0] if args else "BTC").upper()

    # TODO: сюда — реальный запрос к API
    await update.message.reply_text(f"Демо: {symbol} ≈ 68000 USDT ⚠️ (подключи реальное API).")


async def cmd_convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🔁 /convert 100 usd rub — демо-конвертер.
    ℹ️ Подмените заглушку на реальный курс (API/своя БД).
    """
    args = context.args or []
    if len(args) < 3:
        return await update.message.reply_text(
            "Использование: /convert <СУММА> <ИЗ> <В>\nПример: /convert 100 usd rub"
        )

    amount_str, src, dst = args[0], args[1].upper(), args[2].upper()
    try:
        amount = float(amount_str.replace(",", "."))
    except ValueError:
        return await update.message.reply_text("Сумма должна быть числом. Пример: /convert 100 usd rub")

    # TODO: реальный курс; пока — демо множитель
    converted = amount * 1.23
    await update.message.reply_text(f"≈ {converted:.2f} {dst} (демо; подключи реальный курс) ⚠️")


async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🌤 /weather <CITY> — демо-погода.
    ℹ️ Подключите OpenWeatherMap/meteosource и красиво отформатируйте ответ.
    """
    args = context.args or []
    city = "Phuket" if not args else " ".join(args)

    await update.message.reply_text(f"Погода в {city}: демо-данные ⚠️ (подключи API).")


# ─────────────────────────────────────────────────────────
# 🔹 РОУТЕР ПО ТЕКСТУ (для ReplyKeyboard)
# ─────────────────────────────────────────────────────────

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🧭 Любой НЕкомандный текст попадает сюда.
    Удобно «разрулить» быстрые кнопки из ReplyKeyboard.
    """
    text = (update.message.text or "").strip().lower()

    if text.startswith("курс"):
        return await cmd_crypto(update, context)
    if text.startswith("погод"):
        return await cmd_weather(update, context)
    if text.startswith("конвер"):
        return await cmd_convert(update, context)
    if text.startswith("справ"):
        return await cmd_help(update, context)

    # 🪄 Эхо по умолчанию (видно, что бот жив)
    await update.message.reply_text(update.message.text or "…")


# ─────────────────────────────────────────────────────────
# 🔹 РЕГИСТРАЦИЯ ВСЕХ ХЕНДЛЕРОВ
# ─────────────────────────────────────────────────────────

def register(application):
    """
    🔗 Вызывается из app.py при старте сервиса.
    Здесь вешаем все handlers на PTB-приложение.
    """
    # Команды
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help",  cmd_help))
    application.add_handler(CommandHandler("menu",  cmd_menu))
    application.add_handler(CommandHandler("crypto",  cmd_crypto))
    application.add_handler(CommandHandler("convert", cmd_convert))
    application.add_handler(CommandHandler("weather", cmd_weather))

    # Inline-кнопки
    application.add_handler(CallbackQueryHandler(on_callback))

    # Любой текст (кроме команд) — маршрутизируем
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    # 🔧 Пример: добавьте свою команду
    # async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     await update.message.reply_text("pong 🏓")
    # application.add_handler(CommandHandler("ping", cmd_ping))
