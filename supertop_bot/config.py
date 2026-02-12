import os
from pathlib import Path
import json
from dotenv import load_dotenv

load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MODELS_MSK_LINK = os.getenv("MODELS_MSK_LINK", "")
MANAGERS_LINK = os.getenv("MANAGERS_LINK", "")
SHEET_NAME_SCHEDULED = os.getenv("SHEET_NAME_SCHEDULED", "")
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "")
CLIENTS_TABLES_ = os.getenv("CLIENTS_TABLES", "{}")
CLIENTS_TABLES = json.loads(CLIENTS_TABLES_)