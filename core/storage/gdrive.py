import io
import logging
from typing import Any, Dict, BinaryIO
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.oauth2 import service_account
from core.storage.base import DocumentStore
from core.config import settings

logger = logging.getLogger(__name__)

class GoogleDriveDocumentStore(DocumentStore):
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self._service = None

    @property
    def service(self):
        if self._service is None:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self._service = build('drive', 'v3', credentials=creds)
        return self._service

    async def upload(self, file_content: BinaryIO, filename: str, mime_type: str) -> str:
        try:
            file_metadata = {'name': filename}
            media = MediaIoBaseUpload(file_content, mimetype=mime_type, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return file.get('id')
        except Exception as e:
            logger.error(f"Failed to upload to Google Drive: {e}")
            raise

    async def download(self, document_id: str) -> BinaryIO:
        try:
            request = self.service.files().get_media(fileId=document_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            fh.seek(0)
            return fh
        except Exception as e:
            logger.error(f"Failed to download from Google Drive: {e}")
            raise

    async def get_metadata(self, document_id: str) -> Dict[str, Any]:
        try:
            return self.service.files().get(fileId=document_id, fields='id, name, mimeType, size').execute()
        except Exception as e:
            logger.error(f"Failed to get metadata from Google Drive: {e}")
            raise
