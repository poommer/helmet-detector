from ..models.detection import YOLODetector
from .alert_service import AlertService


class HelmetService:

    def __init__(self):
        self.detector = YOLODetector()
        self.alert_service = AlertService()

    def process_frame(self, image_bytes, conf=0.45):

        # 1. AI Detection
        result = self.detector.detect_image_bytes(
            image_bytes,
            conf=conf,
        )

        # 2. Alert Processing
        alerts = self.alert_service.process(
            result["predictions"]
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