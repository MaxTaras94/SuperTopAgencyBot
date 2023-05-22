from typing import cast

from telegram import Update, User
from telegram.ext import ContextTypes, ConversationHandler

from supertop_bot.handlers.response import send_response
from supertop_bot.templates import render_template


async def error_message_recognition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_response(update, context, response=render_template("error_message_recognition.j2"))
    return ConversationHandler.END

