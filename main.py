from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import json
import os
import time
from datetime import datetime

BOT_TOKEN = "8959279502:AAGJIX6qqoSwgFa-Y0lXnhC4ClIR9nE4ifI"
ADMIN_ID = 123456789  # ЗАМІНИ НА СВІЙ TELEGRAM ID

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Файл для зберігання даних
DATA_FILE = "data.json"

# Завантаження даних
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"balance": 0, "deals": [], "users": {}, "deal_counter": 0}

# Збереження даних
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

data = load_data()

# ========== ГОЛОВНЕ МЕНЮ (1:1 ЯК У PLAYEROK) ==========
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🟢 Новая сделка", callback_data="new_deal"),
        InlineKeyboardButton("📋 Мои сделки", callback_data="my_deals")
    )
    keyboard.add(
        InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        InlineKeyboardButton("📊 Меню", callback_data="menu")
    )
    return keyboard

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    # Зберігаємо користувача
    if str(message.from_user.id) not in data["users"]:
        data["users"][str(message.from_user.id)] = {
            "username": message.from_user.username or "Без имени",
            "joined": time.time()
        }
        save_data(data)
    
    bot.send_message(
        message.chat.id,
        "🥰 **Добро пожаловать!**\n\n"
        "✔️ **Playerok** — специализированный сервис по обеспечению безопасности внебиржевых сделок.\n\n"
        "🎵 Автоматизированный алгоритм исполнения.\n"
        "📈 Скорость и автоматизация.\n"
        "📉 Удобный и быстрый вывод средств.\n\n"
        "• Комиссия сервиса: **1%**\n"
        "• Режим работы: **24/7**\n\n"
        "Выберите нужный раздел ниже:",
        reply_markup=main_menu(),
        parse_mode='Markdown'
    )

