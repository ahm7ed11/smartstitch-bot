import os

from dotenv import load_dotenv

load_dotenv()

# --- Discord ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

# --- Google Drive ---
# الطريقة الافتراضية والموصى بها لحسابات Gmail الشخصية: OAuth (البوت بيرفع باسمك إنت)
# ملف الـ OAuth Client (Desktop app) اللي بتنزله من Google Cloud Console
GOOGLE_OAUTH_CLIENT_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_FILE", "oauth_client.json")
# ملف التوكن اللي بيتولد أول مرة تسجل دخول (بعد تشغيل authorize_drive.py)
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

# طريقة بديلة (لو عندك Google Workspace مدفوع وعامل Shared Drive):
# مسار ملف الـ Service Account (JSON) الخاص بجوجل درايف
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json"
)
# (اختياري) آيدي فولدر رئيسي على درايف هيتحط جواه كل الفصول
# لو سبته فاضي، البوت هيرفع الفولدرات على درايف الخاص بالـ Service Account نفسه
GOOGLE_DRIVE_PARENT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID", "").strip()

# --- SmartStitch Default Settings (زي اللي في الصورة اللي بعتها) ---
DEFAULT_OUTPUT_FORMAT = os.getenv("DEFAULT_OUTPUT_FORMAT", "jpg")        # .jpg
DEFAULT_LOSSY_QUALITY = int(os.getenv("DEFAULT_LOSSY_QUALITY", "95"))   # 95%
DEFAULT_SPLIT_HEIGHT = int(os.getenv("DEFAULT_SPLIT_HEIGHT", "12000"))  # Rough Output Height
DEFAULT_CUSTOM_WIDTH = int(os.getenv("DEFAULT_CUSTOM_WIDTH", "720"))    # Manual Custom Width
DEFAULT_DETECTION_TYPE = os.getenv("DEFAULT_DETECTION_TYPE", "pixel")
DEFAULT_SENSITIVITY = int(os.getenv("DEFAULT_SENSITIVITY", "90"))
DEFAULT_IGNORABLE_PIXELS = int(os.getenv("DEFAULT_IGNORABLE_PIXELS", "5"))
DEFAULT_SCAN_LINE_STEP = int(os.getenv("DEFAULT_SCAN_LINE_STEP", "5"))

# --- Misc ---
WORK_DIR = os.getenv("WORK_DIR", "temp_jobs")
MAX_ZIP_SIZE_MB = int(os.getenv("MAX_ZIP_SIZE_MB", "500"))
