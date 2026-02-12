import asyncio
import os
from datetime import datetime
from typing import cast

from supertop_bot.services.googlesheetapi import googlesheetapi
from supertop_bot.handlers.keyboards import keyboard_client_mailing_portfolio_models
from supertop_bot.services.useful_functions import generate_links_for_sharing, chunk
from supertop_bot.services.scheduled_mailing import update_mailing_status
from telegram.error import Forbidden, BadRequest
from telegram import Chat, Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

import logging
logger = logging.getLogger(__name__)

async def execute_scheduled_mailing(context: CallbackContext) -> None:
    """Выполняет запланированную рассылку портфолио моделей клиентам менеджера."""
    data = context.job.data
    task_id = data['task_id']
    manager_id = data['manager_id']
    models_ids_str = data['models_ids']
    geo = data['geo']
    models_ids = models_ids_str.split(',')
    
    await context.bot.send_message(
        chat_id=manager_id,
        text=f"🚀 Начинаю запланированную рассылку по моделям: <b>{models_ids_str}</b>",
        parse_mode='HTML'
    )
    
    clients_df = googlesheetapi.get_id_clients_for_manager(manager_id, geo) 
    
    success_id_clients = []
    for client_id in clients_df['id_tg'].tolist():
        try:
            for num, id_model in enumerate(models_ids):
                caption_text, link_portfolio = googlesheetapi.get_link_to_portfolio_of_model(id_model=id_model)
                links_photo_video = generate_links_for_sharing(googlesheetapi.get_models_photo(link_portfolio))
                links_photo = [item for item in links_photo_video if 'image' in item[0]]
                links_video = [item for item in links_photo_video if 'video' in item[0]]
                media_group_photo = []
                media_group_video = []
                if len(links_photo) <=10:
                    for item in links_photo:
                        media_group_photo.append(InputMediaPhoto(media=item[1]))
                    await context.bot.send_message(chat_id=client_id, text=f"<b>Модель №{num+1}</b>\n\n"+caption_text, parse_mode='HTML')
                    await context.bot.send_media_group(chat_id=client_id, media=media_group_photo, protect_content=False)
                    if len(links_video) > 0:
                        for item in links_video:
                            await context.bot.send_video(chat_id=client_id, video=item[1])
                else:
                    list_of_lists_photos = chunk(links_photo, 10)
                    await context.bot.send_message(chat_id=client_id, text=f"<b>Модель №{num+1}</b>\n\n"+caption_text, parse_mode='HTML')
                    for links_photo in list_of_lists_photos:
                        media_group_photo = []
                        for item in links_photo:
                            media_group_photo.append(InputMediaPhoto(media=item[1]))
                        logger.info(f'media_group_photo = {media_group_photo}')
                        await context.bot.send_media_group(chat_id=client_id, media=media_group_photo, protect_content=False)
                    if len(links_video) > 0:
                        for item in links_video:
                            await context.bot.send_document(chat_id=client_id, document=item[1])
                        
                    success_id_clients.append(client_id)
                keyboard = [
                    [InlineKeyboardButton("Запросить связь с менеджером 🗣", callback_data=f"ordermodel_{id_model}_{client_id}_{manager_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(
                    chat_id=int(client_id),
                    text=f"✅ Понравилась модель №{num+1}",
                    reply_markup=reply_markup,
                    protect_content=True
                )
                await asyncio.sleep(1) 
        
        # except Forbidden:
        #     client_data = clients_df.loc[clients_df['id_tg'] == int(client_id)]
        #     await context.bot.send_message(
        #         chat_id=manager_id,  
        #         text=f"‼️<b>Клиент {client_data['id_tg'].values[0]}</b> заблокировал бота!",
        #         parse_mode='HTML'
        #     )
        
        # except BadRequest:
        #     client_data = clients_df.loc[clients_df['id_tg'] == int(client_id)]
        #     await context.bot.send_message(
        #         chat_id=manager_id,
        #         text=f"‼️<b>Неверный телеграм ID для клиента: {client_data['id_tg'].values[0]}</b>\nПроверить!",
        #         parse_mode='HTML'
        #     )
        
        except Exception as e:
            logger.error(f"Ошибка рассылки для клиента {client_id}: {e}")
            await context.bot.send_message(
                chat_id=manager_id,
                text=f"⚠️ Ошибка в рассылке задачи {task_id} для клиента {client_id}: {str(e)}"
            )
    
    await asyncio.sleep(10)
    
    # for client_id in list(set(success_id_clients)):
        
    
    await context.bot.send_message(
        chat_id=manager_id,
        text=f"✅ Рассылка задачи {task_id} завершена. Отправлено {len(set(success_id_clients))} клиентам."
    )
    update_mailing_status(task_id, 'completed', success_id_clients=success_id_clients)
