from fastapi import APIRouter, File, UploadFile, Query

from ..services.helmet_service import HelmetService

router = APIRouter()

helmet_service = HelmetService()


@router.post("/predict")
async def predict_frame(
    file: UploadFile = File(...),
    conf: float = Query(0.45, ge=0.05, le=0.95),
):
    image_bytes = await file.read()

    result = helmet_service.process_frame(
        image_bytes,
        conf
    )

    return result