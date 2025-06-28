import io
import os
import tempfile
import tkinter as tk
import zipfile
from tkinter import filedialog
from typing import Tuple, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


class WordToHtmlConverter:
    """
    Конвертер Word в HTML+ZIP
    Сохраняет точное оригинальное имя для всех файлов
    """

    def __init__(self, service_account_file: str = 'service_account.json'):
        self.SERVICE_ACCOUNT_FILE = service_account_file
        self.creds = None
        self.drive_service = None

    def select_word_file(self) -> str:
        """Выбор Word файла через проводник"""
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Выберите Word документ",
            filetypes=[("Word Documents", "*.docx")]
        )
        if not file_path:
            raise ValueError("Файл не выбран")
        return file_path

    def get_downloads_path(self) -> str:
        """Путь к папке Загрузки"""
        if os.name == 'nt':
            return os.path.join(os.environ['USERPROFILE'], 'Downloads')
        return os.path.join(os.path.expanduser('~'), 'Downloads')

    def convert(self) -> Tuple[bool, Optional[str]]:
        """
        Конвертация Word в ZIP
        Возвращает:
            - (True, path_to_zip) при успехе
            - (False, None) при ошибке
        """
        try:
            word_path = self.select_word_file()
            original_name = os.path.splitext(os.path.basename(word_path))[0]
            output_zip = os.path.join(self.get_downloads_path(), f"{original_name}.zip")

            if self._convert_to_zip(word_path, output_zip, original_name):
                return True, output_zip
            return False, None

        except Exception as e:
            print(f"Ошибка: {e}")
            return False, None

    def _convert_to_zip(self, word_path: str, output_zip: str, original_name: str) -> bool:
        """Основная логика конвертации"""
        if not self._authenticate():
            print("Ошибка аутентификации Google Drive")
            return False

        try:
            # 1. Загружаем Word файл на Google Drive с оригинальным именем
            file_metadata = {
                'name': original_name,  # Точное оригинальное имя
                'mimeType': 'application/vnd.google-apps.document'
            }

            media = MediaFileUpload(
                word_path,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = file['id']

            # 2. Скачиваем как временный ZIP
            temp_zip = os.path.join(self.get_downloads_path(), f"temp_{os.path.basename(output_zip)}")
            with io.FileIO(temp_zip, 'wb') as fh:
                downloader = MediaIoBaseDownload(
                    fh,
                    self.drive_service.files().export_media(
                        fileId=file_id,
                        mimeType='application/zip'
                    )
                )
                while not downloader.next_chunk()[1]:
                    pass

            # 3. Удаляем временный файл с Google Drive
            self.drive_service.files().delete(fileId=file_id).execute()

            # 4. Обрабатываем ZIP для правильных имен
            self._process_zip_content(temp_zip, output_zip, original_name)

            # 5. Удаляем временный ZIP
            os.remove(temp_zip)

            return True

        except Exception as e:
            print(f"Ошибка конвертации: {e}")
            return False

    def _process_zip_content(self, temp_zip: str, output_zip: str, original_name: str):
        """Обрабатывает содержимое ZIP архива для правильных имен"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Распаковываем временный ZIP
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Находим HTML файл (обычно называется 'index.html' или подобное)
            html_file = self._find_html_file(temp_dir)
            if not html_file:
                raise FileNotFoundError("HTML файл не найден в архиве")

            # Переименовываем HTML файл
            new_html_path = os.path.join(os.path.dirname(html_file), f"{original_name}.html")
            os.rename(html_file, new_html_path)

            # Создаем новый ZIP с правильными именами
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        new_zip.write(file_path, arcname)

    def _find_html_file(self, directory: str) -> Optional[str]:
        """Находит HTML файл в распакованном архиве"""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.html'):
                    return os.path.join(root, file)
        return None

    def _authenticate(self) -> bool:
        """Аутентификация в Google Drive API"""
        try:
            self.creds = service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            return True
        except Exception as e:
            print(f"Ошибка аутентификации: {e}")
            return False
