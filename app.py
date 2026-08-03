from flask import Flask, request, jsonify
import telebot
import threading
import time

BOT_TOKEN = "ВАШ_ТОКЕН"  # ВСТАВТЕ СВІЙ ТОКЕН

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>✅ BOT IS ALIVE!</h1>"

@app.route('/webhook', methods=['POST'])
def webhook():
    return jsonify({'status': 'ok'})

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "✅ Бот працює!")

def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
