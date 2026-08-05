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

DATA_FILE = "users_data.json"

# Завантаження даних
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"profiles": [], "filters": {}, "users": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

data = load_data()

# ========== ГОЛОВНЕ МЕНЮ ==========
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        InlineKeyboardButton("📊 Просмотр БД", callback_data="view_db")
    )
    keyboard.add(
        InlineKeyboardButton("🔍 Парсинг про...", callback_data="parsing"),
        InlineKeyboardButton("🤖 Боты", callback_data="bots")
    )
    keyboard.add(
        InlineKeyboardButton("📝 Шаблоны", callback_data="templates"),
        InlineKeyboardButton("🚫 Чёрный список", callback_data="blacklist")
    )
    keyboard.add(
        InlineKeyboardButton("🔄 Зеркала", callback_data="mirrors"),
        InlineKeyboardButton("ℹ️ Инфо", callback_data="info")
    )
    return keyboard

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = str(message.from_user.id)
    if user_id not in data.get("users", {}):
        data.setdefault("users", {})[user_id] = {
            "access": time.time() + 259200,
            "username": message.from_user.username or "Без имени"
        }
        save_data(data)
        bot.send_message(
            message.chat.id,
            "✅ **Тестовый доступ активирован на 3 дня.**\n\n"
            "Осталось: 2 д. 15 ч.\n"
            "В тестовый доступ входит основной парсер без Premium-фильтров.\n\n"
            "Выберите раздел:",
            reply_markup=main_menu(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            message.chat.id,
            "👋 **Добро пожаловать!**\n\nВыберите раздел:",
            reply_markup=main_menu(),
            parse_mode='Markdown'
        )

# ========== КЛАВІАТУРИ ДЛЯ ВИБОРУ ==========
def gender_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🧑 Мужчины", callback_data="filter_male"),
        InlineKeyboardButton("👩 Женщины", callback_data="filter_female"),
        InlineKeyboardButton("👤 Любой пол", callback_data="filter_any")
    )
    return keyboard

def level_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("1️⃣ Уровень 1", callback_data="level_1"),
        InlineKeyboardButton("2️⃣ Уровень 2", callback_data="level_2"),
        InlineKeyboardButton("3️⃣ Уровень 3", callback_data="level_3")
    )
    keyboard.add(
        InlineKeyboardButton("4️⃣ Уровень 4", callback_data="level_4"),
        InlineKeyboardButton("5️⃣ Уровень 5", callback_data="level_5"),
        InlineKeyboardButton("🌐 Любой", callback_data="level_any")
    )
    return keyboard

def nft_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🟢 1-10", callback_data="nft_1_10"),
        InlineKeyboardButton("🟡 11-50", callback_data="nft_11_50"),
        InlineKeyboardButton("🔴 51+", callback_data="nft_51_plus")
    )
    keyboard.add(
        InlineKeyboardButton("🌐 Любое", callback_data="nft_any")
    )
    return keyboard

def sort_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⬆️ По возрастанию", callback_data="sort_asc"),
        InlineKeyboardButton("⬇️ По убыванию", callback_data="sort_desc")
    )
    return keyboard

