from fastapi import APIRouter, File, UploadFile, Query
from fastapi.concurrency import run_in_threadpool

from ..services.helmet_service import HelmetService

router = APIRouter()

helmet_service = HelmetService()


@router.post("/predict")
async def predict_frame(
    file: UploadFile = File(...),
    conf: float = Query(0.45, ge=0.05, le=0.95),
):
    image_bytes = await file.read()

    # YOLO ใช้เวลานาน ให้รันใน threadpool จะได้ไม่บล็อกเซิร์ฟเวอร์ทั้งตัว
    # (ระหว่างนี้ /health, /line/webhook ยังตอบได้ตามปกติ)
    result = await run_in_threadpool(
        helmet_service.process_frame,
        image_bytes,
        conf,
    )

    return result
