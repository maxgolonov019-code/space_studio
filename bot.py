import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

TOKEN = getenv("BOT_TOKEN", "9298800668:AAEAt0VqEFMzfGybIyHOydoZrypRVOUTU5E")
SUPPORT_CHAT = "https://t.me/space_technical_support_chat"
MANAGER_USERNAME = "@space_technical_support_chat"  # для упоминания в сообщениях

dp = Dispatcher()


# ---------- Состояния для записи ----------
class Consult(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_topic = State()


class DecorCall(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
    waiting_description = State()


# ---------- Главное меню (reply-кнопки) ----------
def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться на консультацию")],
            [KeyboardButton(text="🛋 Вызвать специалиста по декору")],
            [KeyboardButton(text="💬 Чат поддержки")],
        ],
        resize_keyboard=True,
    )
    return kb


# ---------- /start ----------
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    text = (
        f"Здравствуйте, {html.bold(message.from_user.full_name)}! 👋\n\n"
        "Это бот студии декора <b>Space Studio</b>.\n\n"
        "Я помогу вам:\n"
        "• 📅 записаться на консультацию дизайнера;\n"
        "• 🛋 вызвать специалиста, чтобы он приехал и задекорировал пространство (платная услуга);\n"
        "• 💬 перейти в чат поддержки.\n\n"
        f"Если нужен живой человек — пишите в чат: {MANAGER_USERNAME}\n"
        "Или нажмите кнопку ниже."
    )

    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Перейти в чат поддержки", url=SUPPORT_CHAT)],
            [InlineKeyboardButton(text="📅 Консультация", callback_data="consult")],
            [InlineKeyboardButton(text="🛋 Вызвать декоратора", callback_data="decor")],
        ]
    )

    await message.answer(text, reply_markup=inline)
    await message.answer("Выберите действие в меню ниже:", reply_markup=main_menu())


# ---------- Переход в чат поддержки (кнопка reply) ----------
@dp.message(F.text == "💬 Чат поддержки")
async def support_chat(message: Message):
    await message.answer(
        f"Переходите в чат поддержки: {SUPPORT_CHAT}\n"
        f"Там вам ответит наш специалист.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Открыть чат", url=SUPPORT_CHAT)]
            ]
        ),
    )


# ---------- Консультация ----------
@dp.message(F.text == "📅 Записаться на консультацию")
@dp.callback_query(F.data == "consult")
async def consult_start(event, state: FSMContext):
    await state.set_state(Consult.waiting_name)

    text = (
        "📅 <b>Запись на консультацию</b>\n\n"
        "Консультация проходит в чате или по видеосвязи с дизайнером.\n"
        "Стоимость: <b>бесплатно</b> (первичная, 30 минут).\n\n"
        "Как вас зовут?"
    )

    if isinstance(event, CallbackQuery):
        await event.message.answer(text)
        await event.answer()
    else:
        await event.answer(text)


@dp.message(Consult.waiting_name)
async def consult_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Consult.waiting_phone)
    await message.answer("Укажите телефон или Telegram-ник для связи:")


@dp.message(Consult.waiting_phone)
async def consult_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Consult.waiting_topic)
    await message.answer("О чём хотите поговорить? Кратко опишите задачу:")


@dp.message(Consult.waiting_topic)
async def consult_topic(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(topic=message.text)
    await state.clear()

    summary = (
        "✅ <b>Заявка на консультацию принята</b>\n\n"
        f"Имя: {html.quote(data['name'])}\n"
        f"Контакт: {html.quote(data['phone'])}\n"
        f"Тема: {html.quote(message.text)}\n\n"
        "Мы свяжемся с вами в течение рабочего дня.\n"
        f"Или напишите сами: {SUPPORT_CHAT}"
    )

    await message.answer(
        summary,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💬 Чат поддержки", url=SUPPORT_CHAT)],
                [InlineKeyboardButton(text="🏠 В меню", callback_data="menu")],
            ]
        ),
        parse_mode=ParseMode.HTML,
    )


# ---------- Вызов специалиста по декору ----------
@dp.message(F.text == "🛋 Вызвать специалиста по декору")
@dp.callback_query(F.data == "decor")
async def decor_start(event, state: FSMContext):
    await state.set_state(DecorCall.waiting_name)

    text = (
        "🛋 <b>Вызов специалиста по декору</b>\n\n"
        "Это <b>платная услуга</b>. Специалист приедет, оценит пространство "
        "и предложит варианты декора.\n\n"
        "Стоимость выезда и работы обсуждается индивидуально после уточнения задачи.\n\n"
        "Как вас зовут?"
    )

    if isinstance(event, CallbackQuery):
        await event.message.answer(text)
        await event.answer()
    else:
        await event.answer(text)


@dp.message(DecorCall.waiting_name)
async def decor_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(DecorCall.waiting_phone)
    await message.answer("Телефон или Telegram для связи:")


@dp.message(DecorCall.waiting_phone)
async def decor_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(DecorCall.waiting_address)
    await message.answer("Адрес, куда нужно приехать (город, улица, дом):")


@dp.message(DecorCall.waiting_address)
async def decor_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(DecorCall.waiting_description)
    await message.answer("Опишите, что нужно задекорировать (комната, площадь, пожелания):")


@dp.message(DecorCall.waiting_description)
async def decor_description(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(description=message.text)
    await state.clear()

    summary = (
        "✅ <b>Заявка на вызов специалиста принята</b>\n\n"
        f"Имя: {html.quote(data['name'])}\n"
        f"Контакт: {html.quote(data['phone'])}\n"
        f"Адрес: {html.quote(data['address'])}\n"
        f"Задача: {html.quote(message.text)}\n\n"
        "Услуга платная — менеджер свяжется с вами, "
        "уточнит детали и назовёт стоимость.\n"
        f"Чат поддержки: {SUPPORT_CHAT}"
    )

    await message.answer(
        summary,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💬 Чат поддержки", url=SUPPORT_CHAT)],
                [InlineKeyboardButton(text="🏠 В меню", callback_data="menu")],
            ]
        ),
        parse_mode=ParseMode.HTML,
    )


# ---------- Возврат в меню ----------
@dp.callback_query(F.data == "menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Главное меню:", reply_markup=main_menu())
    await callback.answer()


# ---------- Запуск ----------
async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
