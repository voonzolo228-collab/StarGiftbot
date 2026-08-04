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
        keyboard.add(
            InlineKeyboardButton(f"⭐ Забрати {amt} зірок", callback_data=f"claim_{amt}")
        )
        results.append(
            InlineQueryResultArticle(
                id=str(amt),
                title=f"⭐ Чек на {amt} зірок",
                description=f"Натисни, щоб забрати {amt} зірок",
                input_message_content=InputTextMessageContent(
                    f"🎯 **Ти отримав чек на {amt} зірок!**\nНатисни кнопку нижче, щоб забрати їх."
                ),
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        )
    bot.answer_inline_query(inline_query.id, results)

@bot.callback_query_handler(func=lambda call: call.data.startswith('claim_'))
def handle_claim(call):
    amount = call.data.split('_')[1]
    
    # Відповідаємо на натискання кнопки
    bot.answer_callback_query(call.id, f"✅ {amount} зірок зараховано!")
    
    # Редагуємо повідомлення, щоб показати, що дію виконано
    bot.edit_message_text(
        f"✅ **{amount} зірок успішно зараховано!**\nВони прийдуть на твій акаунт протягом 2-5 хвилин.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "🌟 **Вітаю!**\nЯ бот для отримання чеків на зірки.\n\n"
        "Напиши **@StarCheclBot** у будь-якому чаті та обери суму.",
        parse_mode='Markdown'
    )

def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
