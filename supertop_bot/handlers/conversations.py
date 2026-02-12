from telegram import  Update

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters)

from. error_message_recognition import error_message_recognition
from .scheduled_handlers import create_scheduled_mailing, consent_scheduled_mailing, parse_datetime, choose_clients_geo, confirm_scheduled_mailing, CHOOSE_ID_MODELS, CHOOSE_DATETIME, CHOOSE_CLIENTS_GEO, CONFIRM
from .get_offer_for_models import checking_data_for_job, send_jo, start_jo_mailing, choose_manager_for_accepting_applications, get_offer_job_for_models
from. get_data_of_model_for_searching_portfolio import choose_parametres_for_searching_portfolio
from .send_photo_by_model import choose_params_id_or_phone, send_photos_of_models_potrfolio
from .menu_for_managers import come_back
from .get_phone_number import phone_number
from .start import start

conv_handler_start = ConversationHandler(
        entry_points=[CommandHandler("start", start), 
                      MessageHandler(filters.TEXT & filters.Regex("^Повторить аутентификацию$"), start)],
        states={'PHONE_NUMBER': [MessageHandler(filters.Regex(r"^(\d{8,20})$"), phone_number)]},
        fallbacks=[CommandHandler("cancel", ConversationHandler.END)],
        per_message=False,
        per_chat=True,
        per_user=True)


async def debug_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Получен CallbackQuery: {update.callback_query.data}")
    await update.callback_query.answer()

conv_get_portfolio_models = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex(r"^Хочу портфолио модели$"),
                  choose_parametres_for_searching_portfolio)],
    states={'CHOOSE_PARAMS_ID_OR_PHONE': [CallbackQueryHandler(choose_params_id_or_phone)], #, pattern="^(idmodel|phnummod)$"
            'SEND_PHOTOS_BY_ID': [MessageHandler(filters.Regex(r"^([A-Za-z]\d{1,5})$"), send_photos_of_models_potrfolio)],
            'SEND_PHOTOS_BY_PHONE': [MessageHandler(filters.Regex(r"^(\d{9,20})$"), send_photos_of_models_potrfolio)]
            },
    fallbacks=[CommandHandler("cancel", ConversationHandler.END)],
    per_message=False,
    per_chat=True,
    per_user=True)

conv_scheduled_mailing = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Запланировать рассылку портфолио моделей$"), create_scheduled_mailing)],
        states={
            CHOOSE_ID_MODELS: [MessageHandler(filters.Regex(r"^[A-Za-z]+\d+(,[A-Za-z]+\d+)*$"), consent_scheduled_mailing)],
            CHOOSE_CLIENTS_GEO: [CallbackQueryHandler(choose_clients_geo, pattern=r"^geo_.+$")],
            CHOOSE_DATETIME: [MessageHandler(filters.TEXT, parse_datetime)],
            CONFIRM: [CallbackQueryHandler(confirm_scheduled_mailing, pattern="^(confirm_schedule|change)$")]
        },
        fallbacks=[MessageHandler(filters.TEXT & filters.Regex("^(Назад|Главное меню)$"), come_back)],
        per_message=False,
        per_chat=True,
        per_user=True
    )

conv_jo_for_models = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Разослать предложение о работе$"), get_offer_job_for_models)],
        states={'CHOOSE_MANAGER':[MessageHandler(filters.VOICE|filters.TEXT, choose_manager_for_accepting_applications)],
                'GET_JO': [CallbackQueryHandler(checking_data_for_job, pattern="^(Dima|Vika|Olia|Artem|Nadin)$"), MessageHandler(filters.TEXT & filters.Regex("^(Назад|Главное меню)$"), come_back)],
                'START_JO': [CallbackQueryHandler(start_jo_mailing, pattern="^(top60|top60omg|all_models)$"), MessageHandler(filters.TEXT & filters.Regex("^(Назад|Главное меню)$"), come_back)],
                'SEND_JO':[CallbackQueryHandler(send_jo, pattern="^startjo$"), CallbackQueryHandler(get_offer_job_for_models, pattern="^change_jo$"), MessageHandler(filters.TEXT & filters.Regex("^(Назад|Главное меню)$"), come_back)]},
        fallbacks=[MessageHandler(filters.VOICE|filters.TEXT, error_message_recognition)],
        per_message=False,
        per_chat=True,
        per_user=True)