from flask import Flask
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
import threading

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Бот працює!"

@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    results = []
    amounts = [100, 200, 300, 500, 700, 1000]
    for amt in amounts:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(f"⭐ Получить чек на {amt} звёзд", callback_data=f"send_{amt}"))
        results.append(
            InlineQueryResultArticle(
                id=str(amt),
                title=f"⭐ Чек на {amt} звёзд",
                description=f"Нажми, чтобы получить чек на {amt} звёзд",
                input_message_content=InputTextMessageContent(f"⭐ Ты получил чек на {amt} звёзд!"),
                reply_markup=keyboard
            )
        )
    bot.answer_inline_query(inline_query.id, results)

@bot.callback_query_handler(func=lambda call: call.data.startswith('send_'))
def handle_send_stars(call):
    amount = call.data.split('_')[1]
    bot.answer_callback_query(call.id, f"✅ Чек на {amount} звёзд получен!")
    bot.send_message(call.message.chat.id, f"✅ Ты получил чек на {amount} звёзд!")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "✅ Бот працює! Напиши @StarCheclBot у будь-якому чаті.")

def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
