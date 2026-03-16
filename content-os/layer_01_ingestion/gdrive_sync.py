"""
Sovereign Content OS — Layer 01: Google Drive Sync
Pulls new/modified files from Google Drive every 15 minutes.
Maintains a sync manifest to track what's been downloaded.
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_DRIVE_FOLDER_ID,
    VAULT_RAW,
    SYNC_MANIFEST
)

logger = logging.getLogger('content-os.ingestion.gdrive')

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
TOKEN_PATH = Path(__file__).parent.parent / 'config' / 'gdrive_token.json'

# Supported file types for content pipeline
SUPPORTED_MIMES = {
    'video/mp4': '.mp4',
    'video/quicktime': '.mov',
    'video/x-msvideo': '.avi',
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav',
    'audio/x-m4a': '.m4a',
    'audio/mp4': '.m4a',
    'application/pdf': '.pdf',
    'text/plain': '.txt',
    'application/vnd.google-apps.document': '.gdoc',
}


def get_drive_service():
    """Authenticate and return Google Drive service."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def load_manifest():
    """Load sync manifest (tracks downloaded files)."""
    if SYNC_MANIFEST.exists():
        return json.loads(SYNC_MANIFEST.read_text())
    return {'files': {}, 'last_sync': None}


def save_manifest(manifest):
    """Save sync manifest."""
    manifest['last_sync'] = datetime.now().isoformat()
    SYNC_MANIFEST.write_text(json.dumps(manifest, indent=2))


def sync_drive():
    """
    Main sync function — pulls new/modified files from Google Drive.
    Returns count of new files downloaded.
    """
    logger.info('Starting Google Drive sync...')

    if not GOOGLE_DRIVE_FOLDER_ID:
        logger.warning('GOOGLE_DRIVE_FOLDER_ID not set, skipping sync')
        return 0

    try:
        service = get_drive_service()
        manifest = load_manifest()
        new_count = 0

        # Query for files in the target folder
        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            pageSize=100,
            fields='nextPageToken, files(id, name, mimeType, modifiedTime, size)',
            orderBy='modifiedTime desc'
        ).execute()

        files = results.get('files', [])
        logger.info(f'Found {len(files)} files in Drive folder')

        for file in files:
            file_id = file['id']
            file_name = file['name']
            mime_type = file['mimeType']
            modified_time = file['modifiedTime']

            # Skip unsupported file types
            if mime_type not in SUPPORTED_MIMES:
                continue

            # Check if already synced and unchanged
            if file_id in manifest['files']:
                if manifest['files'][file_id]['modified'] == modified_time:
                    continue

            # Download the file
            ext = SUPPORTED_MIMES[mime_type]
            safe_name = ''.join(c for c in file_name if c.isalnum() or c in '._- ')
            dest_path = VAULT_RAW / f'{safe_name}{ext}'

            if mime_type.startswith('application/vnd.google-apps'):
                # Export Google Docs as plain text
                request = service.files().export_media(
                    fileId=file_id, mimeType='text/plain'
                )
            else:
                request = service.files().get_media(fileId=file_id)

            with open(dest_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

            # Update manifest
            manifest['files'][file_id] = {
                'name': file_name,
                'local_path': str(dest_path),
                'mime': mime_type,
                'modified': modified_time,
                'synced_at': datetime.now().isoformat()
            }
            new_count += 1
            logger.info(f'Downloaded: {file_name}')

        save_manifest(manifest)
        logger.info(f'Drive sync complete. {new_count} new files.')
        return new_count

    except Exception as e:
        logger.error(f'Drive sync failed: {e}')
        return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    count = sync_drive()
    print(f'Synced {count} new files from Google Drive')
