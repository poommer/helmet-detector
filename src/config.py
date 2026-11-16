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
