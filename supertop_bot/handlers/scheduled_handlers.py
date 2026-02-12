from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from typing import cast
from datetime import datetime, timedelta
import pytz

from ..services.scheduled_mailing import add_scheduled_mailing
from ..services.googlesheetapi import googlesheetapi
from .response import send_response
from ..templates import render_template

CHOOSE_ID_MODELS, CHOOSE_CLIENTS_GEO, CHOOSE_DATETIME, CONFIRM = range(4)
GEO_TIMEDELTA = {"geo_msk": (timedelta(hours=0), 'MSK 🇷🇺'), 
                 "geo_spb": (timedelta(hours=0), 'SPB 🇷🇺'),
                 "geo_dub": (timedelta(hours=-1), 'SPB 🇷🇺'),
                 "geo_lnd": (timedelta(hours=3), 'LND 🇬🇧'), 
                 "geo_eu": (timedelta(hours=2), 'EU 🇪🇺'), 
                 "geo_usa": (timedelta(hours=8), 'USA 🇺🇸')
}

async def create_scheduled_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Старт: ввод ID моделей."""
    await send_response(update, context, response=render_template("input_id_models_for_scheduled_mailing.j2"))
    return CHOOSE_ID_MODELS

async def consent_scheduled_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверка ID, переход к дате."""
    text_for_mailing = update.message.text
    context.user_data['scheduled_models'] = text_for_mailing
    # Проверка (адаптировано под твой метод)
    invalid_ids = []
    for id_model in text_for_mailing.split(','):
        try:
            googlesheetapi.get_link_to_portfolio_of_model(id_model=id_model)
        except:
            invalid_ids.append(id_model)
    if invalid_ids:
        await send_response(update, context, response=f"Неверные ID: {','.join(invalid_ids)}. Введите заново.")
        return CHOOSE_ID_MODELS
    
    keyboard = [
            [InlineKeyboardButton('MSK 🇷🇺', callback_data='geo_msk')],
            [InlineKeyboardButton('SPB 🇷🇺', callback_data='geo_spb')],
            [InlineKeyboardButton('DUB 🇦🇪', callback_data='geo_dub')],
            [InlineKeyboardButton('LND 🇬🇧', callback_data='geo_lnd')],
            [InlineKeyboardButton('EU 🇪🇺', callback_data='geo_eu')],
            [InlineKeyboardButton('USA 🇺🇸', callback_data='geo_usa')],
        ]
    markup = InlineKeyboardMarkup(keyboard)
    await send_response(update, context, keyboard=markup, response="Рассылку по какому ГЕО будем производить?")
    return CHOOSE_CLIENTS_GEO

async def choose_clients_geo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    "Выбор ГЕО клиентов для рассылки"
    geo = update.callback_query.data
    context.user_data["geo"] = geo
    await send_response(update, context, response=f"Введите дату и время рассылки в часовом поясе {GEO_TIMEDELTA.get(geo)[1]} в следующем формате: DD.MM.YYYY HH:MM (20.01.2026 16:00) 👇")
    return CHOOSE_DATETIME

async def parse_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Парсинг даты."""
    try:
        tz = pytz.timezone('Europe/Moscow')
        dt_str = update.message.text.strip()
        chosed_geo = context.user_data.get('geo')
        tz_chosed_geo = GEO_TIMEDELTA.get(chosed_geo)[0]
        scheduled_dt = datetime.strptime(dt_str, '%d.%m.%Y %H:%M') + tz_chosed_geo
        scheduled_dt = tz.localize(scheduled_dt)
        if scheduled_dt <= datetime.now(tz=tz):
            raise ValueError("Дата в прошлом")
        context.user_data['scheduled_dt'] = scheduled_dt
        keyboard = [
            [InlineKeyboardButton('Подтвердить', callback_data='confirm_schedule')],
            [InlineKeyboardButton('Изменить', callback_data='change')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await send_response(update, context, keyboard=markup, response=f"Рассылка на {scheduled_dt.strftime('%d.%m.%Y %H:%M')} по Москве?")
        context.user_data["geo"] = GEO_TIMEDELTA.get(chosed_geo)[1]
        return CONFIRM
    except ValueError as e:
        await send_response(update, context, response=f"Неверный формат даты: {e}")
        return CHOOSE_DATETIME

async def confirm_scheduled_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохранение и планирование job."""
    query = update.callback_query
    await query.answer()
    if query.data == 'change':
        return CHOOSE_DATETIME
    
    manager_id = cast(int, update.effective_chat.id)
    models_ids = context.user_data['scheduled_models']
    scheduled_dt = context.user_data['scheduled_dt']
    geo = context.user_data.get("geo", "MSK")
    task_id = add_scheduled_mailing(manager_id, models_ids, scheduled_dt, geo)
    context.user_data['scheduled_task_id'] = task_id
    
    # Планируем job
    job_queue = context.application.job_queue
    from ..services.telethon_mailing import execute_scheduled_mailing
    job_queue.run_once(
        callback=execute_scheduled_mailing,
        when=scheduled_dt,
        data={'task_id': task_id, 'manager_id': manager_id, 'models_ids': models_ids, 'geo': geo}
    )
    
    await query.edit_message_text(f"✅ Рассылка запланирована на {scheduled_dt.strftime('%d.%m.%Y %H:%M')}!")
    context.user_data.clear()
    return ConversationHandler.END