# ตัวกลางระหว่าง AlertService กับ LINE: แปลง event เป็นข้อความแล้วส่งหาทุกคน
from ..services.line_service import send_alert_to_all_sync


class LineClient:

    def _build_text(self, event: dict) -> str:
        # แปลง event (dict) เป็นข้อความภาษาไทยที่จะโชว์ใน LINE
        violation = event.get("violation", {})
        device = event.get("device", {})
        location = event.get("location", {})

        return (
            "🚨 แจ้งเตือนความปลอดภัย\n"
            f"เหตุการณ์: {violation.get('label', '-')}\n"
            f"ความมั่นใจ: {violation.get('confidence', 0):.0%}\n"
            f"สถานที่: {location.get('building', '-')} / "
            f"{location.get('floor', '-')} / {location.get('zone', '-')}\n"
            f"กล้อง: {device.get('device_name', '-')} ({device.get('device_id', '-')})\n"
            f"Track ID: {event.get('track_id')}\n"
            f"เวลา (UTC): {event.get('occurred_at', '-')}"
        )

    def send_alert(self, event: dict) -> bool:
        # True = ส่งสำเร็จอย่างน้อย 1 คน, False = ส่งไม่สำเร็จเลย
        result = send_alert_to_all_sync(
            self._build_text(event),
            retry_key=event.get("event_id"),
        )
        return result["success"]