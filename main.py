import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup
from dotenv import load_dotenv

from database import Database
from email_handler import EmailHandler

load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)

db = Database()

class Form(StatesGroup):
    imap_server = State()
    imap_port = State()
    email = State()
    password = State()

def get_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Войти в почту", "Указать IMAP", "Указать логин и пароль",
               "Сброс логин и пароль", "Сброс общий"]
    keyboard.add(*buttons)
    return keyboard

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Это бот для работы с почтой. Выбери действие:", reply_markup=get_keyboard())

@dp.message_handler(lambda message: message.text == "Указать IMAP")
async def set_imap(message: types.Message):
    await Form.imap_server.set()
    await message.reply("Укажи IMAP сервер:")

@dp.message_handler(state=Form.imap_server)
async def process_imap_server(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['imap_server'] = message.text
    await Form.next()
    await message.reply("Теперь укажи порт IMAP-сервера:")

@dp.message_handler(state=Form.imap_port)
async def process_imap_port(message: types.Message, state: FSMContext):
    try:
        port = int(message.text)
        async with state.proxy() as data:
            data['imap_port'] = port
        user_data = db.get_user_data(message.from_user.id)
        if user_data:
            db.save_user_data(message.from_user.id, data['imap_server'], data['imap_port'],
                              user_data[3], user_data[4])
        else:
            db.save_user_data(message.from_user.id, data['imap_server'], data['imap_port'],
                              None, None)
        await state.finish()
        await message.reply("IMAP-данные сохранены.", reply_markup=get_keyboard())
    except ValueError:
        await message.reply("Порт должен быть числом. Попробуйте снова.")

@dp.message_handler(lambda message: ":" in message.text and message.text.count(":") == 1)  # Проверяем, что в сообщении есть ровно одно двоеточие
async def set_email_password(message: types.Message, state: FSMContext):
    email, password = message.text.split(":")
    async with state.proxy() as data:
        data['email'] = email.strip()
        data['password'] = password.strip()
    user_data = db.get_user_data(message.from_user.id)
    if user_data:
        db.save_user_data(message.from_user.id, user_data[1], user_data[2],
                          data['email'], data['password'])
    await message.reply("Логин и пароль сохранены.", reply_markup=get_keyboard())

@dp.message_handler(lambda message: message.text == "Войти в почту")
async def login_email(message: types.Message):
    user_data = db.get_user_data(message.from_user.id)
    if not user_data or None in user_data:
        await message.reply("Сначала укажи IMAP сервер, логин и пароль.")
        return

    imap_server, port, email_address, email_password = user_data[1:]
    if email_address and email_password:
        email_handler = EmailHandler(imap_server, port, email_address, email_password)
        try:
            emails = email_handler.get_emails()
            if emails:
                for i, email_content in enumerate(emails, 1):
                    await message.reply(f"Письмо {i}:\n\n{email_content}", parse_mode=None)
            else:
                await message.reply("Нет новых писем.")
        except Exception as e:
            await message.reply(f"Ошибка при подключении к почте: {str(e)}")
    else:
        await message.reply("Укажите логин и пароль для входа в почту.", reply_markup=get_keyboard())

@dp.message_handler(lambda message: message.text == "Сброс логин и пароль")
async def reset_credentials(message: types.Message):
    user_data = db.get_user_data(message.from_user.id)
    if user_data:
        db.save_user_data(message.from_user.id, user_data[1], user_data[2], None, None)
        await message.reply("Логин и пароль сброшены. Укажи новые логин и пароль.",
                            reply_markup=get_keyboard())
    else:
        await message.reply("Данные не найдены.")

@dp.message_handler(lambda message: message.text == "Сброс общий")
async def reset_all(message: types.Message):
    db.reset_user_data(message.from_user.id)
    await message.reply("Все настройки сброшены. Укажи заново IMAP, логин и пароль.",
                        reply_markup=get_keyboard())

if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)