from supertop_bot.handlers.response import send_response
from supertop_bot.handlers.keyboards import keyboard_manager_menu
from supertop_bot.services.googlesheetapi import googlesheetapi
from supertop_bot.services.useful_functions import generate_links_for_sharing
from supertop_bot.templates import render_template
from telegram import Chat, Update, InputMediaPhoto, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from typing import cast


async def choose_params_id_or_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция отправляет портфолио модели в чат пользователю"""
    query = update.callback_query.data
    await context.bot.delete_message(cast(Chat, update.effective_chat).id, update.callback_query.message.message_id)
    if query == "idmodel":        
        await send_response(update, context, response=render_template("input_id_model.j2"))    
        return "SEND_PHOTOS_BY_ID"
    else:
        await send_response(update, context, response=render_template("input_phone_model.j2"))
        return "SEND_PHOTOS_BY_PHONE"
    
async def send_photos_of_models_potrfolio_for_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция отправляет портфолио модели в чат пользователю по переданному id модели"""
    id_model = update.message.text
    caption_text, link_potrfolio = googlesheetapi.get_link_to_portfolio_of_model(id_model=id_model)
    print(caption_text, link_potrfolio)
    links_photo = generate_links_for_sharing(googlesheetapi.get_models_photo(link_potrfolio))
    media_group = []
    markup = ReplyKeyboardMarkup(keyboard_manager_menu, one_time_keyboard=False, resize_keyboard=True)
    for photo in links_photo:
        media_group.append(InputMediaPhoto(media=photo))
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=caption_text, reply_markup =markup)
    await context.bot.send_media_group(chat_id=cast(Chat, update.effective_chat).id, media=media_group, protect_content=False)
    return ConversationHandler.END

    
async def send_photos_of_models_potrfolio_for_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция отправляет портфолио модели в чат пользователю по переданному номеру телефона модели"""
    phone_number = update.message.text
    caption_text, link_potrfolio = googlesheetapi.get_link_to_portfolio_of_model(phone_number=phone_number)
    links_photo = generate_links_for_sharing(googlesheetapi.get_models_photo(link_potrfolio))
    media_group = []
    markup = ReplyKeyboardMarkup(keyboard_manager_menu, one_time_keyboard=False, resize_keyboard=True)
    for photo in links_photo:
        media_group.append(InputMediaPhoto(media=photo))
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=caption_text, reply_markup =markup)
    await context.bot.send_media_group(chat_id=cast(Chat, update.effective_chat).id, media=media_group, protect_content=False)
    return ConversationHandler.END