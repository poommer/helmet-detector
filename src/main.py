# จุดเริ่มต้นของเว็บแอป: รวมหน้าเว็บ, API ตรวจจับหมวก, webhook LINE และ API แจ้งเตือน
import secrets
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import ALERT_API_TOKEN, validate_config

validate_config()  # ตรวจ .env ก่อน (ก่อนโหลดโมเดลที่ใช้เวลานาน)

from .api.routes import router as detect_router          # noqa: E402  API /predict
from .routes.line_webhook import router as line_router   # noqa: E402  /line/webhook
from .services.line_service import send_alert_to_all     # noqa: E402

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Helmet Detector YOLO11x Web Camera",
    description="Helmet Detector and LINE Notification System",
    version="1.0.0",
)

# ให้บริการ CSS/JS เฉพาะเมื่อมีโฟลเดอร์ static (ไม่มีแล้วจะ error)
if (FRONTEND_DIR / "static").is_dir():
    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_DIR / "static"),
        name="static",
    )

# ลงทะเบียน API ย่อย
app.include_router(detect_router)   # POST /predict
app.include_router(line_router)     # POST /line/webhook


@app.get("/")
async def index_page():
    # หน้าเว็บกล้อง
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/status")
async def status():
    # เช็กว่าเซิร์ฟเวอร์ทำงานอยู่ (ย้ายมาจาก "/" เพราะซ้ำกับหน้าเว็บ)
    return {"status": "running", "service": "PPE Detection Alert API"}


@app.get("/health")
async def health():
    # ใช้ตรวจสุขภาพระบบ
    return {"status": "healthy"}


class HeltectAlert(BaseModel):
    # รูปแบบข้อมูลที่ระบบภายนอกต้องส่งมาที่ /api/alerts/ppe
    person_name: str = "Unknown"
    violation: str
    confidence: float
    camera_id: str = "Camera-01"
    detected_at: str
    image_url: str | None = None


@app.post("/api/alerts/ppe")
async def create_ppe_alert(alert: HeltectAlert, x_alert_token: str = Header(...)):
    # ตรวจรหัสลับใน header X-Alert-Token (compare_digest กันการเดารหัสจากเวลา)
    if not secrets.compare_digest(x_alert_token, ALERT_API_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # สร้างข้อความแจ้งเตือน
    message = (
        "🚨 PPE SAFETY ALERT\n\n"
        f"บุคคล: {alert.person_name}\n"
        f"เหตุการณ์: {alert.violation}\n"
        f"ความมั่นใจ: {alert.confidence:.2%}\n"
        f"กล้อง: {alert.camera_id}\n"
        f"เวลา: {alert.detected_at}"
    )
    if alert.image_url:
        message += f"\nภาพหลักฐาน: {alert.image_url}"

    # ส่งหาผู้รับทุกคน
    result = await send_alert_to_all(message)

    if not result["success"]:
        raise HTTPException(
            status_code=502,
            detail={"message": "LINE notification failed", "result": result},
        )

    return {"status": "success", "message": "PPE alert sent to LINE", "result": result}