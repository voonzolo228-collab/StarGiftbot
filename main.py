import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent

BOT_TOKEN = "8914898641:AAHW8yRrfPEZdoBvDnTRm09l2-h-Z0Nri5o"
bot = telebot.TeleBot(BOT_TOKEN)

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

if __name__ == "__main__":
    bot.polling()
