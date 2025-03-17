import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Filter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
path_to_db = config.path_to_db
admins_list = config.admins_list

def init_db():
    conn = sqlite3.connect(path_to_db)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS guests(user_id TEXT PRIMARY KEY)')
    conn.commit()
    conn.close()

def add_user_to_db(user_id):
    user_id = str(user_id)
    conn = sqlite3.connect(path_to_db)
    cur = conn.cursor()
    cur.execute('''INSERT OR REPLACE INTO guests
                 (user_id)
                 VALUES (?)''',
               (user_id,))
    conn.commit()
    conn.close()

def delete_user_from_db(user_id):
    user_id = str(user_id)
    conn = sqlite3.connect(path_to_db)
    cur = conn.cursor()
    cur.execute('''DELETE FROM guests WHERE user_id = ?''', (user_id,))
    conn.commit()
    conn.close()

def count_users_in_db():
    conn = sqlite3.connect(path_to_db)
    cur = conn.cursor()
    cur.execute('''SELECT COUNT(*) FROM guests''')
    count = cur.fetchone()[0]
    conn.close()
    return count



@dp.message(Command("start"))
async def start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отменить регистрацию")],
        ],
        resize_keyboard=True,
    )
    if message.from_user.id in admins_list:
        await message.answer(
            "Напишите /q, чтобы получить количество зарегистрированных",
        )
        return
    print(message.from_user.id)
    add_user_to_db(message.from_user.id)
    await message.answer(
        "Вы успешно зарегистрированы на мероприятие",
        reply_markup=keyboard,
    )

@dp.message(Command("q"))
async def quantity(message: Message):
    if message.from_user.id not in admins_list:
        await message.answer(
            "Вы не имеете доступа к этой информации"
        )
        return
    await message.reply(
        f"Количество зарегистрированных пользователей: {count_users_in_db()}"
    )

@dp.message(lambda message: message.text.lower() == "отменить регистрацию")
async def delete_user(message: Message):
    delete_user_from_db(str(message.from_user.id))
    await message.answer(
        "Регистрация отменена"
    )

async def main():
    init_db()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
