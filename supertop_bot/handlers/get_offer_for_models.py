import pandas as pd
from supertop_bot.handlers.keyboards import keyboard_manager_menu
from supertop_bot.services.googlesheetapi import googlesheetapi
from supertop_bot.services.useful_functions import generate_links_for_sharing

from supertop_bot.templates import render_template

from telegram import  Chat, ReplyKeyboardMarkup, Update, KeyboardButton, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes, ConversationHandler
from typing import cast
import time



# async def get_offer_job_for_models(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    # markup = ReplyKeyboardMarkup([[KeyboardButton(text="Назад")]], one_time_keyboard=False, resize_keyboard=True)
    # await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text="Ведутся работы🛠⛔️", reply_markup=markup, parse_mode='HTML')
    # return "GET_JO"

async def get_offer_job_for_models(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    markup = ReplyKeyboardMarkup([[KeyboardButton(text="Назад")]], one_time_keyboard=False, resize_keyboard=True)
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text="Напиште сообщение с предложением о работе", reply_markup=markup, parse_mode='HTML')
    return "CHOOSE_MANAGER"
    
async def choose_manager_for_accepting_applications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    keyboard = [[InlineKeyboardButton('Дима', callback_data='Dima'), InlineKeyboardButton('Вика', callback_data='Vika')],
                [InlineKeyboardButton('Оля', callback_data='Olia'), InlineKeyboardButton('Артём', callback_data='Artem')],
                [InlineKeyboardButton('Надин', callback_data='Nadin')]]
    markup = InlineKeyboardMarkup(keyboard)
    audio_msg_id = update.message.message_id
    context.user_data[f"audio_msg_id"] = audio_msg_id
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=render_template("choose_manager_for_accepting_jo.j2"), reply_markup=markup, parse_mode='HTML') 
    return "GET_JO"
    
async def checking_data_for_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    context.user_data[f"responsible_manager"] = update.callback_query.data
    keyboard = [[InlineKeyboardButton('ТОП60', callback_data='top60'), InlineKeyboardButton('ТОП60 Вау', callback_data='top60omg')],[ InlineKeyboardButton('Отправить всем', callback_data='all_models')]]
    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=render_template("checking_jo.j2"), reply_markup=markup, parse_mode='HTML')   
    return "START_JO"
    

async def start_jo_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    categories_dict = {'top60': 'ТОП 60',
                       'top60omg': 'ТОП 60 вау',
                       'all_models': 'Все модели'}
    category_of_models = categories_dict[update.callback_query.data]
    context.user_data[f"category_of_models_{cast(Chat, update.effective_chat).id}"] = category_of_models
    keyboard = [[InlineKeyboardButton('Да', callback_data='startjo'), InlineKeyboardButton('Изменить задание', callback_data='change_jo')]]
    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=render_template("go_to_mailing_of_jo.j2", {"category": category_of_models}), reply_markup=markup, parse_mode='HTML')    
    return "SEND_JO"


async def send_jo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler:
    audio_msg_id = context.user_data.get("audio_msg_id", 0)
    category_of_models = context.user_data.get(f"category_of_models_{cast(Chat, update.effective_chat).id}", [])
    if audio_msg_id != 0:
        models_data = googlesheetapi.get_data_for_models_by_category(category_of_models)
    else:
        markup_main_menu = ReplyKeyboardMarkup(keyboard_manager_menu, one_time_keyboard=False, resize_keyboard=True)
        await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text="Упс( Не удалось определить сообщение для рассылки, попробуйте ещё раз", reply_markup=markup_main_menu, parse_mode='HTML')       
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton('Готова', callback_data='accept_jo'), InlineKeyboardButton('Не могу', callback_data='reject_jo')]]
    markup_jo_model = InlineKeyboardMarkup(keyboard)
    context.user_data[f"models_data_{cast(Chat, update.effective_chat).id}"] = models_data
    context.user_data["from_chat_id_jo"] = cast(Chat, update.effective_chat).id
    if not models_data.empty:
        for id_model in models_data['id tg'].tolist():
            try:
                await context.bot.copy_message(chat_id=int(id_model), from_chat_id=cast(Chat, update.effective_chat).id, message_id=audio_msg_id, protect_content=True)
                await context.bot.send_message(chat_id=int(id_model), text=render_template("aletr_new_jo.j2"), reply_markup=markup_jo_model, parse_mode='HTML', protect_content=True)
            except Forbidden:
                data_manager_of_model = models_data.loc[(models_data['id tg'] == int(id_model))]
                await context.bot.send_message(chat_id=int(data_manager_of_model['id_manager_tg'].values[0]), text=f"‼️<b>Модель {data_manager_of_model['Телефон'].values[0]}</b> заблокировала бота!\nРазобраться!", parse_mode='HTML')
                continue
            except BadRequest:
                data_manager_of_model = models_data.loc[(models_data['id tg'] == int(id_model))]
                await context.bot.send_message(chat_id=int(data_manager_of_model['id_manager_tg'].values[0]), text=f"‼️<b>Неверный телеграмм ID для модели: {data_manager_of_model['Телефон'].values[0]}</b>\nРазобраться!", parse_mode='HTML')
                continue
            
    # return ConversationHandler.END
    
async def accept_jo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    managers_id_tg = googlesheetapi.get_tg_id_managers()
    
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=render_template("mess_for_model_when_she_accept_jo.j2"))
    data_of_models = context.user_data.get(f"models_data_{cast(Chat, update.effective_chat).id}", pd.DataFrame([]))
    id_model = cast(Chat, update.effective_chat).id
    caption_text, link_potrfolio = googlesheetapi.get_link_to_portfolio_of_model(id_model_tg=id_model)
    links_potrfolio_photo = generate_links_for_sharing(googlesheetapi.get_models_photo(link_potrfolio))
    name_responsible_manager = context.user_data.get("responsible_manager", 'unknown')
    chat_id = cast(Chat, managers_id_tg.get(name_responsible_manager, {"unknown":0}).get('id tg', 0))
    try:
        await context.bot.send_message(chat_id=chat_id, text=render_template("mess_for_mng_when_model_accept_jo.j2"))
        await context.bot.copy_message(chat_id=chat_id, from_chat_id=context.user_data.get("from_chat_id_jo"), message_id=context.user_data.get("audio_msg_id"), protect_content=True)
    except BadRequest:
        await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=f"‼️<b>Неверный телеграмм ID для менеджера: {name_responsible_manager, }</b>\nРазобраться!", parse_mode='HTML')
    media_group = []
    if len(links_potrfolio_photo) <=10:
        for photo in links_potrfolio_photo:
            media_group.append(InputMediaPhoto(media=photo))
        await context.bot.send_message(chat_id=cast(Chat, managers_id_tg[name_responsible_manager]), text=caption_text)
        await context.bot.send_media_group(chat_id=cast(Chat, managers_id_tg[name_responsible_manager]), media=media_group, protect_content=False)
        return ConversationHandler.END
    else:
        list_of_lists_photos = chunk(links_potrfolio_photo, 10)
        await context.bot.send_message(chat_id=cast(Chat, managers_id_tg[name_responsible_manager]), text=caption_text)
        for links_photo in list_of_lists_photos:
            media_group = []
            for photo in links_photo:
                media_group.append(InputMediaPhoto(media=photo))
            await context.bot.send_media_group(chat_id=cast(Chat, managers_id_tg[name_responsible_manager]), media=media_group, protect_content=False)