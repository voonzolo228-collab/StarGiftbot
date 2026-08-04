from flask import Flask
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent
import threading

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"  # ЗАМІНИ НА ТОКЕН ВІД @StarCheckBot

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Бот працює!"

@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    results = []
    for i in range(1, 6):
        results.append(
            InlineQueryResultArticle(
                id=str(i),
                title=f"⭐ Тест {i}",
                input_message_content=InputTextMessageContent(f"✅ Тест {i} працює!")
            )
        )
    bot.answer_inline_query(inline_query.id, results)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "✅ Бот працює! Напиши @StarCheckBot у будь-якому чаті.")

def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
