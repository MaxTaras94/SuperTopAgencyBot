from typing import cast

from telegram import Update, User, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from supertop_bot.handlers.keyboards import keyboard_manager_menu
from supertop_bot.handlers.response import send_response
from supertop_bot.templates import render_template


async def error_message_recognition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markup_main_menu = ReplyKeyboardMarkup(keyboard_manager_menu, one_time_keyboard=False, resize_keyboard=True)
    await send_response(update, context, response=render_template("error_message_recognition.j2", {"keyboard": markup_main_menu}))
    return ConversationHandler.END

