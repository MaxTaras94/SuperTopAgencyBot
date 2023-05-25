import random

from supertop_bot.handlers.response import send_response
from supertop_bot.services.googlesheetapi import googlesheetapi
from supertop_bot.services.useful_functions import generate_links_for_sharing
from supertop_bot.templates import render_template
from telegram import Chat, Update
from telegram.ext import ContextTypes, ConversationHandler

from typing import cast


async def order_a_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Функция отправляет заказ на модель связанному с ней менеджеру'''
    query = update.callback_query.data
    id_model = int(query.split("_")[-1])
    id_manager_of_model = googlesheetapi.get_id_manager_of_model(id_model)
    client_phone = googlesheetapi.get_number_phone_of_client(cast(Chat, update.effective_chat).id)
    caption_text, link_portfolio = googlesheetapi.get_link_to_portfolio_of_model(id_model=id_model)
    links_potrfolio_photo = generate_links_for_sharing(googlesheetapi.get_models_photo(link_portfolio))
    link_photo = random.choice(links_potrfolio_photo)
    await context.bot.delete_message(cast(Chat, update.effective_chat).id, update.callback_query.message.message_id)
    await send_response(update, context, response=render_template("success_order.j2"), protect_content=True)
    await context.bot.send_message(chat_id=cast(Chat, id_manager_of_model), text=render_template("new_order.j2", {"client_phone":client_phone, "id_model": id_model}))
    await context.bot.send_message(chat_id=cast(Chat, id_manager_of_model), text=caption_text)
    await context.bot.send_photo(chat_id=cast(Chat, id_manager_of_model), photo=link_photo)