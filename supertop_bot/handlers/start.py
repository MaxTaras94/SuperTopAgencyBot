from telegram import Chat, Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from typing import cast
from supertop_bot.handlers.keyboards import keyboard_manager_menu
from supertop_bot.handlers.response import send_response
from supertop_bot.services.googlesheetapi import googlesheetapi
from supertop_bot.templates import render_template


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = googlesheetapi.check_access(cast(Chat, update.effective_chat).id)
    if update.message.text == "Повторить аутентификацию":
        await send_response(update, context, response=render_template("start_notauth_retry.j2"))
    if data['access'] and data['dataUser']['role'] == "Менеджеры":
        markup = ReplyKeyboardMarkup(keyboard_manager_menu, one_time_keyboard=False, resize_keyboard=True)
        await send_response(update, context, keyboard=markup, response=render_template("start_auth.j2"))
        return ConversationHandler.END
    elif data['access'] and data['dataUser']['role'] != "Менеджеры":
        await send_response(update, context, response=render_template("start_auth.j2"))
        return ConversationHandler.END
    elif not data['access'] and update.message.text == "/start":
        await send_response(update, context, response=render_template("start_notauth.j2"))
    return 'PHONE_NUMBER'