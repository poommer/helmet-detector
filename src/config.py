import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

LINE_CHANNEL_ACCESS_TOKEN = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN", ""
)

LINE_CHANNEL_SECRET = os.getenv(
    "LINE_CHANNEL_SECRET", ""
)

# ไฟล์เก็บรายชื่อผู้้รับที่ลงทะเบียนนผ่าน webhook 
LINE_TO = [x.strip() for x in os.getenv("LINE_TO", "").split(",") if x.strip()]

#รหัสลับสำหรับเรีบก /api/alerts/ppe จากระบบภายนอก
ALERT_API_TOKEN = os.getenv("ALERT_API_TOKEN", "") 

RECIPIENTS_FILE = BASE_DIR / "data" / "recipients.json"

# URL สาธารณะ (https) ของเซิร์ฟเวอร์นี้ เช่น https://xxxx.ngrok-free.app
# LINE ต้องดึงรูปจาก URL นี้ ถ้าไม่ตั้ง จะส่งแค่ข้อความ ไม่มีรูป
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")

# โฟลเดอร์เก็บรูปหลักฐานที่ส่งไป LINE (เปิดให้เข้าถึงผ่าน /static/alerts/...)
ALERT_IMAGE_DIR = BASE_DIR / "frontend" / "static" / "alerts"

def validate_config():
    required = {
        "LINE_CHANNEL_ACCESS_TOKEN": LINE_CHANNEL_ACCESS_TOKEN,
        "LINE_CHANNEL_SECRET": LINE_CHANNEL_SECRET,
        "ALERT_API_TOKEN": ALERT_API_TOKEN,
    }

    missing = [
        name for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}"
        )
