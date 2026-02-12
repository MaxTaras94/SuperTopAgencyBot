from supertop_bot.handlers.response import send_response
from supertop_bot.handlers.keyboards import keyboard_manager_menu
from supertop_bot.services.googlesheetapi import googlesheetapi
from supertop_bot.services.useful_functions import chunk, generate_links_for_sharing
from supertop_bot.templates import render_template
from telegram import Chat, Update, InputMediaPhoto, InputMediaVideo, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from typing import cast

logger = logging.getLogger(__name__)



async def choose_params_id_or_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция отправляет портфолио модели в чат пользователю"""
    query = update.callback_query.data
    context.user_data[f"query_{cast(Chat, update.effective_chat).id}"] = query
    await context.bot.delete_message(cast(Chat, update.effective_chat).id, update.callback_query.message.message_id)
    if query == "idmodel":        
        await send_response(update, context, response=render_template("input_id_model.j2"))
        return "SEND_PHOTOS_BY_ID"  
    else:
        await send_response(update, context, response=render_template("input_phone_model.j2"))
        return "SEND_PHOTOS_BY_PHONE" 
    # return "SEND_PHOTOS"
    

async def send_photos_of_models_potrfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция отправляет портфолио модели в чат пользователю по переданному id/phone модели"""
    models_data_type = context.user_data.get(f"query_{cast(Chat, update.effective_chat).id}", 0)
    markup = ReplyKeyboardMarkup(keyboard_manager_menu, one_time_keyboard=False, resize_keyboard=True)
    data_from_user = update.message.text
    if models_data_type == "idmodel":  
        try:
            caption_text, link_potrfolio = googlesheetapi.get_link_to_portfolio_of_model(id_model=data_from_user)
        except Exception as e:
            logger.error(e)
            await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=f"Модели с ID: <b>{data_from_user} </b> нет в БД - попробуйте снова)", reply_markup=markup, parse_mode='HTML')
            return ConversationHandler.END
    else:
        try:
            caption_text, link_potrfolio = googlesheetapi.get_link_to_portfolio_of_model(phone_number=data_from_user)
        except:
            await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=f"Модели с номером телефона: <b>{data_from_user} </b> нет в БД - попробуйте снова)", reply_markup=markup, parse_mode='HTML')
            return ConversationHandler.END
    if len(link_potrfolio) == 0:
        await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=f"У модели: <b>{data_from_user}</b> в БД нет ссылки на портфолио - попробуйте снова)", reply_markup=markup, parse_mode='HTML')
        return ConversationHandler.END
    links_photo_video = generate_links_for_sharing(googlesheetapi.get_models_photo(link_potrfolio))
    links_photo = [item for item in links_photo_video if 'image' in item[0]]
    links_video = [item for item in links_photo_video if 'video' in item[0]]
    media_group_photo = []
    media_group_video = []
    if len(links_photo) <=10:
        for item in links_photo:
            media_group_photo.append(InputMediaPhoto(media=item[1]))
        await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=caption_text, reply_markup =markup)
        await context.bot.send_media_group(chat_id=cast(Chat, update.effective_chat).id, media=media_group_photo, protect_content=False)
        if len(links_video) > 0:
            for item in links_video:
                await context.bot.send_video(chat_id=cast(Chat, update.effective_chat).id, video=item[1])
        return ConversationHandler.END
    else:
        list_of_lists_photos = chunk(links_photo, 10)
        await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=caption_text, reply_markup=markup)
        for links_photo in list_of_lists_photos:
            media_group_photo = []
            for item in links_photo:
                media_group_photo.append(InputMediaPhoto(media=item[1]))
            logger.info(f'media_group_photo = {media_group_photo}')
            await context.bot.send_media_group(chat_id=cast(Chat, update.effective_chat).id, media=media_group_photo, protect_content=False)
        if len(links_video) > 0:
            for item in links_video:
                await context.bot.send_document(chat_id=cast(Chat, update.effective_chat).id, document=item[1])
        return ConversationHandler.END
