import datetime
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    Application,
    MessageHandler,
    filters)
import logging
from supertop_bot import config
from .handlers.scheduled_handlers import choose_clients_geo
from .handlers.conversations import conv_handler_start, conv_get_portfolio_models, conv_scheduled_mailing, conv_jo_for_models, debug_callback
from .handlers.menu_for_managers import come_back, menu_models, menu_clients
from .handlers.order_a_model import order_a_model
from .handlers.get_offer_for_models  import accept_jo


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR
)
logger = logging.getLogger(__name__)

        
def main():
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    # Блок для автоматической регулярной рассылки
    # job_queue = application.job_queue
    # time = datetime.time(11, 00, 00, 000000)
    # job_mailing_cold_clients = job_queue.run_daily(handlers.mailing_cold_clients, time=time)
    # job_minute = job_queue.run_repeating(handlers.mailing_cold_clients, interval=600, first=10)
    
    # conv_handler_start = ConversationHandler(
    #     entry_points=[CommandHandler("start", handlers.start), 
    #                   MessageHandler(filters.TEXT & filters.Regex("^Повторить аутентификацию$"), handlers.start)],
    #     states={'PHONE_NUMBER': [MessageHandler(filters.Regex("^(\d{8,20})$"), handlers.phone_number)]},
    #     fallbacks=[MessageHandler(filters.TEXT, handlers.error_message_recognition), MessageHandler(filters.TEXT & filters.Regex("^(Назад|Главное меню)$"), handlers.come_back)])

    # conv_get_portfolio_models = ConversationHandler(
    #     entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Хочу портфолио модели$"),
    #                   handlers.choose_parametres_for_searching_portfolio)],
    #     states={'CHOOSE_PARAMS_ID_OR_PHONE': [CallbackQueryHandler(handlers.choose_params_id_or_phone, pattern="^(idmodel|phnummod)$"), 
    #                                           MessageHandler(filters.TEXT & filters.Regex("^(Назад|Главное меню)$"), handlers.come_back)],
    #             'SEND_PHOTOS': [MessageHandler(filters.Regex("^(\d{1,5})$"), handlers.send_photos_of_models_potrfolio),
    #                                   MessageHandler(filters.Regex("^(\d{9,20})$"), handlers.send_photos_of_models_potrfolio),
    #                                   MessageHandler(filters.TEXT & filters.Regex("^(Назад|Главное меню)$"), handlers.come_back)]
    #             },
    #     fallbacks=[MessageHandler(filters.TEXT, handlers.error_message_recognition)],
    #     per_message=False)
    
    
    application.add_handlers([conv_handler_start, conv_get_portfolio_models, conv_scheduled_mailing, conv_jo_for_models,
                              MessageHandler(filters.TEXT & filters.Regex("^(Назад|Главное меню)$"), come_back),
                              MessageHandler(filters.TEXT & filters.Regex("^Модели$"), menu_models),
                              MessageHandler(filters.TEXT & filters.Regex("^Клиенты$"), menu_clients),
                              CallbackQueryHandler(order_a_model, pattern=r"^ordermodel_.+$"),
                              CallbackQueryHandler(accept_jo, pattern="^accept_jo$"),
                              CallbackQueryHandler(debug_callback)
                              ])
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        logger.warning(traceback.format_exc())
