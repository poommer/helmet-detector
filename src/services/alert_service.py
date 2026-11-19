import base64
import json
import threading
import time

from concurrent.futures import ThreadPoolExecutor

from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from ..integrations.line_client import LineClient
from ..config import ALERT_IMAGE_DIR


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
        image_keep_days=7,
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

        # Track ID ที่กำลังส่ง LINE อยู่ (ยังไม่รู้ผล) กันส่งซ้ำระหว่างรอ
        self.pending_ids = set()

        # ส่ง LINE ใน thread แยก เพื่อไม่ให้ /predict (และภาพจากกล้อง) ค้างรอ LINE ตอบ
        self._executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="line-alert",
        )

        # กันหลาย thread แก้ข้อมูลสถานะพร้อมกัน (thread ส่ง LINE กับ thread ตรวจเฟรม)
        self._lock = threading.Lock()

        # ลบรูปหลักฐานที่เก่ากว่ากี่วัน (เช็กอย่างมากชั่วโมงละครั้ง)
        self.image_keep_seconds = image_keep_days * 24 * 60 * 60
        self._last_image_cleanup = None

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

        # ID ที่เคยส่งไม่สำเร็จแล้วหายไปจากกล้องนาน ๆ ก็ลบทิ้ง ไม่ให้ค้างใน memory
        stale = [
            track_id
            for track_id, timestamp in self.last_attempt_by_id.items()
            if now - timestamp >= self.expire_seconds
            and track_id not in self.pending_ids
        ]

        for track_id in stale:
            self.last_attempt_by_id.pop(track_id, None)

    def _cleanup_old_images(self):
        # ลบรูปหลักฐานเก่า ไม่ให้โฟลเดอร์ static/alerts โตไปเรื่อย ๆ
        now = time.monotonic()
        if (
            self._last_image_cleanup is not None
            and now - self._last_image_cleanup < 60 * 60
        ):
            return
        self._last_image_cleanup = now

        cutoff = time.time() - self.image_keep_seconds
        try:
            for path in ALERT_IMAGE_DIR.glob("*.jpg"):
                if path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
        except OSError as err:
            print(f"[AlertService] Cannot clean old images: {err}")

    # ------------------------------------------
    # Create Alert Event
    # ------------------------------------------

    def _save_image(self, event_id, image_base64):
        # บันทึกภาพที่มีกรอบตรวจจับเป็นไฟล์ jpg เพื่อให้ LINE ดึงไปแสดง
        if not image_base64:
            return None
        try:
            ALERT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"{event_id}.jpg"
            (ALERT_IMAGE_DIR / filename).write_bytes(base64.b64decode(image_base64))
            self._cleanup_old_images()
            return filename
        except (OSError, ValueError) as err:
            print(f"[AlertService] Cannot save alert image: {err}")
            return None

    def _create_event(self, prediction, track_id, image_base64=None):
        context = self._get_context()
        event_id = str(uuid4())

        class_name = prediction.get("class")
        confidence = prediction.get("confidence", 0.0)

        return {
            "event_id": event_id,
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

            # ชื่อไฟล์รูปหลักฐาน (None = ไม่มีรูป)
            "image_file": self._save_image(event_id, image_base64),
        }

    # ------------------------------------------
    # Send Event to LineClient
    # ------------------------------------------

    def _dispatch_event(self, prediction, track_id, image_base64=None):
        # สร้าง event แล้วส่ง LINE ใน background ทันที ไม่รอผล
        # (ผลการส่งจะไปอัปเดต notified_ids ใน _send_in_background)
        event = self._create_event(
            prediction,
            track_id,
            image_base64,
        )
        event["delivery_status"] = "pending"

        if track_id is not None:
            self.pending_ids.add(track_id)

        self._executor.submit(self._send_in_background, event)

        return event

    def _send_in_background(self, event):
        track_id = event.get("track_id")

        try:
            success = self.line_client.send_alert(event)

        except Exception as err:
            print(f"[AlertService] LINE client error: {err}")
            success = False

        if not success:
            print(
                f"[AlertService] Delivery failed: "
                f"{event['event_id']}"
            )

        with self._lock:
            if track_id is None:
                return

            self.pending_ids.discard(track_id)

            if success:
                self.notified_ids[track_id] = time.monotonic()
                self.last_attempt_by_id.pop(track_id, None)

    # ------------------------------------------
    # Main Alert Processing
    # ------------------------------------------

    def process(self, predictions, image_base64=None):
        with self._lock:
            return self._process(predictions, image_base64)

    def _process(self, predictions, image_base64=None):
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

            # เคยแจ้งเตือนสำเร็จแล้ว (ยังไม่หมดอายุ) หรือกำลังส่งอยู่
            if track_id in self.notified_ids or track_id in self.pending_ids:
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

            event = self._dispatch_event(
                prediction,
                track_id,
                image_base64,
            )

            new_alerts.append(event)

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

            event = self._dispatch_event(
                prediction,
                None,
                image_base64,
            )

            new_alerts.append(event)

        return new_alerts