from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext

from config import TOKEN
from mybot.messages import MESSAGES
from mybot.utils import States, get_keyboard, get_query

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(state="*", commands=['test'])
async def test(msg: types.Message):
    pass


@dp.message_handler(state="*", commands=['start'])
async def command_start(msg: types.Message):
    user_id = msg.from_user.id
    # state = dp.current_state(user=user_id) # ???

    result = get_query("select", "SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if result == "error":
        await msg.answer(MESSAGES['errorDB'])
    elif len(result):
        result = get_query("select", "SELECT * FROM users_info WHERE user_id = ?", (user_id,))
        if result == "error":
            await msg.answer(MESSAGES['errorDB'], reply_markup=get_keyboard("remove"))
        elif len(result):
            await States.FIND.set()
            await msg.answer("Первая анкета")
        else:
            await msg.answer(text="Выберите язык", reply_markup=get_keyboard("language"))
            await States.LANGUAGE.set()
    else:
        result = get_query("insert", "INSERT INTO users (user_id) VALUES(?)", (user_id,))
        if result == "error":
            await msg.answer(MESSAGES['errorDB'])
        else:
            await msg.answer(text="Выберите язык", reply_markup=get_keyboard("language"))
            await States.LANGUAGE.set()


@dp.message_handler(state="*", commands=['help'])
async def command_help(msg: types.Message):
    await msg.answer(text=MESSAGES['command_help'])


@dp.message_handler(state="*", commands=['stop'])
async def command_stop(msg: types.Message):
    user_id = msg.from_user.id

    result = get_query("delete", "DELETE FROM users WHERE user_id = ?", (user_id,))
    if result == "error":
        await msg.answer(MESSAGES['errorDB'])
    else:
        result = get_query("delete", "DELETE FROM users_info WHERE user_id = ?", (user_id,))
        if result == "error":
            await msg.answer(MESSAGES['errorDB'])
        else:
            await msg.answer("Все данные удалены", reply_markup=get_keyboard("remove"))


@dp.message_handler(state=States.LANGUAGE)
async def get_language(msg: types.Message, state: FSMContext):
    language = msg.text.lower()
    if language in ("русский", "русский"):
        async with state.proxy() as data:
            data['language'] = msg.text
        await States.AGE.set()
        await msg.answer("Сколько Вам лет?", reply_markup=get_keyboard("remove"))
    else:
        await msg.answer("Используйте варианты клавиатуры")


@dp.message_handler(state=States.AGE)
async def get_age(msg: types.Message, state: FSMContext):
    age = msg.text
    if not age.isdigit():
        await msg.answer("Укажите возраст числом")
    else:
        if int(age) < 16:
            await msg.answer("К нам можно только с 16 лет")
        elif int(age) > 100:
            await msg.answer("Столько не живут")
        else:
            async with state.proxy() as data:
                data['age'] = msg.text
            await States.GENDER.set()
            await msg.answer("Ваш пол?", reply_markup=get_keyboard("gender"))


@dp.message_handler(state=States.GENDER)
async def get_gender(msg: types.Message, state: FSMContext):
    gender = msg.text.lower()
    if gender in ("мужской", "женский"):
        async with state.proxy() as data:
            data['gender'] = gender
        await States.FIND_GENDER.set()
        await msg.answer("Кого ищете?", reply_markup=get_keyboard("find_gender"))
    else:
        await msg.answer("Используйте варианты клавиатуры")


@dp.message_handler(state=States.FIND_GENDER)
async def get_find_gender(msg: types.Message, state: FSMContext):
    find_gender = msg.text.lower()
    if find_gender in ("мужчину", "женщину", "всё равно"):
        async with state.proxy() as data:
            data['find_gender'] = find_gender
        await States.LOCATION.set()
        await msg.answer("Откуда Вы?", reply_markup=get_keyboard("remove"))
    else:
        await msg.answer("Используйте варианты клавиатуры")


@dp.message_handler(state=States.LOCATION)
async def get_location(msg: types.Message, state: FSMContext):
    location = msg.text
    if location.isalpha():
        async with state.proxy() as data:
            data['location'] = location
        await States.NAME.set()
        await msg.answer("Как Вас зовут?", reply_markup=get_keyboard("remove"))
    else:
        await msg.answer("Такого города не существует")


@dp.message_handler(state=States.NAME)
async def get_name(msg: types.Message, state: FSMContext):
    name = msg.text
    async with state.proxy() as data:
        data['name'] = name
    await States.DESCRIPTION.set()
    await msg.answer("Описание Вашей анкеты", reply_markup=get_keyboard("description"))


@dp.message_handler(state=States.DESCRIPTION)
async def get_description(msg: types.Message, state: FSMContext):
    description = msg.text
    async with state.proxy() as data:
        if description != "Пропустить":
            data['description'] = description
        else:
            data['description'] = ""
    await States.PHOTO.set()
    await msg.answer("Пришлите Ваше фото", reply_markup=get_keyboard("remove"))


@dp.message_handler(state=States.PHOTO, content_types=['photo'])
async def get_photo(msg: types.Message, state: FSMContext):

    file_id = msg.photo[1].file_id

    async with state.proxy() as data:
        data['photo_id'] = file_id

    await States.RESULT.set()

    # Если data['description'] НЕ пустой, то добавляем в caption, иначе не добавляем
    if data['description'] != "":
        caption = data['name'] + ", " + data['age'] + ", " + data['location'] + "\n\n" + data['description']
    else:
        caption = data['name'] + ", " + data['age'] + ", " + data['location']

    await msg.answer_photo(file_id, caption)
    await msg.answer("Всё верно?", reply_markup=get_keyboard("result_question"))


@dp.message_handler(state=States.PHOTO, content_types=['audio', 'document', 'game', 'sticker', 'video', 'video_note',
                                                       'voice', 'contact', 'location', 'venue', 'poll', 'dice',
                                                       'new_chat_members', 'left_chat_member', 'invoice',
                                                       'successful_payment', 'connected_website', 'migrate_to_chat_id',
                                                       'migrate_from_chat_id', 'unknown', 'any', 'text'])
async def get_photo_wrong(msg: types.Message):
    await msg.answer("Пришлите фото")


@dp.message_handler(state=States.RESULT)
async def get_result(msg: types.Message, state: FSMContext):
    if msg.text == "Да":
        # file = msg.photo[1]
        # file_id = file.file_id

        async with state.proxy() as data:
            pass

        file_id = data['photo_id']
        file = await bot.get_file(file_id)
        await file.download("photo/" + file_id + ".jpg")

        query = "INSERT INTO users_info (user_id, language, age, gender, find_gender, location, name, description, photo_id, photo_path) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        user_id = msg.chat.id
        photo_path = "photo/" + file_id + ".jpg"
        values = (user_id, data['language'], data['age'], data['gender'], data['find_gender'], data['location'],
                  data['name'], data['description'], data['photo_id'], photo_path)
        result = get_query("insert", query, values)

        if result == "error":
            await msg.answer(MESSAGES['errorDB'])
        else:
            await States.FIND.set()
            await msg.answer("Первая анкета", reply_markup=get_keyboard("remove"))
    elif msg.text == "Изменить анкету":
        await States.AGE.set()
        await msg.answer("Сколько Вам лет?", reply_markup=get_keyboard("remove"))
    else:
        await msg.answer("Выберите вариант на клавиатуре")


if __name__ == '__main__':
    executor.start_polling(dp)
