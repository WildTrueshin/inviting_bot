import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Filter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
path_to_db = config.path_to_db
admins_list = config.admins_list

def init_db():
    conn = sqlite3.connect(path_to_db)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS guests(user_id, organization, post, name)''')
    conn.commit()
    conn.close()

def add_user_to_db(user_id, organization, post, name):
    user_id = str(user_id)
    conn = sqlite3.connect(path_to_db)
    cur = conn.cursor()
    cur.execute('''INSERT OR REPLACE INTO guests
                 (user_id, organization, post, name)
                 VALUES (?, ?, ?, ?)''',
               (user_id, organization, post, name))
    conn.commit()
    conn.close()

def delete_user_from_db(user_id):
    user_id = str(user_id)
    conn = sqlite3.connect(path_to_db)
    cur = conn.cursor()
    cur.execute('''DELETE FROM guests WHERE user_id = ?''', (user_id,))
    conn.commit()
    conn.close()

def check_user(user_id):
    user_id = str(user_id)
    conn = sqlite3.connect(path_to_db)
    cur = conn.cursor()
    cur.execute('''SELECT * FROM guests WHERE user_id = ?''', (user_id,))
    user = cur.fetchone()
    conn.close()
    return user is not None

def get_users_list():
    conn = sqlite3.connect(path_to_db)
    cur = conn.cursor()
    cur.execute('''SELECT * FROM guests''')
    users = cur.fetchall()
    conn.close()
    return users

class UserState(StatesGroup):
    organization = State()
    post = State()
    name = State()

def create_single_button(text):
    return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=text)],
                ],
                resize_keyboard=True,
           )

@dp.message(lambda message: message.text == "/start" or message.text.lower() == "зарегистрироваться")
async def start(message: Message, state: State):
    if message.from_user.id in admins_list:
        await message.answer(
               "Вы хотите увидеть список зарегистрированных?",
               reply_markup=create_single_button("Список зарегистрированных") 
              )
        return
    if check_user(message.from_user.id):
        await message.answer(
                "Вы уже зарегистрированы"
              )
        return
    await message.answer(
            "Введите название вашей организации"
          )
    await state.set_state(UserState.organization)

@dp.message(UserState.organization)
async def get_organization(message: Message, state: FSMContext):
    await state.update_data(organization=message.text)
    await state.set_state(UserState.post)
    await message.answer(
            "Введите вашу должность в организации"
          )

@dp.message(UserState.post)
async def get_post(message: Message, state: FSMContext):
    await state.update_data(post=message.text)
    await state.set_state(UserState.name)
    await message.answer(
            "Введите ваше имя"
          )

@dp.message(UserState.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    add_user_to_db(message.from_user.id, data["organization"], data["post"], data["name"])
    await state.clear()
    await message.answer(
            "Вы успешно зарегистрированы",
            reply_markup=create_single_button("Отменить регистрацию")
          )

@dp.message(F.text.lower() == "отменить регистрацию")
async def canel_ref(message: Message):
    delete_user_from_db(message.from_user.id)
    await message.answer(
            "Регистрация отменена",
            reply_markup=create_single_button("Зарегистрироваться")
          )

def generate_message(users_list):
    res = "Количество зарегистрированных: " + str(len(users_list)) + "\n\n"
    for user in users_list:
        res += user[1] + "\n";
        res += user[2] + "\n";
        res += user[3] + "\n\n";
    return res

@dp.message(F.text.lower() == "список зарегистрированных")
async def list_of_users(message: Message):
    if message.from_user.id not in admins_list:
        await message.answer(
                "Вы не имеете доступ к этой информации"
                )
        return
    await message.answer(generate_message(get_users_list()))


async def main():
    init_db()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
