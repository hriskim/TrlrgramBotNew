# 🤖 Telegram Bot (PTB v20 + FastAPI, Webhook) для Render (free)

Этот шаблон переводит бота с ноутбука (polling) в прод-сервис на **Webhook**.
Работает на **Render Free** (усыпляет при простое — ок, Telegram сам ретраит).

## 📁 Содержимое
- `app.py` — веб-сервер (FastAPI), ставит вебхук на публичный URL, принимает `/webhook/<секрет>`, передаёт апдейты в PTB.
- `user_bot.py` — ваши хендлеры: команды, кнопки, демо-фичи.
- `requirements.txt` — зависимости.
- `render.yaml` — конфигурация Render Web Service.
- `.env.sample` — пример окружения.

## 🧪 Локальный запуск
```bash
pip install -r requirements.txt
export BOT_TOKEN=xxx:from_BotFather
export WEBHOOK_SECRET=hooksecret
export PUBLIC_URL=http://localhost:8000
uvicorn app:app --host 0.0.0.0 --port 8000
