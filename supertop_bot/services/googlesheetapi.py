# -*- coding: utf-8 -*-
"""
Created on Fri Oct 28 08:30:05 2022

@author: taras
"""

from supertop_bot import config
from supertop_bot.services.useful_functions import get_id_from_link
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from gspread.exceptions import APIError
import pandas as pd
import sqlite3
import re
from typing import Dict, List, Tuple

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import time
import logging

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']


logger = logging.getLogger(__name__)



class GoogleSheetsAPI:
    '''
    Класс для работы с Google инструментами, с локальной SQLite БД для кэша и синхронизацией по TTL.
    Использует lazy loading для минимизации API-вызовов и retry для обработки квот.
    '''
    # Константы для TTL кэша (в секундах)
    TTL_MANAGERS = 2100
    TTL_CLIENTS = 2100 
    TTL_MODELS = 2100

    def __init__(self, db_path='main_db.db'):
        self.db_path = db_path
        self._db_conn = None  # Lazy DB connection
        self._credentials = None  # Lazy credentials
        self._connection_to_google_sheet = None  # Lazy gspread client
        self._google_drive = None  # Lazy drive service
        self._manager_sheet = None  # Lazy sheets
        self._models_msk = None
        self._init_db()  # Инициализация DB (локальная, без API)

    def _init_db(self):
        self.db_conn  # Trigger lazy DB connect
        self._create_tables()
        self._init_metadata()

    @property
    def db_conn(self):
        if self._db_conn is None:
            self._db_conn = sqlite3.connect(self.db_path, check_same_thread=False)  # Allow multi-thread if needed
            self._db_cursor = self._db_conn.cursor()
        return self._db_conn

    @property
    def db_cursor(self):
        self.db_conn  # Ensure connected
        return self._db_cursor

    @property
    def credentials(self):
        if self._credentials is None:
            self._credentials = service_account.Credentials.from_service_account_file(
                config.SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
        return self._credentials

    @property
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIError),
        before_sleep=lambda rs: logger.warning(f"Retry {rs.attempt_number} for gspread auth after {rs.outcome.exception()}"),
    )
    def connection_to_google_sheet(self):
        if self._connection_to_google_sheet is None:
            try:
                self._connection_to_google_sheet = gspread.authorize(self.credentials)
            except APIError as e:
                if e.response and e.response.status_code == 429:
                    raise  # Retry
                else:
                    logger.error(f"gspread auth error: {str(e)}")
                    raise
        return self._connection_to_google_sheet

    @property
    def google_drive(self):
        if self._google_drive is None:
            self._google_drive = build('drive', 'v3', credentials=self.credentials)
        return self._google_drive

    @property
    def manager_sheet(self):
        if self._manager_sheet is None:
            self._manager_sheet = self._open_sheet_with_retry(config.MANAGERS_LINK)
        return self._manager_sheet

    @property
    def models_msk(self):
        if self._models_msk is None:
            self._models_msk = self._open_sheet_with_retry(config.MODELS_MSK_LINK)
        return self._models_msk

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIError),
        before_sleep=lambda rs: logger.warning(f"Retry {rs.attempt_number} for open_by_url after {rs.outcome.exception()}"),
    )
    def _open_sheet_with_retry(self, url):
        try:
            return self.connection_to_google_sheet.open_by_url(url)
        except APIError as e:
            if e.response and e.response.status_code == 429:
                raise  # Retry
            else:
                logger.error(f"Error opening sheet {url}: {str(e)}")
                raise

    def _create_tables(self):
        """Создаёт таблицы в SQLite для хранения данных."""
        # Таблица для менеджеров
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS managers (
                id INTEGER PRIMARY KEY,
                phone TEXT,
                name TEXT,
                id_tg INTEGER,
                username TEXT,
                app_api_id TEXT,
                api_hash TEXT
            )
        ''')

        # Таблица для моделей
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY,
                category TEXT,
                id_model INTEGER,
                id_tg INTEGER,
                phone INTEGER,
                name TEXT,
                age INTEGER,
                height INTEGER,
                breast_size INTEGER,
                own_breasts FLOAT,
                tattoo BOOLEAN,
                description_header TEXT,
                portfolio TEXT,
                working BOOLEAN
            )
        ''')

        # Таблица для клиентов (объединённая из таблиц менеджеров)
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY,
                phone TEXT,
                name TEXT,
                id_manager_tg INTEGER,
                id_tg INTEGER,
                username TEXT,
                geo TEXT
            )
        ''')

        # Таблица для метаданных (timestamps синхронизации)
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value REAL
            )
        ''')

        self.db_conn.commit()

    def _init_metadata(self):
        """Инициализирует метаданные для timestamps, если их нет."""
        keys = ['managers_timestamp', 'models_timestamp', 'clients_timestamp']
        for key in keys:
            self.db_cursor.execute("INSERT OR IGNORE INTO metadata (key, value) VALUES (?, 0)", (key,))
        self.db_conn.commit()

    def _get_timestamp(self, key: str) -> float:
        """Получает timestamp из метаданных."""
        self.db_cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
        result = self.db_cursor.fetchone()
        return result[0] if result else 0

    def _update_timestamp(self, key: str, timestamp: float):
        """Обновляет timestamp в метаданных."""
        self.db_cursor.execute("UPDATE metadata SET value = ? WHERE key = ?", (timestamp, key))
        self.db_conn.commit()

    def _is_cache_valid(self, key: str, ttl: int) -> bool:
        """Проверяет свежесть кэша по timestamp в БД."""
        timestamp = self._get_timestamp(key)
        return time.time() - timestamp < ttl

    def _sync_managers(self):
        """Синхронизирует данные менеджеров из Google Sheets в БД."""
        worksheet = self.manager_sheet.worksheet("M")  # Lazy load
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        # Очистка таблицы и вставка новых данных
        self.db_cursor.execute("DELETE FROM managers")
        df.to_sql('managers', self.db_conn, if_exists='append', index=False)
        
        self._update_timestamp('managers_timestamp', time.time())
        logger.info("Managers data synced to DB")

    def _sync_models(self):
        """Синхронизирует данные моделей из Google Sheets в БД."""
        worksheet = self.models_msk.worksheet("МОД")  # Lazy load
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        # Очистка таблицы и вставка новых данных
        self.db_cursor.execute("DELETE FROM models")
        df.to_sql('models', self.db_conn, if_exists='append', index=False)
        
        self._update_timestamp('models_timestamp', time.time())
        logger.info("Models data synced to DB")

    def _sync_clients(self):
        """Синхронизирует данные клиентов из таблиц менеджеров в БД."""
        if not self._is_cache_valid('managers_timestamp', self.TTL_MANAGERS):
            self._sync_managers()  # Убедимся, что менеджеры свежие
        
        managers_df = self._get_managers_df()  # Из локальной БД
        all_clients = pd.DataFrame()
        
        for _, manager in managers_df.iterrows():
            tg_id_manager = manager['id_tg']
            if tg_id_manager not in [188902033]:
                clients_for_mng = self._get_client_table_for_manager(tg_id_manager)
                if not clients_for_mng.empty:
                    clients_for_mng['id_manager_tg'] = tg_id_manager
                    all_clients = pd.concat([all_clients, clients_for_mng], ignore_index=True)
        
        # Очистка таблицы и вставка новых данных
        self.db_cursor.execute("DELETE FROM clients")
        all_clients.to_sql('clients', self.db_conn, if_exists='append', index=False)
        
        self._update_timestamp('clients_timestamp', time.time())
        logger.info("Clients data synced to DB")

    def _get_managers_df(self) -> pd.DataFrame:
        """Возвращает DataFrame менеджеров из БД, синхронизируя если нужно."""
        if not self._is_cache_valid('managers_timestamp', self.TTL_MANAGERS):
            self._sync_managers()
        return pd.read_sql_query("SELECT * FROM managers", self.db_conn)

    def _get_models_df(self) -> pd.DataFrame:
        """Возвращает DataFrame моделей из БД, синхронизируя если нужно."""
        if not self._is_cache_valid('models_timestamp', self.TTL_MODELS):
            self._sync_models()
        return pd.read_sql_query("SELECT * FROM models", self.db_conn)

    def _get_clients_df(self) -> pd.DataFrame:
        """Возвращает DataFrame клиентов из БД, синхронизируя если нужно."""
        if not self._is_cache_valid('clients_timestamp', self.TTL_CLIENTS):
            self._sync_clients()
        return pd.read_sql_query("SELECT * FROM clients", self.db_conn)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIError),
        before_sleep=lambda rs: logger.warning(f"Retry {rs.attempt_number} for client table load after {rs.outcome.exception()}"),
    )
    def _get_client_table_for_manager(self, tg_id_manager: int) -> pd.DataFrame:
        """Загружает таблицу клиентов для менеджера напрямую из Google (поскольку индивидуальные, кэш в БД для clients общий)."""
        table_url = config.CLIENTS_TABLES.get(str(tg_id_manager), "")
        if not table_url:
            raise ValueError(f"No table URL for manager {tg_id_manager}")
        
        try:
            worksheet = self.connection_to_google_sheet.open_by_url(table_url)
            sheet = worksheet.worksheet("KL")
            df = pd.DataFrame(sheet.get_all_records())
        
            if 'id' in df.columns:
                df = df.drop(columns=['id'])
            
            return df
        except APIError as e:
            if e.response and e.response.status_code == 429:
                raise  # Retry
            else:
                logger.error(f"Error loading client table for {tg_id_manager}: {str(e)}")
                raise

    def get_models_photo(self, link: str) -> List[Tuple[str]]:
        '''Функция на вход получает id папки с портфолио модели и возвращает список id файлов, которые содержатся в этой папке'''
        id_folder_from_link = get_id_from_link(link)  # Предполагаем функция get_id_from_link определена
        results = self.google_drive.files().list(pageSize=50,
                               fields="nextPageToken, files(id, name, mimeType)", q=f"'{id_folder_from_link}' in parents").execute()  # Lazy drive
        return [(item['mimeType'], item['id'].strip()) for item in results.get('files', [])]

    def get_tg_id_managers(self):
        df = self._get_managers_df()
        return df.set_index('name').T.to_dict(), df['id_tg'].to_list()

    def get_clinets_table_for_manager_id(self, tg_id_manager: int):
        # Теперь из БД, фильтруя по manager
        df = self._get_clients_df()
        return df[df['id_manager_tg'] == tg_id_manager]

    def get_link_to_portfolio_of_model(self, id_model: str=None, phone_number: int=None, id_model_tg: int = None) -> tuple:
        df = self._get_models_df()
        if id_model is not None:
            if not (len(id_model) > 1 and id_model[0].isalpha() and id_model[1:].isdigit()):
                raise ValueError("Invalid id_model format. Expected format like 'X123'")
            
            prefix = id_model[0].upper() 
            numeric_id = int(id_model[1:])
            
            data = df.loc[(df['category'] == prefix) & (df['id_model'] == numeric_id)]
        elif phone_number is not None:
            data = df.loc[(df['phone'] == int(phone_number))]
        elif id_model_tg is not None:
            data = df.loc[(df['id_tg'] == int(id_model_tg))]
        if len(data) == 0:
            raise ValueError("No data found for the given parameters")
        return data.description_header.iloc[0], data.portfolio.iloc[0]

    def get_id_manager_of_model(self, id_model: int) -> int:
        df = self._get_models_df()
        id_manager_of_model = df.loc[(df['id_model'] == int(id_model))]['id_manager_tg'].tolist()[0]
        return id_manager_of_model

    def get_number_phone_of_client(self, id_tg: int) -> int:
        df = self._get_clients_df()
        number_phone_of_client = df.loc[(df['id_tg'] == int(id_tg))]['phone'].tolist()[0]
        return number_phone_of_client

    def get_id_models_for_mailing(self) -> list:
        df = self._get_models_df()
        return df.tail(2)

    def get_id_clients_for_mailing(self) -> pd.DataFrame:
        df = self._get_clients_df()
        return df[["id_tg", "id_manager_tg", "phone"]]

    def get_data_for_models_by_category(self, category: str) -> pd.DataFrame:
        df = self._get_models_df()
        if category == "Все модели":
            return df
        else:
            data = df.loc[(df['category'] == category)]
            return data

    def check_access(self, id_tg: int) -> dict:
        '''Функция проверяет, добавлен ли пользователь c таким id_tg в таблицу или нет.'''
        checking = {'access': False, 'dataUser':{'name':None, 'phone':None, 'role':None}}
        
        # Проверка в managers
        managers_df = self._get_managers_df()
        data = managers_df.loc[(managers_df['id_tg'] == id_tg)]
        if not data.empty:
            checking['access'] = True
            checking['dataUser']['role'] = "Менеджеры"
            checking['dataUser']['name'], checking['dataUser']['phone'] = data.iloc[0]['name'], data.iloc[0]['phone']
            return checking
        
        # Проверка в clients
        clients_df = self._get_clients_df()
        data = clients_df.loc[(clients_df['id_tg'] == id_tg)]
        if not data.empty:
            checking['access'] = True
            checking['dataUser']['role'] = "Клиенты"
            checking['dataUser']['name'], checking['dataUser']['phone'] = data.iloc[0]['name'], data.iloc[0]['phone']
            return checking
        
        return checking

    def get_id_clients_for_manager(self, manager_id: int, geo: str = None) -> pd.DataFrame:
        df = self._get_clients_df()
        geo_code = geo.split(' ')[0] if geo else "MSK"
        return df.loc[(df['id_manager_tg'] == manager_id) & (df['geo'] == geo_code)]


    def check_user_by_phone_number(self, phone_number: int, id_tg: int) -> dict:
        '''Функция проверяет, добавлен ли пользователь c таким phone_number в таблицу или нет.'''
        checking = {'access': False, 'dataUser':{'name':None, 'phone':None, 'role':None}}
        
        # Проверка в managers и clients через БД
        managers_df = self._get_managers_df()
        data = managers_df.loc[(managers_df['phone'].astype(str).str.contains(str(phone_number)))]
        if not data.empty and data['id_tg'].values[0] == "":
            checking['access'] = True
            checking['dataUser']['role'] = "Менеджеры"
            checking['dataUser']['name'], checking['dataUser']['phone'] = data.iloc[0]['name'], data.iloc[0]['phone']
            # Обновление в Google (поскольку БД локальная, обновляем Google и ресинхронизируем)
            self._update_google_sheet(self.manager_sheet.worksheet('M'), data.index[0] + 2, {'id_tg': id_tg})  # +2 если headers в row 1
            self._sync_managers()  # Ресинхронизация
            return checking
        
        clients_df = self._get_clients_df()
        data = clients_df.loc[(clients_df['phone'].astype(str).str.contains(str(phone_number)))]
        if not data.empty and data['id_tg'].values[0] == "":
            checking['access'] = True
            checking['dataUser']['role'] = "Клиенты"
            checking['dataUser']['name'], checking['dataUser']['phone'] = data.iloc[0]['name'], data.iloc[0]['phone']
            # Аналогично обновить Google и ресинх (для clients — определите sheet по manager)
            return checking
        
        return checking

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIError),
        before_sleep=lambda rs: logger.warning(f"Retry {rs.attempt_number} for update cell after {rs.outcome.exception()}"),
    )
    def _update_google_sheet(self, worksheet, row_num: int, updates: dict):
        """Вспомогательный метод для обновления Google Sheet (для случаев, когда нужно обновить источник)."""
        headers = [h.lower().replace(' ', '_') for h in worksheet.row_values(1)]
        for key, value in updates.items():
            col_idx = headers.index(key) + 1 if key in headers else None
            if col_idx is None:
                raise ValueError(f"Column {key} not found in sheet")
            try:
                if isinstance(value, list):
                    values_str = [str(v) for v in value]
                    value = ", ".join(values_str)
                worksheet.update_cell(row_num, col_idx, value)
            except APIError as e:
                if e.response and e.response.status_code == 429:
                    raise  # Retry
                else:
                    logger.error(f"Error updating cell {row_num},{col_idx}: {str(e)} | value_={value}")
                    
                    raise

    def add_row_to_sheet(self, worksheet, sheet_name: str, data: dict) -> int:
        """Добавляет строку в Google Sheet и ресинхронизирует БД."""
        headers = worksheet.row_values(1)
        row_values = [data.get(header.lower().replace(' ', '_'), '') for header in headers]
        try:
            updated_range = worksheet.append_row(row_values)['updates']['updatedRange']
            row_num_str = updated_range.split(':')[-1]
            row_num = int(re.findall(r'\d+', row_num_str)[0])
            logger.info(f"Added row {row_num} to {sheet_name}")
            
            # Ресинх после добавления
            if sheet_name == 'M':
                self._sync_managers()
            elif sheet_name == 'МОД':
                self._sync_models()
            
            return row_num
        except APIError as e:
            logger.error(f"Error adding row to {sheet_name}: {str(e)}")
            raise

    def get_sheet_data(self, worksheet, sheet_name: str) -> list:
        """Возвращает данные из БД или напрямую из Google, если таблицы нет в БД."""
        if sheet_name == 'M':
            return self._get_managers_df().to_dict('records')
        elif sheet_name == 'МОД':
            return self._get_models_df().to_dict('records')
        # Для других - напрямую с retry
        return self._get_all_records_with_retry(worksheet)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIError),
    )
    def _get_all_records_with_retry(self, worksheet):
        try:
            return worksheet.get_all_records()
        except APIError as e:
            if e.response and e.response.status_code == 429:
                raise
            else:
                logger.error(f"Error getting records: {str(e)}")
                raise

    def update_row_in_sheet(self, worksheet, row_num: int, updates: dict) -> None:
        """Обновляет в Google и ресинхронизирует БД."""
        self._update_google_sheet(worksheet, row_num, updates)
        
        # Ресинх после обновления
        if worksheet.title == 'M':
            self._sync_managers()
        elif worksheet.title == 'МОД':
            self._sync_models()
        # Для clients - сложнее, добавьте логику если нужно

    def get_manager_data(self, tg_id: int) -> dict:
        """Получает данные менеджера из БД."""
        df = self._get_managers_df()
        manager_row = df[df['id_tg'] == tg_id]
        if manager_row.empty:
            raise ValueError(f"Manager {tg_id} not found")
        row_data = manager_row.iloc[0]
        return {
            'tg_id': int(row_data['id_tg']),
            'phone': str(row_data['phone']),
            'name': str(row_data['name']),
            'api_id': int(row_data['app_api_id']) if pd.notna(row_data['app_api_id']) else None,
            'api_hash': str(row_data['api_hash']) if pd.notna(row_data['api_hash']) else None
        }

    def __del__(self):
        if self._db_conn:
            self._db_conn.close()


googlesheetapi = GoogleSheetsAPI()


if __name__ == "__main__":
    gs = GoogleSheetsAPI()