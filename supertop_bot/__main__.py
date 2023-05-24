import datetime
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    Application,
    MessageHandler,
    filters)
import logging
from supertop_bot import config, handlers



logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR, filename='telegram_bot.log'
)
logger = logging.getLogger(__name__)

        
def main():
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    # Блок для автоматической регулярной рассылки
    # job_queue = application.job_queue
    # time = datetime.time(11, 00, 00, 000000)
    # job_mailing_cold_clients = job_queue.run_daily(handlers.mailing_cold_clients, time=time)
    # job_minute = job_queue.run_repeating(handlers.mailing_cold_clients, interval=600, first=10)
    
    conv_handler_start = ConversationHandler(
        entry_points=[CommandHandler("start", handlers.start), 
                      MessageHandler(filters.TEXT & filters.Regex("^Повторить аутентификацию$"), handlers.start)],
        states={'PHONE_NUMBER': [MessageHandler(filters.Regex("^(\d{8,20})$"), handlers.phone_number)]},
        fallbacks=[MessageHandler(filters.TEXT, handlers.error_message_recognition)])

    conv_get_portfolio_models = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Хочу портфолио модели$"),
                      handlers.choose_parametres_for_searching_portfolio)],
        states={'CHOOSE_PARAMS_ID_OR_PHONE': [CallbackQueryHandler(handlers.choose_params_id_or_phone, pattern="^(idmodel|phnummod)$")],
                'SEND_PHOTOS_BY_ID': [MessageHandler(filters.Regex("^(\d{1,5})$"), handlers.send_photos_of_models_potrfolio_for_id)],
                'SEND_PHOTOS_BY_PHONE': [MessageHandler(filters.Regex("^(\d{9,20})$"), handlers.send_photos_of_models_potrfolio_for_phone)]
                },
        fallbacks=[MessageHandler(filters.TEXT, handlers.error_message_recognition)],
        per_message=False)
    
    conv_cold_mailing = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Создать холодную рассылку$"),
                      handlers.create_cold_mailing)],
        states={'CHOOSE_ID_MODELS_FOR_MAILING': [MessageHandler(filters.Regex("^[1-9]*(,[0-9]*[0-9])*$"), handlers.consent_start_mailing),
                                                CallbackQueryHandler(handlers.create_cold_mailing, pattern="^(change_list_of_models)$")],
                'START_MAILING': [CallbackQueryHandler(handlers.start_mailing_cold_clients, pattern="^(start_cold_mailing)$"),
                                  CallbackQueryHandler(handlers.create_cold_mailing, pattern="^(change_list_of_models)$")]},
        fallbacks=[MessageHandler(filters.TEXT, handlers.error_message_recognition)],
        per_message=False)
    conv_jo_for_models = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Разослать предложение о работе$"), handlers.get_offer_job_for_models)],
        states={'CHOOSE_MANAGER':[MessageHandler(filters.VOICE|filters.TEXT, handlers.choose_manager_for_accepting_applications)],
                'GET_JO': [CallbackQueryHandler(handlers.checking_data_for_job, pattern="^(Dima|Vika|Olia|Artem|Ksenia)$")],
                'START_JO': [CallbackQueryHandler(handlers.start_jo_mailing, pattern="^(top60|top60omg)$")],
                'SEND_JO':[CallbackQueryHandler(handlers.send_jo, pattern="^startjo$"), CallbackQueryHandler(handlers.get_offer_job_for_models, pattern="^change_jo$")]},
        fallbacks=[MessageHandler(filters.VOICE|filters.TEXT, handlers.error_message_recognition)],
        per_message=False)
    application.add_handlers([conv_handler_start, conv_get_portfolio_models, conv_cold_mailing, conv_jo_for_models,
                              MessageHandler(filters.TEXT & filters.Regex("^(Назад|Главное меню)$"), handlers.come_back),
                              MessageHandler(filters.TEXT & filters.Regex("^Модели$"), handlers.menu_models),
                              MessageHandler(filters.TEXT & filters.Regex("^Клиенты$"), handlers.menu_clients),
                              CallbackQueryHandler(handlers.order_a_model, pattern="^ordermodel_(\d+)"),
                              CallbackQueryHandler(handlers.accept_jo, pattern="^accept_jo$")
                              ])
    application.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        logger.warning(traceback.format_exc())
