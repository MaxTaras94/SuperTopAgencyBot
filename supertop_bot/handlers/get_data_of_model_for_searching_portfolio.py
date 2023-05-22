from supertop_bot.handlers.response import send_response
from supertop_bot.templates import render_template
from telegram import Chat, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from typing import cast


async def choose_parametres_for_searching_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция отправляет в чат пользователю предложение выбрать параметр, по которому будет искаться портофлио модели"""
    buttons = [
        [
            InlineKeyboardButton(text="ID модели", callback_data="idmodel"),
            InlineKeyboardButton(text="Моб. номер модели", callback_data="phnummod")
        ]]
    keyboard = InlineKeyboardMarkup(buttons)
    await send_response(update, context, keyboard=keyboard, response=render_template("parametr_for_searching_portfolio.j2")) 
    return "CHOOSE_PARAMS_ID_OR_PHONE"
