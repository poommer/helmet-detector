from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..services.helmet_service import HelmetService

router = APIRouter()

helmet_service = HelmetService()
MAX_IMAGE_BYTES = 10 * 1024 * 1024


@router.get("/api/access-policy")
async def access_policy():
    return helmet_service.get_access_policy()


@router.post("/predict")
async def predict_frame(
    file: UploadFile = File(...),
    conf: float = Query(0.45, ge=0.05, le=0.95),
    mode: Literal["image", "camera"] = Query("image"),
):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="กรุณาอัปโหลดไฟล์รูปภาพ")

    image_bytes = await file.read(MAX_IMAGE_BYTES + 1)
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="รูปภาพต้องมีขนาดไม่เกิน 10 MB")
    if not image_bytes:
        raise HTTPException(status_code=400, detail="ไฟล์รูปภาพว่างเปล่า")

    # YOLO ใช้เวลานาน ให้รันใน threadpool จะได้ไม่บล็อกเซิร์ฟเวอร์ทั้งตัว
    # (ระหว่างนี้ /health, /line/webhook ยังตอบได้ตามปกติ)
    try:
        result = await run_in_threadpool(
            helmet_service.process_frame,
            image_bytes,
            conf,
            mode == "image",
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    return result
