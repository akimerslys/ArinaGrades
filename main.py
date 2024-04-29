import datetime
import json

from aiogram import Bot, F, Dispatcher
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardBuilder, InlineKeyboardMarkup

import config
from config import subjects_9_grade, marks, key, admin_users

from loguru import logger
from logg import LoggingMiddleware

from config import token, redis_pass, redis_ip
from redis.asyncio import Redis

bot = Bot(token=token)
redis_client = Redis(
        host=redis_ip,
        password=redis_pass,
        port=6379,
    )

dp = Dispatcher(bot=bot)


def marks_kb(id_):
    keyboard = InlineKeyboardBuilder()
    for i in range(11):
        keyboard.add(InlineKeyboardButton(text=str(i + 2), callback_data=f"subject_mark_{id_}_{i + 2}"))
    keyboard.add(InlineKeyboardButton(text='❌ Видалити Невідомі', callback_data=f"subject_mark_{id_}_-2"))
    keyboard.add(InlineKeyboardButton(text='❓ Невідомо', callback_data=f"subject_mark_{id_}_-1"))

    keyboard.add(InlineKeyboardButton(text='Назад', callback_data=f"subjects_menu"))
    keyboard.adjust(3, 3, 3, 2, 2, 1)
    return keyboard.as_markup(resize_keyboard=True)


def subjects_kb():
    keyboard = InlineKeyboardBuilder()
    for i, subject in enumerate(subjects_9_grade, start=0):
        button = InlineKeyboardButton(text=subject, callback_data=f"subject_id_{i}")
        keyboard.add(button)
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)


def subject_kb(id: int):
    id = str(id)
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=marks[0] + ' Очистити', callback_data=f"subject_status_{id}_0"))
    keyboard.add(InlineKeyboardButton(text=marks[1] + ' Оновити', callback_data=f"subject_status_{id}_1"))
    keyboard.add(InlineKeyboardButton(text='✅ Закрити', callback_data=f"subject_mark_{id}_0"))
    #keyboard.add(InlineKeyboardButton(text='123', callback_data=f"subject_status_{id}_3"))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data=f"subjects_menu"))
    keyboard.adjust(3, 1)
    return keyboard.as_markup(resize_keyboard=True)


async def get_text(subjects: dict | None = None):
    text = 'Оцінки:\n\n'
    if not subjects:
        redis_ff = await redis_client.get(key)
        subjects = json.loads(redis_ff)
    for i, subject in enumerate(subjects_9_grade, start=0):
        str_i = str(i)
        marks = ((', '.join([str(x) for x in subjects[str_i][1:]])).replace('-1', '?') +
                                     (' (сер. бал ' + str(subjects[str_i][0]) + ')' if subjects[str_i][0] > 1 else ''))

        text += f"{marks[subjects[str_i][0]]} {subject}:  {marks}\n"
    return text


@dp.callback_query(F.data.startswith('subject_id_'))
async def subject_id(call: CallbackQuery):
    id = int(call.data.split('_')[-1])
    text = 'Стан предмета ' + subjects_9_grade[id] + ':\n'
    await call.message.edit_text(text, reply_markup=subject_kb(id))


@dp.callback_query(F.data.startswith('subject_status_'))
async def update_subject(call: CallbackQuery):
    if call.from_user.id not in admin_users:
        await call.answer('Ви не Аріна!', show_alert=True)
        return
    data = call.data.split('_')
    id_, status = data[-2], data[-1]

    if status == '0':
        subjects = json.loads(await redis_client.get(key))
        subjects[id_] = [0]
        await redis_client.set(key, json.dumps(subjects))

        text = await get_text(subjects)
        await call.message.edit_text(text, reply_markup=subjects_kb())
        return
    await call.message.edit_text('Вибери оцінку для', reply_markup=marks_kb(id_))


@dp.callback_query(F.data.startswith('subject_mark_'))
async def update_mark(call: CallbackQuery):

    def get_avg(marks):
        summ = sum(marks[1:])
        lenn = len(marks[1:])
        array_avg = round(summ / lenn)
        return array_avg

    data = call.data.split('_')
    id_, mark = data[-2], int(data[-1])

    subjects = json.loads(await redis_client.get(key))

    if mark == -2:
        subjects[id_] = list(filter(lambda x: x != -1, subjects[id_]))
    elif mark == 0:
        if -1 in subjects[id_]:
            await call.answer('Ви не можете закрити предмет поки є невідомі оцінки', show_alert=True)
            return
        if len(subjects[id_]) < 2:
            await call.answer('НЕМА ОЦІНОК', show_alert=True)
        subjects[id_][0] = get_avg(subjects[id_])
    else:
        # -1 and normal mark
        subjects[id_][0] = 1
        subjects[id_].append(mark)

    await redis_client.set(key, json.dumps(subjects))
    text = await get_text(subjects)
    await call.message.edit_text(text, reply_markup=subjects_kb())


@dp.message()
async def subjects(message: Message):
    text = await get_text()
    await message.answer(text, reply_markup=subjects_kb())


@dp.callback_query()
async def subjects_call(call: CallbackQuery):
    text = await get_text()
    await call.message.edit_text(text, reply_markup=subjects_kb())


async def setup_db():
    val = {}
    for i, subj in enumerate(config.subjects_9_grade, start=0):
        val[str(i)] = [0]
    await redis_client.set(key, json.dumps(val))


async def on_startup() -> None:
    logger.info("bot starting...")

    await setup_db()

    dp.update.outer_middleware(LoggingMiddleware())

    logger.success(f"Bot Started, UTC time {datetime.datetime.utcnow()}")


async def on_shutdown() -> None:

    logger.warning("bot stopping...")

    await bot.session.close()

    logger.warning("bot stopped")


async def main() -> None:

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
