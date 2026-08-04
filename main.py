from flask import Flask
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent

BOT_TOKEN = "8914898641:AAHW8yRrfPEZdoBvDnTRm09l2-h-Z0Nri5o"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@bot.inline_handler(lambda query: True)
def inline_test(inline_query):
    results = []
    for i in range(1, 6):
        results.append(
            InlineQueryResultArticle(
                id=str(i),
                title=f"Тест {i}",
                input_message_content=InputTextMessageContent(f"✅ Тест {i} працює!")
            )
        )
    bot.answer_inline_query(inline_query.id, results)

@app.route('/')
def index():
    return "✅ Бот працює!"

if __name__ == "__main__":
    import threading
    threading.Thread(target=bot.polling, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
