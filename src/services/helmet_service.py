# บริการหลักของระบบ: รับภาพจากกล้อง -> ตรวจจับด้วย AI -> ส่งต่อให้ระบบแจ้งเตือน
import base64

from ..models.detection import YOLODetector
from .alert_service import AlertService


class HelmetService:

    def __init__(self):
        self.detector = YOLODetector()        # โมเดล YOLO สำหรับตรวจจับหมวก
        self.alert_service = AlertService()   # ระบบตัดสินใจว่าจะแจ้งเตือนหรือไม่

    def process_frame(self, image_bytes, conf=0.45):

        # 1. ตรวจจับด้วย AI
        result = self.detector.detect_image_bytes(
            image_bytes,
            conf=conf,
        )

        # 2. ส่งผลตรวจจับ + ภาพที่มีกรอบ ไปให้ระบบแจ้งเตือน
        #    (detection.py ส่งภาพมาเป็น base64 ต้องแปลงกลับเป็นไฟล์ jpg ก่อน)
        snapshot_jpeg = base64.b64decode(result["annotated_image_base64"])
        alerts = self.alert_service.process(
            result["predictions"],
            snapshot_jpeg=snapshot_jpeg,
        )

        # 3. ส่งผลกลับไปให้หน้าเว็บ (ไม่ส่งภาพกลับ เพราะหน้าเว็บวาดกรอบเอง)
        return {
            "width": result["width"],
            "height": result["height"],
            "count": result["count"],
            "predictions": result["predictions"],
            "new_alerts_count": len(alerts),
            "alerts": alerts,
        }