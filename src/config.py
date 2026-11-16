# ตั้งค่ากลางของระบบ: โหลดไฟล์ .env แล้วเก็บค่าคอนฟิกทั้งหมดไว้ที่เดียว
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent        # โฟลเดอร์ src/
load_dotenv(BASE_DIR.parent / ".env")             # โหลด .env จาก root ของ repo

# Token สำหรับเรียก LINE Messaging API (LINE Developers > Messaging API)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

# Secret สำหรับตรวจว่า webhook มาจาก LINE จริง (LINE Developers > Basic settings)
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

# ผู้รับแจ้งเตือนแบบกำหนดเอง ใส่ได้หลายคนคั่นด้วย , (ไม่บังคับ)
LINE_TO = [x.strip() for x in os.getenv("LINE_TO", "").split(",") if x.strip()]

# รหัสลับสำหรับเรียก /api/alerts/ppe จากระบบภายนอก
ALERT_API_TOKEN = os.getenv("ALERT_API_TOKEN", "")

# ไฟล์เก็บรายชื่อผู้รับที่ลงทะเบียนผ่าน webhook (สร้างให้อัตโนมัติ)
RECIPIENTS_FILE = BASE_DIR / "data" / "recipients.json"

# URL สาธารณะ (https) ของเซิร์ฟเวอร์ เช่น https://xxxx.trycloudflare.com
# ถ้าว่าง = ส่งการ์ดโดยไม่มีภาพ (LINE ต้องเปิดภาพจาก https ได้)
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

# โฟลเดอร์เก็บภาพหลักฐาน
SNAPSHOT_DIR = BASE_DIR / "data" / "snapshots"


def validate_config():
    # ตรวจว่าใส่ค่าที่จำเป็นใน .env ครบหรือยัง ถ้าไม่ครบให้หยุดตั้งแต่เปิดเซิร์ฟเวอร์
    required = {
        "LINE_CHANNEL_ACCESS_TOKEN": LINE_CHANNEL_ACCESS_TOKEN,
        "LINE_CHANNEL_SECRET": LINE_CHANNEL_SECRET,
        "ALERT_API_TOKEN": ALERT_API_TOKEN,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"ยังไม่ได้ตั้งค่าใน .env: {', '.join(missing)}")