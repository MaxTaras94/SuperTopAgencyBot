from supertop_bot.handlers.response import send_response
from supertop_bot.handlers.keyboards import keyboard_manager_menu
from supertop_bot.services.googlesheetapi import googlesheetapi
from supertop_bot.templates import render_template
from telegram import Chat, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from typing import cast


async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем от пользователя номер телефона и передаём на проверку"""
    phone_number = update.message.text
    reply_keyboard = [["Повторить аутентификацию"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    msg = await send_response(update, context, response=render_template("wait.j2"))
    data = googlesheetapi.check_user_by_phone_number(phone_number, cast(Chat, update.effective_chat).id)
    if data['access']:
        await context.bot.delete_message(cast(Chat, update.effective_chat).id, msg.message_id)
        if data['dataUser']['role'] == "Менеджеры":
            markup = ReplyKeyboardMarkup(keyboard=keyboard_manager_menu, one_time_keyboard=False, resize_keyboard=True)
            await send_response(update, context, keyboard=markup, response=render_template("user_added_to_db.j2")) 
        else:
            await send_response(update, context, keyboard=ReplyKeyboardRemove(), response=render_template("user_added_to_db.j2")) 
    else:
        await context.bot.delete_message(cast(Chat, update.effective_chat).id, msg.message_id)
        await send_response(update, context, keyboard=markup, response=render_template("access_denied.j2"))
    return ConversationHandler.END