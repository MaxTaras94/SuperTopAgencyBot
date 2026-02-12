from typing import cast

from telegram import Update, User
from telegram.ext import ContextTypes, ConversationHandler

from supertop_bot.handlers.response import send_response
from supertop_bot.templates import render_template


async def create_cold_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_response(update, context, response=render_template("input_id_models_for_cold_mailing.j2"))
    return "CHOOSE_ID_MODELS_FOR_MAILING"
    