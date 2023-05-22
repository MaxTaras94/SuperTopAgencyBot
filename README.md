# Telegram-бот агентства СуперТОП

## Запуск

Скопируйте `.env.example` в `.env` и отредактируйте `.env` файл, заполнив в нём все переменные окружения:

```bash
cp supertop_bot/.env.example supertop_bot/.env
```

Для управления зависимостями используется [poetry](https://python-poetry.org/),
требуется Python 3.11.

Установка зависимостей и запуск бота:

```bash
poetry install
poetry run python -m supertop_bot
```


## Деплой

[Описание того, как можно развернуть бота на сервере](DEPLOY.md)
