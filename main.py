import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

API_TOKEN = '8017118025:AAHb_hxP6N0ffLELWMj0riXGIlpMAZ7erz4'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Словник для бронювань
bookings = {}


# Стани
class BookingState(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()


# Обробка команди /start
@dp.message(Command("start"))
async def start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Забронювати місце 🏠", callback_data="book")],
        [InlineKeyboardButton(text="Переглянути календар 📅", callback_data="calendar")]
    ])
    await message.answer("Привіт! Вибери дію:", reply_markup=markup)


# Обробка вибору "Забронювати місце"
@dp.callback_query(F.data == "book")
async def ask_name(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, "Введіть своє ім'я для бронювання:")
    await state.set_state(BookingState.waiting_for_name)


# Обробка введення імені
@dp.message(BookingState.waiting_for_name)
async def ask_date(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=(datetime.today() + timedelta(days=i)).strftime("%d.%m.%Y"),
                              callback_data=f"book_date_{(datetime.today() + timedelta(days=i)).strftime('%Y-%m-%d')}")]
        for i in range(7)
    ])
    await message.answer("Оберіть дату для бронювання:", reply_markup=markup)
    await state.set_state(BookingState.waiting_for_date)


# Обробка вибору дати
@dp.callback_query(F.data.startswith('book_date'))
async def ask_start_time(callback_query: CallbackQuery, state: FSMContext):
    date = callback_query.data.split('_')[2]
    await state.update_data(date=date)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{hour}:00", callback_data=f"start_time_{hour}:00")]
        for hour in range(8, 22)
    ])
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, "Оберіть початок бронювання:", reply_markup=markup)
    await state.set_state(BookingState.waiting_for_start_time)


# Обробка вибору початкового часу
@dp.callback_query(F.data.startswith('start_time'))
async def ask_end_time(callback_query: CallbackQuery, state: FSMContext):
    start_time = callback_query.data.split('_')[2]
    await state.update_data(start_time=start_time)
    start_hour = int(start_time.split(':')[0])
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"До {hour}:00", callback_data=f"end_time_{hour}:00")]
        for hour in range(start_hour + 1, 23)
    ])
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, "Оберіть кінець бронювання:", reply_markup=markup)
    await state.set_state(BookingState.waiting_for_end_time)


# Обробка вибору кінцевого часу
@dp.callback_query(F.data.startswith('end_time'))
async def confirm_booking(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    name = user_data.get("name", "Невідомий")
    date = user_data.get("date", "Невідома дата")
    start_time = user_data.get("start_time", "Невідомо")
    end_time = callback_query.data.split('_')[2]
    bookings[f"{name} ({date})"] = f"{start_time} - {end_time}"

    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id,
                           f"Бронювання підтверджено для {name} на {date} з {start_time} до {end_time}.")
    await state.clear()

    # Показати кнопки вибору після бронювання
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Забронювати місце 🏠", callback_data="book")],
        [InlineKeyboardButton(text="Переглянути календар 📅", callback_data="calendar")]
    ])
    await bot.send_message(callback_query.from_user.id, "Що хочете зробити далі?", reply_markup=markup)


# Перегляд календаря
@dp.callback_query(F.data == "calendar")
async def view_calendar(callback_query: CallbackQuery):
    calendar = "\n".join([f"{name}: {time}" for name, time in bookings.items()]) if bookings else "Немає бронювань."
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, f"Ось календар бронювань:\n{calendar}")


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
