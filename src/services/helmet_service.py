import threading

from ..models.detection import YOLODetector
from .alert_service import AlertService


class HelmetService:

    def __init__(self):
        self.detector = YOLODetector()
        self.alert_service = AlertService()

        # tracker ของ YOLO (ByteTrack, persist=True) จำสถานะข้ามเฟรม
        # จึงต้องตรวจทีละเฟรม ห้ามสอง thread เรียกพร้อมกัน
        self._detect_lock = threading.Lock()

    def process_frame(self, image_bytes, conf=0.45):

        # 1. AI Detection
        with self._detect_lock:
            result = self.detector.detect_image_bytes(
                image_bytes,
                conf=conf,
            )

        # 2. Alert Processing
        alerts = self.alert_service.process(
            result["predictions"],
            image_base64=result.get("annotated_image_base64"),
        )

        # 3. Return API Response
        return {
            "width": result["width"],
            "height": result["height"],
            "count": result["count"],
            "predictions": result["predictions"],
            "new_alerts_count": len(alerts),
            "alerts": alerts,
        }