import threading

from ..models.detection import YOLODetector
from .alert_service import AlertService
from .access_policy_service import AccessPolicyService


class HelmetService:

    def __init__(self):
        self._detect_lock = threading.Lock()
        self.detector = YOLODetector()
        self.alert_service = AlertService()
        self.access_policy_service = AccessPolicyService()

    def get_access_policy(self):
        return self.access_policy_service.get_configuration()

    def process_frame(self, image_bytes, conf=0.45, immediate_alert=True):

        # 1. AI Detection
        with self._detect_lock:
            result = self.detector.detect_image_bytes(
                image_bytes,
                conf=conf,
            )

        # 2. Area access assessment
        access_result = self.access_policy_service.evaluate(result["predictions"])
        predictions = access_result["predictions"]

        # 3. Uploaded images alert immediately; camera alerts need repeated frames.
        alerts = self.alert_service.process(
            predictions,
            image_base64=result.get("annotated_image_base64"),
            immediate=immediate_alert,
        )

        # 4. Return API Response
        return {
            "width": result["width"],
            "height": result["height"],
            "count": result["count"],
            "predictions": predictions,
            "annotated_image_base64": result.get("annotated_image_base64"),
            "access_evaluation": access_result["access_evaluation"],
            "new_alerts_count": len(alerts),
            "alerts": alerts,
        }
