"""
🚀 app.py — ГЛАВНЫЙ серверный файл (FastAPI + Webhook для Telegram)

ЗАЧЕМ НУЖЕН:
• 🧠 Это веб-сервис, который поднимает Render. Он слушает HTTP-порт и принимает обновления от Telegram.
• 🌐 Здесь создаётся endpoint /webhook/<секрет>, на который Telegram присылает апдейты.
• 🔗 На старте мы автоматически ставим вебхук на публичный URL (Render даёт RENDER_EXTERNAL_URL).
• 🧲 Все апдейты перебрасываются в PTB-приложение с вашими хендлерами (см. user_bot.py).

ЧТО НАСТРОИТЬ:
• 🔐 Переменные окружения: BOT_TOKEN (из @BotFather) и WEBHOOK_SECRET (любой ваш секрет).
• 🖥️ Локально можно задать PUBLIC_URL (например http://localhost:8000) для теста вебхука.

ЧЕГО НЕ ДЕЛАТЬ:
• ⛔ Не используйте long-polling (run_polling) на Render Free — тут нужен Webhook.
• ⛔ Не слушайте произвольный порт — Render ждёт порт из переменной $PORT.

КАК ПРОВЕРИТЬ:
1) ✅ GET /health → {"ok": true}
2) 🔍 https://api.telegram.org/bot<ТОКЕН>/getWebhookInfo → в url ваш Render-домен + /webhook/<секрет>
3) 💬 Напишите боту в Telegram → он отвечает.
"""

import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application

# 🪵 Включим понятные логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ptb-webhook")

# 🔐 Переменные окружения (ЗАДАЁМ В UI Render → Environment)
BOT_TOKEN = os.environ["BOT_TOKEN"]                   # токен бота из @BotFather
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "hook")  # ваш секрет для пути вебхука
# 🌐 Публичный URL: Render задаёт RENDER_EXTERNAL_URL автоматически.
# Локально можно задать PUBLIC_URL для теста.
PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("PUBLIC_URL")

# 🤖 Создаём PTB-приложение (ядро бота)
application = Application.builder().token(BOT_TOKEN).build()

# 🧩 Подтягиваем ваши хендлеры
from user_bot import register  # noqa: E402
register(application)

# ⚙️ Поднимаем веб-сервер
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    """
    🏁 Старт сервиса:
    1) Проверяем публичный URL
    2) Ставим вебхук на <PUBLIC_URL>/webhook/<SECRET>
    3) Инициализируем и запускаем PTB
    """
    assert PUBLIC_URL, "❌ Нет PUBLIC_URL / RENDER_EXTERNAL_URL — куда ставить вебхук?"
    url = f"{PUBLIC_URL}/webhook/{WEBHOOK_SECRET}"

    # 🧷 Поставим вебхук. drop_pending_updates=True — Telegram сбросит «висящие» апдейты
    await application.bot.set_webhook(url, drop_pending_updates=True)

    # ▶️ Запускаем PTB
    await application.initialize()
    await application.start()

    logger.info("✅ Webhook set to %s", url)


@app.on_event("shutdown")
async def on_shutdown():
    """🧹 Аккуратно останавливаем PTB при выключении сервиса."""
    await application.stop()
    await application.shutdown()


@app.get("/health")
async def health():
    """🩺 Простой health-check, удобен для мониторинга и проверки Render."""
    return {"ok": True}


@app.post("/webhook/{secret}")
async def webhook(secret: str, request: Request):
    """
    📩 Главная точка приёма апдейтов от Telegram:
    • сверяем секрет,
    • превращаем JSON → Update,
    • отправляем в PTB,
    • отдаём быстрый 200 OK (ВАЖНО — иначе Telegram будет ретраить).
    """
    if secret != WEBHOOK_SECRET:
        return {"ok": False}

    data = await request.json()
    update = Update.de_json(data, application.bot)

    await application.process_update(update)
    return {"ok": True}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

