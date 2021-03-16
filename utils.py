from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
import sqlite3
from datetime import datetime


class States(StatesGroup):
    IDLE = State()
    LANGUAGE = State()
    AGE = State()
    GENDER = State()
    FIND_GENDER = State()
    LOCATION = State()
    NAME = State()
    DESCRIPTION = State()
    PHOTO = State()
    RESULT = State()
    FIND = State()


def get_keyboard(current_set: str):
    """
    Возвращает настроенную клавиатуру

    param: language, gender, findGender, description, remove
    """

    if current_set == "remove":
        return ReplyKeyboardRemove()

    buttons = {
        "language": ("Русский",),
        "gender": ("Мужской", "Женский"),
        "find_gender": ("Мужчину", "Женщину", "Всё равно"),
        "description": ("Пропустить",),
        "result_question": ("Да", "Изменить анкету")
    }
    assert current_set in buttons, "Такого набора клавиатур нет"

    current_kb = ReplyKeyboardMarkup(resize_keyboard=True)

    current_kb.add(*buttons[current_set])
    return current_kb


def get_query(type_query: str, query: str, values: tuple):
    """
    Запрос в БД

    Если select, возвращает cursor.fetchall() \n
    Если insert, update, delete, возвращает True \n
    Если возникает ошибка, возвращает error
    """

    try:
        con = sqlite3.connect("main.db")
        cursor = con.cursor()
        cursor.execute(query, values)

        if type_query == "select":
            result_select = cursor.fetchall()
            con.close()
            return result_select
        elif type_query in ("insert", "update", "delete"):
            con.commit()
            con.close()
            return True

    except sqlite3.Error as error:
        with open("errorDB.txt", "a") as f:
            date = '{:%d-%m-%Y %H:%M:%S}'.format(datetime.now())
            f.write(f"{date}: {error} \n")
        return "error"

