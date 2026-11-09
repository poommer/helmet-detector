"""
ไฟล์: src/detection.py
อัปเกรดระบบ Object Tracking (ByteTrack) และจำแนกกลุ่มคลาสหมวกนิรภัยทั้ง 8 คลาส
"""

from pathlib import Path
import base64
import cv2
import numpy as np
import torch
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "Training Model" / "model.pt"

# แบ่งกลุ่มคลาสจากโมเดลของคุณ
SAFE_HELMET_CLASSES = {
    "helmet_blue",
    "helmet_other",
    "helmet_red",
    "helmet_white",
    "helmet_yellow",
}
VIOLATION_CLASSES = {
    "not_helmet",
    "non_industrial_headwear",
}


class YOLODetector:
    def __init__(self, model_path: str | Path = DEFAULT_MODEL_PATH, conf_threshold: float = 0.45):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"ไม่พบไฟล์โมเดลที่: {self.model_path}")

        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        print(f"[YOLODetector] โหลดโมเดลจาก: {self.model_path} (Device: {self.device})")
        self.model = YOLO(str(self.model_path))
        self.conf_threshold = conf_threshold

    def detect_image_bytes(self, image_bytes: bytes, conf: float | None = None) -> dict:
        threshold = conf if conf is not None else self.conf_threshold

        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("ไม่สามารถอ่านข้อมูลภาพที่ส่งมาจากหน้าเว็บได้")

        # ใช้ model.track() คู่กับ ByteTrack และ persist=True เพื่อแจกเลข ID ติดตามแต่ละคนข้ามเฟรม
        results = self.model.track(
            source=frame,
            conf=threshold,
            device=self.device,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
        )[0]

        predictions = []
        for box in results.boxes:
            x1, y1, x2, y2 = [round(float(v), 1) for v in box.xyxy[0].tolist()]
            xc, yc, w, h = [round(float(v), 1) for v in box.xywh[0].tolist()]
            cls_id = int(box.cls[0].item())
            score = round(float(box.conf[0].item()), 3)
            cls_name = results.names.get(cls_id, str(cls_id))
            track_id = int(box.id[0].item()) if box.id is not None else None

            if cls_name in VIOLATION_CLASSES:
                category = "violation"
            elif cls_name in SAFE_HELMET_CLASSES:
                category = "safe"
            else:
                category = "person"

            predictions.append({
                "track_id": track_id,
                "class_id": cls_id,
                "class": cls_name,
                "category": category,
                "confidence": score,
                "bbox_xyxy": [x1, y1, x2, y2],
                "x": xc,
                "y": yc,
                "width": w,
                "height": h,
            })

        annotated_frame = results.plot()
        _, buffer = cv2.imencode(".jpg", annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        annotated_base64 = base64.b64encode(buffer).decode("utf-8")

        return {
            "width": frame.shape[1],
            "height": frame.shape[0],
            "count": len(predictions),
            "predictions": predictions,
            "annotated_image_base64": annotated_base64,
        }


if __name__ == "__main__":
    detector = YOLODetector()
    print("✅ โหลดโมเดลสำเร็จ! คลาสทั้งหมดในโมเดลของคุณคือ:", detector.model.names)