# ========== ОБРОБКА КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if call.data == "new_deal":
        bot.send_message(
            chat_id,
            "🟢 **Новая сделка**\n\n"
            "Введите сумму сделки в рублях (например: 1000):",
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(call.message, create_deal)

    elif call.data == "my_deals":
        user_deals = [d for d in data["deals"] if d["user_id"] == user_id]
        if not user_deals:
            bot.send_message(chat_id, "📋 У вас пока нет сделок.")
        else:
            text = "📋 **Ваши сделки:**\n\n"
            for d in user_deals[-10:]:
                status_emoji = "✅" if d["status"] == "success" else "⏳"
                status_text = "Успешно" if d["status"] == "success" else "В обработке"
                date = datetime.fromtimestamp(d["created_at"]).strftime("%d.%m %H:%M")
                text += f"• #{d['id']} | {d['amount']}₽ | {status_emoji} {status_text} | {date}\n"
            bot.send_message(chat_id, text, parse_mode='Markdown')

    elif call.data == "profile":
        balance = data["balance"]
        user_deals = [d for d in data["deals"] if d["user_id"] == user_id]
        success_deals = len([d for d in user_deals if d["status"] == "success"])
        
        text = f"👤 **Ваш профиль**\n\n"
        text += f"💰 Баланс: **{balance}₽**\n"
        text += f"📊 Всего сделок: **{len(user_deals)}**\n"
        text += f"✅ Успешных: **{success_deals}**\n"
        text += f"📈 Комиссия: **1%**"
        bot.send_message(chat_id, text, parse_mode='Markdown')

    elif call.data == "menu":
        bot.send_message(
            chat_id,
            "📊 **Меню**\n\nВыберите действие:",
            reply_markup=main_menu(),
            parse_mode='Markdown'
        )

    elif call.data.startswith("admin_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Доступ запрещён!")
            return
        handle_admin(call)

# ========== СТВОРЕННЯ УГОДИ ==========
def create_deal(message):
    try:
        amount = int(message.text.strip())
        if amount < 1:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0!")
            return
        
        data["deal_counter"] += 1
        deal_id = data["deal_counter"]
        
        data["deals"].append({
            "id": deal_id,
            "user_id": message.from_user.id,
            "amount": amount,
            "status": "pending",
            "created_at": time.time()
        })
        save_data(data)
        
        bot.send_message(
            message.chat.id,
            f"🟢 **Сделка #{deal_id} создана!**\n\n"
            f"💰 Сумма: **{amount}₽**\n"
            f"📊 Статус: ⏳ **В обработке**\n\n"
            f"Комиссия: **{int(amount * 0.01)}₽** (1%)\n"
            f"К получению: **{int(amount * 0.99)}₽**\n\n"
            f"Ожидайте подтверждения от администратора.",
            parse_mode='Markdown'
        )
        
        # Повідомлення адміну про нову угоду
        bot.send_message(
            ADMIN_ID,
            f"🆕 **Новая сделка!**\n\n"
            f"ID: #{deal_id}\n"
            f"Пользователь: @{message.from_user.username or 'Без имени'}\n"
            f"Сумма: {amount}₽\n"
            f"Комиссия: {int(amount * 0.01)}₽\n\n"
            f"Подтвердите сделку через /admin",
            parse_mode='Markdown'
        )
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите сумму числом! (например: 1000)")

# ========== АДМІН-ПАНЕЛЬ ==========
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💰 Пополнить баланс", callback_data="admin_add_balance"),
        InlineKeyboardButton("✅ Подтвердить сделку", callback_data="admin_confirm_deal")
    )
    keyboard.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📋 Все сделки", callback_data="admin_all_deals")
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
    )
    bot.send_message(
        message.chat.id,
        "🔐 **Админ-панель**\n\n"
        f"💰 Баланс: {data['balance']}₽\n"
        f"📊 Всего сделок: {len(data['deals'])}",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

def handle_admin(call):
    chat_id = call.message.chat.id

    if call.data == "admin_add_balance":
        bot.send_message(chat_id, "💰 Введите сумму для пополнения баланса:")
        bot.register_next_step_handler(call.message, add_balance)

    elif call.data == "admin_confirm_deal":
        pending = [d for d in data["deals"] if d["status"] == "pending"]
        if not pending:
            bot.send_message(chat_id, "✅ Нет сделок для подтверждения.")
            return
        text = "✅ **Выберите сделку для подтверждения:**\n\n"
        for d in pending[-10:]:
            text += f"#{d['id']} | {d['amount']}₽ | @{data['users'].get(str(d['user_id']), {}).get('username', 'Неизвестно')}\n"
        text += "\nВведите ID сделки:"
        bot.send_message(chat_id, text, parse_mode='Markdown')
        bot.register_next_step_handler(call.message, confirm_deal)

    elif call.data == "admin_stats":
        pending = len([d for d in data["deals"] if d["status"] == "pending"])
        success = len([d for d in data["deals"] if d["status"] == "success"])
        total = len(data["deals"])
        users = len(data["users"])
        
        text = f"📊 **Статистика**\n\n"
        text += f"👥 Пользователей: **{users}**\n"
        text += f"📋 Всего сделок: **{total}**\n"
        text += f"⏳ В обработке: **{pending}**\n"
        text += f"✅ Успешных: **{success}**\n"
        text += f"💰 Баланс: **{data['balance']}₽**"
        bot.send_message(chat_id, text, parse_mode='Markdown')

    elif call.data == "admin_all_deals":
        if not data["deals"]:
            bot.send_message(chat_id, "📋 Нет сделок.")
            return
        text = "📋 **Все сделки:**\n\n"
        for d in data["deals"][-20:]:
            status_emoji = "✅" if d["status"] == "success" else "⏳"
            username = data["users"].get(str(d["user_id"]), {}).get("username", "Неизвестно")
            text += f"#{d['id']} | {d['amount']}₽ | {status_emoji} | @{username}\n"
        bot.send_message(chat_id, text, parse_mode='Markdown')

def add_balance(message):
    try:
        amount = int(message.text.strip())
        if amount < 1:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0!")
            return
        data["balance"] += amount
        save_data(data)
        bot.send_message(
            message.chat.id,
            f"✅ Баланс пополнен на **{amount}₽**\n\n💰 Текущий баланс: **{data['balance']}₽**",
            parse_mode='Markdown'
        )
    except:
        bot.send_message(message.chat.id, "❌ Введите сумму числом!")

def confirm_deal(message):
    try:
        deal_id = int(message.text.strip())
        for deal in data["deals"]:
            if deal["id"] == deal_id and deal["status"] == "pending":
                deal["status"] = "success"
                # Начисляем пользователю (минус комиссия 1%)
                commission = int(deal["amount"] * 0.01)
                user_balance = deal["amount"] - commission
                data["balance"] += user_balance
                save_data(data)
                
                bot.send_message(
                    message.chat.id,
                    f"✅ **Сделка #{deal_id} подтверждена!**\n\n"
                    f"💰 Сумма: {deal['amount']}₽\n"
                    f"📉 Комиссия: {commission}₽ (1%)\n"
                    f"📈 Начислено: {user_balance}₽\n\n"
                    f"Пользователь получит уведомление.",
                    parse_mode='Markdown'
                )
                
                # Уведомляем пользователя
                bot.send_message(
                    deal["user_id"],
                    f"✅ **Сделка #{deal_id} успешно завершена!**\n\n"
                    f"💰 Сумма: {deal['amount']}₽\n"
                    f"📉 Комиссия: {commission}₽ (1%)\n"
                    f"📈 Получено: {user_balance}₽\n\n"
                    f"Баланс обновлён!",
                    parse_mode='Markdown'
                )
                return
        bot.send_message(message.chat.id, "❌ Сделка не найдена или уже подтверждена.")
    except:
        bot.send_message(message.chat.id, "❌ Введите ID сделки числом!")

# ========== ЗАПУСК ==========
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
