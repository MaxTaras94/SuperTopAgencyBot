FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.3 && poetry --version  

COPY pyproject.toml poetry.lock ./

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/app/main.db", "/app/telegram_bot.log"]

CMD ["python", "-m", "supertop_bot"]