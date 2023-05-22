from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters)

from . import start, phone_number, cancel, choose_parametres_for_searching_portfolio, choose_params_id_or_phone, send_photos_of_models_potrfolio_for_id, send_photos_of_models_potrfolio_for_phone

conv_handler_start = ConversationHandler(
        entry_points=[CommandHandler("start", start), 
                      MessageHandler(filters.TEXT & filters.Regex("^Повторить аутентификацию$"), start)],
        states={'PHONE_NUMBER': [MessageHandler(filters.Regex("^(\d{8,20})$"), phone_number)]},
        fallbacks=[CommandHandler("cancel", cancel)])

conv_get_portfolio_models = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Хочу портфолио модели$"),
                  choose_parametres_for_searching_portfolio)],
    states={'CHOOSE_PARAMS_ID_OR_PHONE': [CallbackQueryHandler(choose_params_id_or_phone, pattern="^(idmodel|phnummod)$")],
            'SEND_PHOTOS_BY_ID': [MessageHandler(filters.Regex("^(\d{1,5})$"), send_photos_of_models_potrfolio_for_id)],
            'SEND_PHOTOS_BY_PHONE': [MessageHandler(filters.Regex("^(\d{9,20})$"), send_photos_of_models_potrfolio_for_phone)]
            },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False)