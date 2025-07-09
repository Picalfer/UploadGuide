import io
import os
from typing import Tuple, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


def convert(word_path):
    converter = WordToHtmlConverter()
    success, path = converter.convert(word_path)
    if not success or not path:
        raise ValueError("Ошибка конвертации")
    return path


class WordToHtmlConverter:
    """
    Конвертер Word в HTML+ZIP
    Сохраняет точное оригинальное имя для всех файлов
    """

    def __init__(self, service_account_file: str = 'service_account.json'):
        self.SERVICE_ACCOUNT_FILE = service_account_file
        self.creds = None
        self.drive_service = None

    def convert(self, word_path) -> Tuple[bool, Optional[str]]:
        try:
            original_name = os.path.splitext(os.path.basename(word_path))[0]
            output_zip = os.path.join(os.getcwd(), f"{original_name}.zip")

            if self._convert_to_zip(word_path, output_zip, original_name):
                print(f"✅ Конвертация прошла успешно. Файл сохранён: {output_zip}")
                return True, output_zip

            print("❌ Конвертация не удалась.")
            return False, None

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False, None

    def _convert_to_zip(self, word_path: str, output_zip: str, original_name: str) -> bool:
        if not self._authenticate():
            print("Ошибка аутентификации Google Drive")
            return False

        try:
            file_metadata = {
                'name': original_name,
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

            with io.FileIO(output_zip, 'wb') as fh:
                downloader = MediaIoBaseDownload(
                    fh,
                    self.drive_service.files().export_media(
                        fileId=file_id,
                        mimeType='application/zip'
                    )
                )
                while not downloader.next_chunk()[1]:
                    pass

            self.drive_service.files().delete(fileId=file_id).execute()

            return True

        except Exception as e:
            print(f"Ошибка конвертации: {e}")
            return False

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