# ========== ОБРОБКА КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if call.data == "profile":
        user_data = data.get("users", {}).get(str(user_id), {})
        access_time = user_data.get("access", 0)
        days_left = max(0, int((access_time - time.time()) / 86400))
        hours_left = max(0, int((access_time - time.time()) % 86400 / 3600))
        
        text = f"👤 **Ваш профиль**\n\n"
        text += f"🆔 ID: {user_id}\n"
        text += f"📛 Имя: {user_data.get('username', 'Неизвестно')}\n"
        text += f"⏳ Доступ: {days_left} д. {hours_left} ч.\n"
        text += f"📊 Всего профилей: {len(data.get('profiles', []))}"
        bot.send_message(chat_id, text, parse_mode='Markdown')

    elif call.data == "view_db":
        if not data.get("profiles"):
            bot.send_message(chat_id, "📊 **База данных пуста.**\n\nИспользуйте парсинг для добавления профилей.", parse_mode='Markdown')
            return
        
        text = "📊 **Просмотр БД**\n\n"
        for p in data["profiles"][-10:]:
            nft_count = len(p.get('nfts', []))
            text += f"• {p.get('name', 'Без имени')} | {p.get('gender', 'Не указан')} | NFT: {nft_count} | LVL: {p.get('level', 0)}\n"
        bot.send_message(chat_id, text, parse_mode='Markdown')

    elif call.data == "parsing":
        bot.send_message(
            chat_id,
            "🔍 **Парсинг профилей**\n\n"
            "Шаг 1: Выберите пол:",
            reply_markup=gender_keyboard(),
            parse_mode='Markdown'
        )

    elif call.data.startswith("filter_"):
        gender = call.data.split("_")[1]
        data["filters"]["gender"] = gender
        save_data(data)
        
        bot.send_message(
            chat_id,
            f"✅ Выбрано: {gender}\n\n"
            "Шаг 2: Выберите уровень профиля:",
            reply_markup=level_keyboard(),
            parse_mode='Markdown'
        )

    elif call.data.startswith("level_"):
        level = call.data.split("_")[1]
        data["filters"]["level"] = level
        save_data(data)
        
        bot.send_message(
            chat_id,
            f"✅ Уровень: {level}\n\n"
            "Шаг 3: Выберите количество NFT:",
            reply_markup=nft_keyboard(),
            parse_mode='Markdown'
        )

    elif call.data.startswith("nft_"):
        nft_filter = call.data.split("_")[1]
        data["filters"]["nft"] = nft_filter
        save_data(data)
        
        bot.send_message(
            chat_id,
            f"✅ NFT: {nft_filter}\n\n"
            "Шаг 4: Выберите сортировку:",
            reply_markup=sort_keyboard(),
            parse_mode='Markdown'
        )

    elif call.data.startswith("sort_"):
        sort_type = call.data.split("_")[1]
        data["filters"]["sort"] = sort_type
        save_data(data)
        
        # Показуємо всі вибрані фільтри
        filters = data.get("filters", {})
        text = "🎯 **Ваши фильтры:**\n\n"
        text += f"👤 Пол: {filters.get('gender', 'Не выбран')}\n"
        text += f"📊 Уровень: {filters.get('level', 'Не выбран')}\n"
        text += f"🎨 NFT: {filters.get('nft', 'Не выбран')}\n"
        text += f"📈 Сортировка: {filters.get('sort', 'Не выбрана')}\n\n"
        text += "✅ Нажмите 'Начать парсинг' для поиска:"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🚀 Начать парсинг", callback_data="start_parsing"))
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="menu"))
        
        bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

    elif call.data == "start_parsing":
        bot.send_message(chat_id, "⏳ **Парсинг запущен...**\n\nЭто может занять несколько секунд.")
        
        # Генерація профілів згідно з фільтрами
        profiles = generate_profiles(data.get("filters", {}))
        data["profiles"] = profiles
        save_data(data)
        
        bot.send_message(
            chat_id,
            f"✅ **Парсинг завершён!**\n\n"
            f"Найдено: {len(profiles)} профилей\n"
            f"🎨 Всего NFT: {sum(len(p.get('nfts', [])) for p in profiles)}",
            parse_mode='Markdown'
        )

    elif call.data == "bots":
        bot.send_message(
            chat_id,
            "🤖 **Боты**\n\n"
            "Список доступных ботов для парсинга:\n"
            "• @GiftParserBot - основной парсер\n"
            "• @GiftFilterBot - фильтрация\n"
            "• @GiftExportBot - экспорт данных",
            parse_mode='Markdown'
        )

    elif call.data == "templates":
        bot.send_message(
            chat_id,
            "📝 **Шаблоны**\n\n"
            "Готовые шаблоны для поиска:\n"
            "• VIP профили (100+ NFT)\n"
            "• Новые профили (до 10 NFT)\n"
            "• Активные профили (онлайн)",
            parse_mode='Markdown'
        )

    elif call.data == "blacklist":
        bot.send_message(
            chat_id,
            "🚫 **Чёрный список**\n\n"
            "Профили, которые исключены из поиска:\n"
            "• Список пуст.",
            parse_mode='Markdown'
        )

    elif call.data == "mirrors":
        bot.send_message(
            chat_id,
            "🔄 **Зеркала**\n\n"
            "Активные зеркала сервиса:\n"
            "• https://gift-parser.com\n"
            "• https://gift-parser.net",
            parse_mode='Markdown'
        )

    elif call.data == "info":
        bot.send_message(
            chat_id,
            f"ℹ️ **Информация**\n\n"
            f"Версия: 2.0\n"
            f"База данных: {len(data.get('profiles', []))} профилей\n"
            f"Последнее обновление: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode='Markdown'
        )

    elif call.data == "menu":
        bot.send_message(
            chat_id,
            "📊 **Главное меню**",
            reply_markup=main_menu(),
            parse_mode='Markdown'
        )

    elif call.data.startswith("admin_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Доступ запрещён!")
            return
        handle_admin(call)

