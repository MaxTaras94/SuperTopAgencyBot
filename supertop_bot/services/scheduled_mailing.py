import datetime
from typing import List, Dict
from supertop_bot import config
from ..services.googlesheetapi import googlesheetapi
import logging
import pytz


logger = logging.getLogger(__name__)

def add_scheduled_mailing(manager_id: int, models_ids: str, scheduled_datetime: datetime.datetime, geo: str) -> str:
    """Добавляет задачу в Sheets. Возвращает task_id (номер строки)."""
    tz = pytz.timezone('Europe/Moscow')
    data = {
        'manager_id': manager_id,
        'models_ids': models_ids,
        'scheduled_datetime': scheduled_datetime.isoformat(),
        'status': 'pending',
        'geo': geo,
        'created_at': datetime.datetime.now(tz=tz).isoformat(),
        'error': ''
    }
    spreadsheet = googlesheetapi.connection_to_google_sheet.open_by_url(config.SHEET_NAME_SCHEDULED)
    worksheet  = spreadsheet.worksheet("tasks")
    row_num = googlesheetapi.add_row_to_sheet(worksheet, "tasks", data)
    logger.info(f"Added scheduled mailing {row_num} for manager {manager_id}")
    return str(row_num)

def update_mailing_status(task_id: str, status: str, success_id_clients: list = [], error: str = '') -> None:
    """Обновляет статус задачи."""
    updates = {'status': status, 'success_id_clients': success_id_clients}
    if error:
        updates['error'] = error
    spreadsheet = googlesheetapi.connection_to_google_sheet.open_by_url(config.SHEET_NAME_SCHEDULED)
    worksheet  = spreadsheet.worksheet("tasks")
    googlesheetapi.update_row_in_sheet(worksheet, int(task_id), updates)
    logger.info(f"Updated status for {task_id}: {status}")

def get_pending_mailings() -> List[Dict]:
    """Получает pending задачи (для мониторинга, опционально)."""
    spreadsheet = googlesheetapi.connection_to_google_sheet.open_by_url(config.SHEET_NAME_SCHEDULED)
    worksheet  = spreadsheet.worksheet("tasks")
    sheet_data = googlesheetapi.get_sheet_data(worksheet, "tasks")
    now = datetime.datetime.now()
    pending = [
        row for row in sheet_data 
        if row.get('status') == 'pending' and datetime.datetime.fromisoformat(row['scheduled_datetime']) <= now
    ]
    return pending