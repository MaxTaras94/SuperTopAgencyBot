# Telegram-бот для книжного клуба [Ботаним!](https://botanim.to.digital)

[![alt text](botanim-logo.svg)](https://botanim.to.digital)

## Команды бота:

- `/start` — приветственное сообщение
- `/help` — справка
- `/allbooks` — все книги, которые есть в нашем списке
- `/already` — прочитанные книги
- `/now` — книга, которую сейчас читаем
- `/vote` — проголосовать за следующую книгу
- `/voteresults` — текущие результаты текущего голосования

Голосование доступно только для участников клуба, остальные команды — для всех.

## Запуск

Скопируйте `.env.example` в `.env` и отредактируйте `.env` файл, заполнив в нём все переменные окружения:

```bash
cp botanim_bot/.env.example botanim_bot/.env
```

Для управления зависимостями используется [poetry](https://python-poetry.org/),
требуется Python 3.11.

Установка зависимостей и запуск бота:

```bash
poetry install
poetry run python -m botanim_bot
```

## Ideas

- Сделать возможность напоминаний тем, кто еще не проголосовал о том, что голосование заканчивается через N часов
- Добавить отзывы
- Возможность поиска книг — возможно с автодополнением
- Возможность предлагать книги для добавления

## Деплой

[Описание того, как можно развернуть бота на сервере](DEPLOY.md)