## Деплой бота на сервере

Протестировано на Debian 10.

Обновляем систему

```bash
sudo apt update && sudo apt upgrade
```

Устанавливаем Python 3.11 сборкой из исходников и sqlite3:

```bash
cd
sudo apt install -y sqlite3 pkg-config
wget https://www.python.org/ftp/python/3.11.1/Python-3.11.1.tgz
tar -xzvf Python-3.11.1.tgz
cd Python-3.11.1
apt-get install build-essential
./configure --enable-optimizations --prefix=/home/www/.python3.11
sudo make altinstall
```

Устанавливаем Poetry:

```basj
curl -sSL https://install.python-poetry.org | python3 -
```

Клонируем репозиторий в `~/code/supertop_bot`:

```bash
mkdir -p ~/code/
cd ~/code
git clone https://github.com/MaxTaras94/SuperTopAgencyBot.git
cd SuperTopAgencyBot
```

Создаём переменные окружения:

```
cp supertop_bot/.env.example supertop_bot/.env
vim supertop_bot/.env
```

`TELEGRAM_BOT_TOKEN` — токен бота, полученный в BotFather


Устанавливаем зависимости Poetry и запускаем бота вручную:

```bash
poetry install
poetry run python -m supertop_bot
```

Можно проверить работу бота. Для остановки, жмём `CTRL`+`C`.

Получим текущий адрес до Pytnon-интерпретатора в poetry виртуальном окружении Poetry:

```bash
poetry shell
which python
```

Скопируем путь до интерпретатора Python в виртуальном окружении.

Настроим systemd-юнит для автоматического запуска бота, подставив скопированный путь в ExecStart, а также убедившись,
что директория до проекта (в данном случае `/home/www/code/supertop_bot`) у вас такая же:

```
sudo tee /etc/systemd/system/supertop.service << END
[Unit]
Description=SuperTopAgency Telegram bot
After=network.target

[Service]
User=www
Group=www-data
WorkingDirectory=/home/www/code/supertop-bot
Restart=on-failure
RestartSec=2s
ExecStart=/home/www/.cache/pypoetry/virtualenvs/supertop-bot-dRxws4wE-py3.11/bin/python -m supertop_bot

[Install]
WantedBy=multi-user.target
END

sudo systemctl daemon-reload
sudo systemctl enable supertopbot.service
sudo systemctl start supertopbot.service
```
