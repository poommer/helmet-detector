import secrets

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse 
from src.config import validate_config
from src.routes.line_webhook import router as line_router 
from fastapi import Header, HTTPException
from pydantic import BaseModel

from src.config import ALERT_API_TOKEN
from src.services.line_service import send_alert_to_all
from .api.routes import router

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"


app = FastAPI(
    title="Helmet Detector YOLO11x Web Camera", 
    description="Helmet Detector and Line Notification System", 
    version="1.0.0"
)

# ให้บริการ CSS และ JavaScript
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static"
)

# API Routes
app.include_router(router)


# หน้าเว็บหลัก
@app.get("/")
async def index_page():
    return FileResponse(
        FRONTEND_DIR  / "index.html"
    )

@app.get("/") 
async def root(): 
    return {
        "status": "running",
        "service": "PPE Detection Alert API"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


app.include_router(line_router)

class heltectAlert(BaseModel):
    person_name: str = "Unknown"
    violation: str
    confidence: float
    camera_id: str = "Camera-01"
    detected_at: str
    image_url: str | None = None

@app.post("/api/alerts/ppe")
async def create_ppe_alert(
    alert: heltectAlert,
    x_alert_token: str = Header(...)
):

 if not secrets.compare_digest(
        x_alert_token,
        ALERT_API_TOKEN
    ):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

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

    result = await send_alert_to_all(message)

    if not result["success"]:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "LINE notification failed",
                "result": result
            }
        )

    return {
        "status": "success",
        "message": "PPE alert sent to LINE",
        "result": result
    }


