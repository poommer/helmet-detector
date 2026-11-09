import json
import time

from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from ..integrations.line_client import LineClient


VIOLATION_CLASSES = {
    "not_helmet",
    "non_industrial_headwear",
}

THAI_CLASS_NAMES = {
    "not_helmet": "ไม่สวมหมวกนิรภัย",
    "non_industrial_headwear": "สวมหมวกผิดประเภท/ไม่ใช่หมวกเซฟตี้",
}


class AlertService:

    def __init__(
        self,
        line_client=None,
        confirm_frames=3,
        expire_seconds=300,
        retry_seconds=15,
        fallback_cooldown=15,
    ):
        self.line_client = line_client or LineClient()

        self.confirm_frames = confirm_frames
        self.expire_seconds = expire_seconds
        self.retry_seconds = retry_seconds
        self.fallback_cooldown = fallback_cooldown

        # จำนวนเฟรมที่พบการฝ่าฝืนแยกตาม Track ID
        self.violation_streak = {}

        # Track ID ที่ส่งแจ้งเตือนสำเร็จแล้ว
        self.notified_ids = {}

        # เวลาที่พยายามส่งล่าสุด แยกตาม Track ID
        self.last_attempt_by_id = {}

        # Fallback สำหรับกรณีไม่มี Track ID
        self.last_fallback_attempt = 0.0

        # Path ของ Mock Configuration
        self.data_dir = Path(__file__).resolve().parents[1] / "data"

    # ------------------------------------------
    # Load Mock Device & Location
    # ------------------------------------------

    def _load_json(self, filename, key):
        path = self.data_dir / filename

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            return data.get(key, {})

        except (FileNotFoundError, json.JSONDecodeError) as err:
            print(f"[AlertService] Cannot load {filename}: {err}")
            return {}

    def _get_context(self):
        device = self._load_json(
            "device.json",
            "device",
        )

        location = self._load_json(
            "location.json",
            "location",
        )

        return {
            "device": device,
            "location": location,
        }

    # ------------------------------------------
    # Cleanup Expired Track IDs
    # ------------------------------------------

    def _cleanup_old_ids(self, now):
        expired = [
            track_id
            for track_id, timestamp in self.notified_ids.items()
            if now - timestamp >= self.expire_seconds
        ]

        for track_id in expired:
            self.notified_ids.pop(track_id, None)
            self.violation_streak.pop(track_id, None)
            self.last_attempt_by_id.pop(track_id, None)

    # ------------------------------------------
    # Create Alert Event
    # ------------------------------------------

    def _create_event(self, prediction, track_id):
        context = self._get_context()

        class_name = prediction.get("class")
        confidence = prediction.get("confidence", 0.0)

        return {
            "event_id": str(uuid4()),
            "event_type": "helmet_violation",
            "occurred_at": datetime.now(timezone.utc).isoformat(),

            "track_id": track_id,

            "violation": {
                "class": class_name,
                "label": THAI_CLASS_NAMES.get(
                    class_name,
                    class_name,
                ),
                "confidence": confidence,
            },

            "device": context["device"],
            "location": context["location"],
        }

    # ------------------------------------------
    # Send Event to LineClient
    # ------------------------------------------

    def _dispatch_event(self, prediction, track_id):
        event = self._create_event(
            prediction,
            track_id,
        )

        try:
            success = self.line_client.send_alert(event)

        except Exception as err:
            print(f"[AlertService] LINE client error: {err}")
            success = False

        event["delivery_status"] = (
            "sent" if success else "failed"
        )

        if not success:
            print(
                f"[AlertService] Delivery failed: "
                f"{event['event_id']}"
            )

        return event, success

    # ------------------------------------------
    # Main Alert Processing
    # ------------------------------------------

    def process(self, predictions):
        now = time.monotonic()

        self._cleanup_old_ids(now)

        new_alerts = []

        # เก็บ Violation ของ Track ID ที่พบในเฟรมปัจจุบัน
        current_violations = {}

        # เก็บรายการที่ไม่มี Track ID
        fallback_violations = []

        for prediction in predictions:
            class_name = prediction.get("class")

            if class_name not in VIOLATION_CLASSES:
                continue

            track_id = prediction.get("track_id")

            if track_id is None:
                fallback_violations.append(prediction)
                continue

            # ถ้า Track ID ซ้ำในเฟรมเดียวกัน
            # เลือก Prediction ที่ Confidence สูงกว่า
            previous = current_violations.get(track_id)

            if (
                previous is None
                or prediction.get("confidence", 0)
                > previous.get("confidence", 0)
            ):
                current_violations[track_id] = prediction

        # Reset Streak ของ ID ที่ไม่พบการฝ่าฝืนในเฟรมนี้
        inactive_ids = (
            set(self.violation_streak)
            - set(current_violations)
        )

        for track_id in inactive_ids:
            self.violation_streak.pop(track_id, None)

        # --------------------------------------
        # Process Tracked Violations
        # --------------------------------------

        for track_id, prediction in current_violations.items():

            # เคยแจ้งเตือนสำเร็จแล้วและยังไม่หมดอายุ
            if track_id in self.notified_ids:
                continue

            self.violation_streak[track_id] = min(
                self.violation_streak.get(track_id, 0) + 1,
                self.confirm_frames,
            )

            if self.violation_streak[track_id] < self.confirm_frames:
                continue

            # ป้องกันการ Retry ทุกเฟรม
            last_attempt = self.last_attempt_by_id.get(
                track_id,
                0.0,
            )

            if now - last_attempt < self.retry_seconds:
                continue

            self.last_attempt_by_id[track_id] = now

            event, success = self._dispatch_event(
                prediction,
                track_id,
            )

            new_alerts.append(event)

            if success:
                self.notified_ids[track_id] = now
                self.last_attempt_by_id.pop(track_id, None)

        # --------------------------------------
        # Process Violations Without Track ID
        # --------------------------------------

        if (
            fallback_violations
            and now - self.last_fallback_attempt
            >= self.fallback_cooldown
        ):
            prediction = fallback_violations[0]

            self.last_fallback_attempt = now

            event, success = self._dispatch_event(
                prediction,
                None,
            )

            new_alerts.append(event)

        return new_alerts