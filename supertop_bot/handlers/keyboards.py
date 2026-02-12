from telegram import  KeyboardButton



keyboard_manager_menu = [[KeyboardButton(text="Клиенты"), KeyboardButton(text="Модели")]]
keyboard_manager_menu_clients = [[KeyboardButton(text="Запланировать рассылку портфолио моделей")], [KeyboardButton(text="Назад")]]
keyboard_manager_menu_models = [[KeyboardButton(text="Хочу портфолио модели"),
                                KeyboardButton(text="Разослать предложение о работе")],
                                [KeyboardButton(text="Назад")]]
keyboard_client_mailing_portfolio_models = [[KeyboardButton(text="Понравилась модель")]]