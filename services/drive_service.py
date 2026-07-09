"""
Google Drive API wrapper.
بيستخدم Service Account عشان يقرا ويكتب على جوجل درايف.
"""
import io
import os
import re

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

import config
from utils.zip_utils import sanitize_name

SCOPES = ["https://www.googleapis.com/auth/drive"]

FOLDER_MIME = "application/vnd.google-apps.folder"

_service = None


class DriveError(Exception):
    pass


def get_service():
    """
    بيدور على وسيلة اتصال بجوجل درايف بالترتيب ده:
    1) OAuth (token.json) -> البوت بيرفع باسمك إنت، بيستخدم مساحتك (الطريقة الموصى بيها لحساب Gmail عادي)
    2) Service Account -> شغالة بس لو عندك Google Workspace وعامل Shared Drive
    """
    global _service
    if _service is not None:
        return _service

    creds = None
    token_path = config.GOOGLE_TOKEN_FILE
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())

    if not creds or not creds.valid:
        if os.path.exists(config.GOOGLE_SERVICE_ACCOUNT_FILE):
            creds = service_account.Credentials.from_service_account_file(
                config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
        else:
            raise DriveError(
                "محتاج تسجّل دخول جوجل درايف الأول. "
                "شغّل الأمر ده مرة واحدة من التيرمنال:\n"
                "python authorize_drive.py"
            )

    _service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return _service


# ---------------------------------------------------------------------------
# URL Parsing
# ---------------------------------------------------------------------------

FOLDER_PATTERNS = [
    r"drive\.google\.com/drive(?:/u/\d+)?/folders/([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/drive/mobile/folders/([a-zA-Z0-9_-]+)",
]

FILE_PATTERNS = [
    r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/uc\?(?:export=download&)?id=([a-zA-Z0-9_-]+)",
    r"[?&]id=([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
]


def is_drive_link(url: str) -> bool:
    return "drive.google.com" in url or "docs.google.com" in url


def extract_folder_id(url: str) -> str | None:
    for pattern in FOLDER_PATTERNS:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def extract_file_id(url: str) -> str | None:
    for pattern in FILE_PATTERNS:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Metadata / Download
# ---------------------------------------------------------------------------

def get_metadata(file_id: str) -> dict:
    service = get_service()
    try:
        return (
            service.files()
            .get(fileId=file_id, fields="id, name, mimeType, size", supportsAllDrives=True)
            .execute()
        )
    except Exception as e:
        raise DriveError(f"مقدرتش أجيب معلومات الملف/الفولدر من درايف: {e}")


def download_file_bytes(file_id: str, dest_path: str) -> str:
    service = get_service()
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    with io.FileIO(dest_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest_path


def list_children(folder_id: str) -> list[dict]:
    service = get_service()
    items = []
    page_token = None
    while True:
        resp = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def download_folder_recursive(folder_id: str, dest_dir: str) -> int:
    """
    بينزل كل الصور (وكمان الفولدرات الفرعية) من فولدر درايف لمسار محلي.
    بيرجع عدد الملفات اللي اتنزلت.
    """
    os.makedirs(dest_dir, exist_ok=True)
    children = list_children(folder_id)
    count = 0
    for item in children:
        name = sanitize_name(item["name"])
        if item["mimeType"] == FOLDER_MIME:
            count += download_folder_recursive(item["id"], os.path.join(dest_dir, name))
        elif item["mimeType"].startswith("image/"):
            download_file_bytes(item["id"], os.path.join(dest_dir, name))
            count += 1
    return count


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def create_folder(name: str, parent_id: str | None = None) -> str:
    service = get_service()
    metadata = {"name": name, "mimeType": FOLDER_MIME}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = (
        service.files()
        .create(body=metadata, fields="id", supportsAllDrives=True)
        .execute()
    )
    return folder["id"]


def upload_file(local_path: str, name: str, parent_id: str) -> str:
    service = get_service()
    metadata = {"name": name, "parents": [parent_id]}
    media = MediaFileUpload(local_path, resumable=True)
    uploaded = (
        service.files()
        .create(body=metadata, media_body=media, fields="id", supportsAllDrives=True)
        .execute()
    )
    return uploaded["id"]


def upload_directory(local_dir: str, drive_parent_id: str, progress_cb=None) -> str:
    """
    بترفع فولدر كامل (بكل الصور والفولدرات الفرعية اللي جواه) على درايف.
    بترجع آيدي الفولدر الرئيسي اللي اتعمل على درايف.
    progress_cb(done, total) -> بيتنادي بعد كل ملف يترفع.
    """
    all_files = []
    for root, _dirs, files in os.walk(local_dir):
        for f in files:
            all_files.append(os.path.join(root, f))
    total = max(len(all_files), 1)
    done = 0

    folder_id_cache = {local_dir: drive_parent_id}

    def get_or_create_drive_folder(local_path: str) -> str:
        if local_path in folder_id_cache:
            return folder_id_cache[local_path]
        parent_local = os.path.dirname(local_path)
        parent_drive_id = get_or_create_drive_folder(parent_local)
        folder_name = sanitize_name(os.path.basename(local_path))
        new_id = create_folder(folder_name, parent_drive_id)
        folder_id_cache[local_path] = new_id
        return new_id

    for root, _dirs, files in os.walk(local_dir):
        if not files:
            continue
        drive_folder_id = get_or_create_drive_folder(root)
        for f in sorted(files):
            upload_file(os.path.join(root, f), f, drive_folder_id)
            done += 1
            if progress_cb:
                progress_cb(done, total)

    return drive_parent_id


def make_public_readable(file_id: str):
    service = get_service()
    try:
        service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
            supportsAllDrives=True,
        ).execute()
    except Exception as e:
        raise DriveError(f"مقدرتش أخلي الفولدر متاح بالرابط: {e}")


def folder_link(file_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{file_id}"
