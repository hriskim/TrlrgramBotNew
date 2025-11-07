"""
🚀 app.py — ГЛАВНЫЙ серверный файл (FastAPI + Webhook для Telegram)

ЗАЧЕМ НУЖЕН:
• 🧠 Это веб-сервис, который поднимает Render. Он слушает HTTP-порт и принимает обновления от Telegram.
• 🌐 Здесь создаётся endpoint /webhook/<секрет>, на который Telegram присылает апдейты.
• 🔗 На старте мы автоматически ставим вебхук на публичный URL (Render даёт RENDER_EXTERNAL_URL).
• 🧲 Все апдейты перебрасываются в PTB-приложение с вашими хендлерами (см. user_bot.py).

ЧТО НАСТРОИТЬ:
• 🔐 Переменные окружения: BOT_TOKEN (из @BotFather) и WEBHOOK_SECRET (любой ваш секрет).
• 🧾 Опционально: SERVICE_FINGERPRINT (строка-«отпечаток» сервиса для /health).
• 🖥️ Локально можно задать PUBLIC_URL (например http://localhost:8000) для теста вебхука.

ЧЕГО НЕ ДЕЛАТЬ:
• ⛔ Не используйте long-polling (run_polling) на Render Free — тут нужен Webhook.
• ⛔ Не слушайте произвольный порт — Render ждёт порт из переменной $PORT.

КАК ПРОВЕРИТЬ:
1) ✅ GET /health → {"ok": true, "fingerprint": "...", "repo": "..."}
2) 🔍 https://api.telegram.org/bot<ТОКЕН>/getWebhookInfo → в url ваш Render-домен + /webhook/<секрет>
3) 💬 Напишите боту в Telegram → он отвечает.
"""

import os
import logging
from typing import Optional

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application

# 🪵 Понятные логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ptb-webhook")

# 🔐 Переменные окружения (значения задаём в Render → Settings → Environment)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "hook")  # ваш секрет для пути вебхука
# 🌐 Публичный URL: Render задаёт RENDER_EXTERNAL_URL. Локально можно PUBLIC_URL.
PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("PUBLIC_URL")

# 🏷️ «Отпечаток» сервиса/репозитория для /health (удобно, чтобы убедиться, что деплой тот)
SERVICE_FINGERPRINT = os.getenv("SERVICE_FINGERPRINT", "unknown")

# 📄 Опционально читаем отпечаток из файла репозитория (если положите FINGERPRINT.txt в корень)
try:
    with open("FINGERPRINT.txt", "r", encoding="utf-8") as f:
        REPO_FINGERPRINT = f.read().strip()
except FileNotFoundError:
    REPO_FINGERPRINT = "no-file"

# 🤖 PTB-приложение создадим лениво (в on_startup), чтобы не падать без переменных окружения
application: Optional[Application] = None

# 🧩 Подтягиваем регистрацию хендлеров (логика — в user_bot.py)
from user_bot import register  # noqa: E402

# ⚙️ Поднимаем веб-сервер
app = FastAPI()


@app.on_event("startup")
async def on_startup():
    """
    🏁 Старт сервиса:
    1) Проверяем, что есть PUBLIC_URL (куда ставить вебхук)
    2) Читаем BOT_TOKEN из окружения (на этапе старта, а не при импорте)
    3) Создаём PTB-приложение, регистрируем хендлеры, ставим вебхук, запускаем PTB
    """
    global application

    if not PUBLIC_URL:
        raise RuntimeError("❌ Нет PUBLIC_URL / RENDER_EXTERNAL_URL — куда ставить вебхук?")

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("❌ Нет BOT_TOKEN в переменных окружения (Render → Settings → Environment).")

    # Создаём PTB-приложение только теперь, когда токен точно есть
    application = Application.builder().token(bot_token).build()
    register(application)

    # Ставим вебхук
    url = f"{PUBLIC_URL}/webhook/{WEBHOOK_SECRET}"
    await application.bot.set_webhook(url, drop_pending_updates=True)

    # Запускаем PTB
    await application.initialize()
    await application.start()

    logger.info("✅ Webhook set to %s", url)


@app.on_event("shutdown")
async def on_shutdown():
    """🧹 Аккуратно останавливаем PTB при выключении сервиса."""
    if application:
        await application.stop()
        await application.shutdown()


@app.get("/health")
async def health():
    """
    🩺 Простой health-check.
    Возвращаем «отпечатки», чтобы легко убедиться, что деплой смотрит на нужный репо/ветку.
    SERVICE_FINGERPRINT — из ENV, REPO_FINGERPRINT — из файла FINGERPRINT.txt (если есть).
    """
    return {
        "ok": True,
        "fingerprint": SERVICE_FINGERPRINT,
        "repo": REPO_FINGERPRINT,
    }


@app.post("/webhook/{secret}")
async def webhook(secret: str, request: Request):
    """
    📩 Приём апдейтов от Telegram:
    • сверяем секрет,
    • превращаем JSON → Update,
    • отправляем в PTB,
    • отдаём быстрый 200 OK (ВАЖНО — иначе Telegram будет ретраить).
    """
    if secret != WEBHOOK_SECRET:
        return {"ok": False}

    if not application:
        # Если вдруг не успели инициализироваться
        return {"ok": False, "error": "bot not initialized"}

    data = await request.json()
    update = Update.de_json(data, application.bot)

    await application.process_update(update)
    return {"ok": True}
