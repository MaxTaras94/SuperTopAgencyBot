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
import pandas as pd
from typing import Dict, List


SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']



class GoogleSheetsAPI:
    '''
    Класс для работы с Гугл инструментами. Для коннекта с Гугл таблицами юзается gspread, для Гугл Диска - googleapiclient
    '''
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(config.SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        connection_to_google_sheet = gspread.authorize(credentials)
        self.__conn_to_spreadSheet = connection_to_google_sheet.open_by_url(config.GS_TABLE_LINK)
        self.__googleDrive = build('drive', 'v3', credentials=credentials)
        
    def get_models_photo(self, link: str) -> List[str]:
        '''Функция на вход получает id папки с портфолио модели и возвращает список id файлов, которые содержатся в этой папке'''
        id_folder_from_link = get_id_from_link(link)
        results = self.__googleDrive.files().list(pageSize=50,
                               fields="nextPageToken, files(id, name, mimeType)", q=f"'{id_folder_from_link}' in parents").execute()
        return [item['id'].strip() for item in results['files']]
    
            
    def get_link_to_portfolio_of_model(self, id_model: int=None, phone_number: int=None) -> tuple:
        '''Функция на вход получает id модели и возращает ссылку на её портфолио с описанием модели'''
        worksheet = self.__conn_to_spreadSheet.worksheet("Модели")
        df = pd.DataFrame(worksheet.get_all_records())
        print(f"Я в ф-ции get_link_to_portfolio_of_model. Передан phone_number={phone_number}")
        if id_model is not None:
            data = df.loc[(df['id'] == int(id_model))]
        elif phone_number is not None:
            data = df.loc[(df['Телефон'] == int(phone_number))]
        return data['Описание для шапки'].values[0], data['Портфолио'].values[0]
    
    def get_id_manager_of_model(self, id_model: int) -> int:
        worksheet = self.__conn_to_spreadSheet.worksheet("Модели")
        df = pd.DataFrame(worksheet.get_all_records())
        id_manager_of_model = df.loc[(df['id'] == int(id_model))]['id_manager_tg'].tolist()[0]
        return id_manager_of_model
        
    def get_number_phone_of_client(self, id_tg: int) -> int:
        worksheet = self.__conn_to_spreadSheet.worksheet("Клиенты")
        df = pd.DataFrame(worksheet.get_all_records())
        number_phone_of_client = df.loc[(df['id tg'] == int(id_tg))]['Телефон'].tolist()[0]
        return number_phone_of_client
        
        
    def get_id_models_for_mailing(self) -> list:
        '''Функция возвращает данные по 2-м последним добавленным моделям из таблицы для рассылки'''
        worksheet = self.__conn_to_spreadSheet.worksheet("Модели")
        df = pd.DataFrame(worksheet.get_all_records())
        df_last_two_rows = df.tail(2)
        return df_last_two_rows.id.tolist()
    
    def get_id_clients_for_mailing(self) -> list:
        '''Функция возвращает id всех клиентов для рассылки'''
        worksheet = self.__conn_to_spreadSheet.worksheet("Клиенты")
        df = pd.DataFrame(worksheet.get_all_records())
        return df["id tg"].tolist() 
            
        
    def check_access(self, id_tg: int) -> dict:
        '''Функция проверяет, добавлен ли пользователь c таким id_tg в таблицу или нет. Возвращает картеж, где 1-ый элемент - True/False,
        а 2-й - имя пользователя, если он уже есть в таблице'''
        worksheets = self.__conn_to_spreadSheet.worksheets()
        checking = {'access': False, 'dataUser':{'name':None, 'phone':None, 'role':None}}
        for sheet in worksheets:
            if not checking['access']:
                data_from_sheet = self.__conn_to_spreadSheet.worksheet(sheet.title)
                df = pd.DataFrame(data_from_sheet.get_all_records())
                try:
                    data = df.loc[(df['id tg'] == id_tg)]
                    if len(data) == 0:
                        continue
                    else:
                        checking['access'] = True
                        checking['dataUser']['role'] = sheet.title
                        checking['dataUser']['name'], checking['dataUser']['phone'] = data.values[0][2], data.values[0][1]
                except KeyError:
                    continue
            else:
                return checking
        return checking
        
    def check_user_by_phone_number(self, phone_number: int, id_tg: int) -> dict:
        '''Функция проверяет, добавлен ли пользователь c таким phone_number в таблицу или нет. Возращает картеж, где 1-ый элемент - True/False,
        а 2-й - имя пользователя, если он уже есть в таблице'''
        worksheets = self.__conn_to_spreadSheet.worksheets()
        checking = {'access': False, 'dataUser':{'name':None, 'phone':None, 'role':None}}
        for sheet in worksheets:
            if not checking['access']:
                data_from_sheet = self.__conn_to_spreadSheet.worksheet(sheet.title)
                df = pd.DataFrame(data_from_sheet.get_all_records())
                try:
                    data = df.loc[(df['Телефон'].astype(str).str.contains(str(phone_number)))]
                    print(f'data = {data}')
                    if len(data) == 0:
                        continue
                    else:
                        checking['access'] = True
                        checking['dataUser']['role'] = sheet.title
                        checking['dataUser']['name'], checking['dataUser']['phone'] = data.values[0][2], data.values[0][1]
                        self.__conn_to_spreadSheet.worksheet(sheet.title).update_cell(data.id+1, len(data.columns), id_tg)
                except KeyError:
                    continue
            else:
                return checking
        return checking
googlesheetapi = GoogleSheetsAPI()

if __name__ == "__main__":
    gs = GoogleSheetsAPI()
    gs.check_access(4419441982)
