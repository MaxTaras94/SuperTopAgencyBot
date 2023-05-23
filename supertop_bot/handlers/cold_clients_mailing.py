import asyncio
from supertop_bot.handlers.keyboards import keyboard_manager_menu
from supertop_bot.services.googlesheetapi import googlesheetapi
from supertop_bot.services.useful_functions import generate_links_for_sharing
from telegram import  Chat, InputMediaPhoto,  InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from typing import cast
import time



async def consent_start_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    keyboard = [[InlineKeyboardButton('Начать рассылку', callback_data='start_cold_mailing')], [InlineKeyboardButton('Изменить список моделей', callback_data='change_list_of_models')]]
    text_for_mailing = update.message.text
    reply_markup = InlineKeyboardMarkup(keyboard)
    faile_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Изменить список моделей', callback_data='change_list_of_models')]])
    context.user_data[f"id_models_for_cold_mailing_{cast(Chat, update.effective_chat).id}"] = text_for_mailing
    check_data_for_mailing = {}
    for id_model in text_for_mailing.split(','):
        try:
            googlesheetapi.get_link_to_portfolio_of_model(id_model=int(id_model))
            check_data_for_mailing[id_model] = True
        except:
            check_data_for_mailing[id_model] = False
    id_models_brake = []
    for key, value in check_data_for_mailing.items(): 
        if not value:
            id_models_brake.append(key)
    if len(id_models_brake) > 0:
        await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=f"Получен список моделей: <b>{text_for_mailing}</b>, но в БД нет маделей с такими ID: <b>{','.join(id_models_brake)}</b>", reply_markup=faile_markup, parse_mode='HTML')
        return "CHOOSE_ID_MODELS_FOR_MAILING"
    else:
        await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=f"Получен список моделей: <b>{text_for_mailing}</b>", reply_markup=reply_markup, parse_mode='HTML')
        return "START_MAILING"

async def start_mailing_cold_clients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler:
    '''Функция делает рассылку на всех холодных клиентов по портфолио моделей'''
    id_models_for_mailing = context.user_data.get(f'id_models_for_cold_mailing_{cast(Chat, update.effective_chat).id}', 'Not found').split(',')
    id_clients_for_mailing = googlesheetapi.get_id_clients_for_mailing() 
    markup = ReplyKeyboardMarkup(keyboard_manager_menu, one_time_keyboard=False, resize_keyboard=True)
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=f"Начинаю рассылку по клиентам следующих моделей: <b>{','.join(id_models_for_mailing)}</b>", reply_markup=markup, parse_mode='HTML')
    for client_id in id_clients_for_mailing:
        for num, id_model in enumerate(id_models_for_mailing):      
            caption_text, link_potrfolio = googlesheetapi.get_link_to_portfolio_of_model(id_model=id_model)
            links_potrfolio_photo = generate_links_for_sharing(googlesheetapi.get_models_photo(link_potrfolio))
            media_group = [InputMediaPhoto(media=photo) for photo in links_potrfolio_photo]
            
            await context.bot.send_message(chat_id=cast(Chat, client_id), text=f"<b>Модель №{num+1}</b>\n"+caption_text, reply_markup=markup, parse_mode='HTML')
            await context.bot.send_media_group(chat_id=cast(Chat, client_id),
                                                media=media_group, 
                                                protect_content=False)
        keyboard = [
            [InlineKeyboardButton(f"Понравилась модель №{num+1}", callback_data=f"ordermodel_{id_model}")] for num,id_model in enumerate(id_models_for_mailing)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await asyncio.sleep(20)
        await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text="Вам понравились наши модели?🔥", reply_markup=reply_markup)
    return ConversationHandler.END