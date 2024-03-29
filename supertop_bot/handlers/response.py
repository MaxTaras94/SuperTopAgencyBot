from typing import cast

import telegram
from telegram import Chat, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes


async def send_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    response: str,
    keyboard: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove |None = None,
    protect_content=False
) -> None:
    args = {
        "chat_id": _get_chat_id(update),
        "disable_web_page_preview": True,
        "text": response,
        "parse_mode": 'HTML',
        "protect_content": protect_content
    }
    if keyboard:
        args["reply_markup"] = keyboard

    msg = await context.bot.send_message(**args)
    return msg

def _get_chat_id(update: Update) -> int:
    return cast(Chat, update.effective_chat).id
