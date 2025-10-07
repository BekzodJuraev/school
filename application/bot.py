from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.web_app_info import WebAppInfo
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.bot.api import TelegramAPIServer
from aiogram.dispatcher import FSMContext
import logging
import requests
import json

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

bot = Bot('1289185931:AAEGdoVik_p5rXlg1eQP8AZtMJ7er3-m4mw')
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(f"Здравствуйте {message.from_user.first_name}\nОставьте заявку!")



    #markup = types.InlineKeyboardMarkup()
    #user_id = message.from_user.id
    #user_name=message.from_user.first_name
    #payload = {
     #   'user_id': user_id,
      #  'user_name':user_name}

   # requests.post(url="https://53f7-217-30-171-58.ngrok-free.app/api_marketing/",json=payload)

    #await message.answer('Good!', reply_markup=markup)

@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def echo_all(message: types.Message):


    """
    This handler will be called for any message that is not a command.
    """
    # Get user's feedback
    feedback = message.text
    user_id = message.from_user.id
    user_name=message.from_user.first_name
    payload = {
        'id_user': user_id,
        'fullname': user_name,
        'text':feedback

        }

    requests.post(url="https://e598-217-30-171-58.ngrok-free.app/api/", json=payload)

    # Process the feedback (you can add your own logic here)

    # Send 'raxmat' as a response
    #await message.reply("raxmat")
    get = requests.get(url="https://e598-217-30-171-58.ngrok-free.app/api/")
    data=get.json()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    approve_button = types.InlineKeyboardButton('✅ Approve', callback_data='approve')

    keyboard.add(approve_button)
    await message.answer(f'Мы получили вашу заявку и рассмотрим ее в ближайшее время. Спасибо за обратную связь! Ждите ваша очередь {data}',reply_markup=keyboard)






if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