# ========== ГЕНЕРАЦІЯ ПРОФІЛІВ ==========
def generate_profiles(filters):
    profiles = []
    nfts = [
        "Artisan Brick", "Astral Shard", "B Day Candle", "Berry Box",
        "Big Year", "Bling Binky", "Bonded Ring", "Bow Tie",
        "Bunny Muffin", "Candy Cane", "Chill Flame", "Clover Pin",
        "Cookie Heart", "Crystal Ball", "Diamond Ring", "Durovs Cap"
    ]
    
    gender = filters.get("gender", "any")
    level = filters.get("level", "any")
    nft_filter = filters.get("nft", "any")
    
    for i in range(1, 31):
        # Визначення статі
        if gender == "any":
            gen = ["male", "female"][i % 2]
        else:
            gen = gender
        
        # Визначення рівня
        if level == "any":
            lvl = i % 5 + 1
        else:
            try:
                lvl = int(level)
            except:
                lvl = 1
        
        # Визначення кількості NFT
        if nft_filter == "1_10":
            nft_count = i % 10 + 1
        elif nft_filter == "11_50":
            nft_count = (i % 40) + 11
        elif nft_filter == "51_plus":
            nft_count = (i % 50) + 51
        else:
            nft_count = i % 10 + 1
        
        profile = {
            "id": i,
            "name": f"User_{i}",
            "gender": gen,
            "level": lvl,
            "nfts": nfts[:min(nft_count, len(nfts))]
        }
        profiles.append(profile)
    
    # Сортування
    sort = filters.get("sort", "asc")
    if sort == "asc":
        profiles.sort(key=lambda x: x["level"])
    else:
        profiles.sort(key=lambda x: x["level"], reverse=True)
    
    return profiles

# ========== АДМІН-ПАНЕЛЬ ==========
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📋 Все профили", callback_data="admin_profiles")
    )
    keyboard.add(
        InlineKeyboardButton("🗑 Очистить БД", callback_data="admin_clear"),
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
    )
    bot.send_message(
        message.chat.id,
        "🔐 **Админ-панель**",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

def handle_admin(call):
    chat_id = call.message.chat.id

    if call.data == "admin_stats":
        profiles = data.get("profiles", [])
        text = f"📊 **Статистика**\n\n"
        text += f"👥 Всего профилей: {len(profiles)}\n"
        text += f"🧑 Мужчин: {len([p for p in profiles if p.get('gender') == 'male'])}\n"
        text += f"👩 Женщин: {len([p for p in profiles if p.get('gender') == 'female'])}\n"
        text += f"🎨 Всего NFT: {sum(len(p.get('nfts', [])) for p in profiles)}"
        bot.send_message(chat_id, text, parse_mode='Markdown')

    elif call.data == "admin_profiles":
        if not data.get("profiles"):
            bot.send_message(chat_id, "📋 База данных пуста.")
            return
        text = "📋 **Все профили:**\n\n"
        for p in data["profiles"]:
            text += f"• {p['name']} | {p['gender']} | NFT: {len(p.get('nfts', []))} | LVL: {p.get('level', 0)}\n"
        bot.send_message(chat_id, text, parse_mode='Markdown')

    elif call.data == "admin_clear":
        data["profiles"] = []
        save_data(data)
        bot.send_message(chat_id, "🗑 База данных очищена!")

# ========== ЗАПУСК ==========
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
