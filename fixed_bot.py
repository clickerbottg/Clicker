import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

TOKEN = "7880046385:AAHq25wmdy2bXy_BMVGe_pY1YYsksMlbjUw"  # Замініть на свій токен
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Підключення до бази даних
conn = sqlite3.connect("clicker.db")
cursor = conn.cursor()

# Створення таблиці, якщо вона не існує
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    dc INTEGER DEFAULT 0,
    upgrade_level INTEGER DEFAULT 1
)
""")
conn.commit()

# Функція для отримання даних користувача
def get_user(user_id):
    cursor.execute("SELECT dc, upgrade_level FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return (0, 1)  # Початкові значення
    return user

# Функція для оновлення балансу DC
def update_dc(user_id, amount):
    dc, level = get_user(user_id)
    new_dc = dc + amount
    cursor.execute("UPDATE users SET dc = ? WHERE user_id = ?", (new_dc, user_id))
    conn.commit()

# Функція для оновлення рівня покращень
def upgrade_user(user_id):
    dc, level = get_user(user_id)
    cost = level * 10  # Вартість апгрейду

    if dc >= cost:
        cursor.execute("UPDATE users SET dc = ?, upgrade_level = ? WHERE user_id = ?", (dc - cost, level + 1, user_id))
        conn.commit()
        return True, level + 1, cost
    return False, level, cost

# Функція для отримання топу гравців
def get_leaderboard():
    cursor.execute("SELECT user_id, dc FROM users ORDER BY dc DESC LIMIT 10")
    return cursor.fetchall()

# Генерація кнопок
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💰 Клік", callback_data="click"))
    keyboard.add(InlineKeyboardButton("⚡ Прокачати", callback_data="upgrade"))
    keyboard.add(InlineKeyboardButton("🏆 Лідерборд", callback_data="top"))
    return keyboard

# Стартове повідомлення
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    get_user(user_id)  # Реєстрація в БД
    await message.answer(
    "🎮 Ласкаво просимо в DC-клікер!\n\n"
    "Натискайте кнопки нижче:",
    reply_markup=get_main_keyboard()
)


# Обробка натискання кнопок
@dp.callback_query_handler(lambda call: call.data in ["click", "upgrade", "top"])
async def handle_click(call: types.CallbackQuery):
    user_id = call.from_user.id

    if call.data == "click":
        _, level = get_user(user_id)
        update_dc(user_id, level)
        await call.message.edit_text(
    f"💰 Ви отримали {level} DC!\n"
    f"🔝 Ваш баланс: {get_user(user_id)[0]} DC",
    reply_markup=get_main_keyboard()
)


    elif call.data == "upgrade":
        success, new_level, cost = upgrade_user(user_id)
        if success:
            text = (
    f"✅ Ви покращили рівень до {new_level}!\n"
    f"💰 Новий прибуток за клік: {new_level} DC"
)

        else:
            text = (
    f"❌ У вас недостатньо DC!\n"
    f"💸 Вартість покращення: {cost} DC"
)

        await call.message.edit_text(text, reply_markup=get_main_keyboard())

    elif call.data == "top":
        top_users = get_leaderboard()
        if not top_users:
            text = "😔 Поки що немає гравців у топі!"
        else:
            text = "🏆 *Топ гравців DC:* 🏆\n"
            for idx, (user_id, dc) in enumerate(top_users, start=1):
                text += f"{idx}. [User {user_id}](tg://user?id={user_id}) – {dc} DC\n"
        await call.message.edit_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
