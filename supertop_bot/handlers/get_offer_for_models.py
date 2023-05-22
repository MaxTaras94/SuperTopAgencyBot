from telegram import  Chat, ReplyKeyboardMarkup, Update, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from typing import cast
import time



async def get_offer_job_for_models(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    markup = ReplyKeyboardMarkup([[KeyboardButton(text="Назад")]], one_time_keyboard=False, resize_keyboard=True)
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text="Ведутся работы🛠⛔️", reply_markup=markup, parse_mode='HTML')
