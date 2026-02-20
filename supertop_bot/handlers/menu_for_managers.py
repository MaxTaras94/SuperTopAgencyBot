from supertop_bot.handlers.response import send_response
from supertop_bot.services.googlesheetapi import googlesheetapi
from supertop_bot.handlers.keyboards import keyboard_manager_menu, keyboard_manager_menu_models, keyboard_manager_menu_clients
from supertop_bot.templates import render_template
from telegram import Chat, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from typing import cast


async def menu_models(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Раздел меню Модели для менеджера"""
    markup = ReplyKeyboardMarkup(keyboard_manager_menu_models, one_time_keyboard=True, resize_keyboard=True)
    await send_response(update, context, keyboard=markup, response=render_template("choose_action.j2"))
    
async def menu_clients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Раздел меню Клиенты для менеджера"""
    markup = ReplyKeyboardMarkup(keyboard_manager_menu_clients, one_time_keyboard=True, resize_keyboard=True)
    managers_id_tg = googlesheetapi.get_tg_id_managers()
    print(managers_id_tg)
    if cast(Chat, update.effective_chat).id in [570451645, 449441982, 188902033]:
        await send_response(update, context, keyboard=markup, response=render_template("choose_action.j2")) 
    else:
        markup = ReplyKeyboardMarkup([[KeyboardButton(text="Назад")]], one_time_keyboard=True, resize_keyboard=True)
        await send_response(update, context, keyboard=markup, response=render_template("permission_denied.j2")) 
    return ConversationHandler.END
    
async def come_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вернуться в меню менеджера"""
    markup = ReplyKeyboardMarkup(keyboard_manager_menu, one_time_keyboard=True, resize_keyboard=True)
    await send_response(update, context, keyboard=markup, response=render_template("main_menu.j2")) 
    return ConversationHandler.END