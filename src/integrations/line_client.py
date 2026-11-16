# ตัวกลางระหว่าง AlertService กับ LINE: แปลง event เป็นการ์ด Flex Message แล้วส่งหาทุกคน
from datetime import datetime, timedelta, timezone

from ..config import PUBLIC_BASE_URL
from ..services.line_service import send_alert_to_all_sync

THAI_TZ = timezone(timedelta(hours=7))   # เวลาประเทศไทย (UTC+7)


def to_thai_time(iso_text):
    # แปลงเวลา UTC แบบ ISO เป็นเวลาไทยที่อ่านง่าย เช่น 16/11/2026 20:59:03
    try:
        return datetime.fromisoformat(iso_text).astimezone(THAI_TZ).strftime("%d/%m/%Y %H:%M:%S")
    except (TypeError, ValueError):
        return "-"


def info_row(label, value):
    # 1 แถวข้อมูล: ป้ายสีเทาทางซ้าย + ค่าสีเข้มทางขวา
    return {
        "type": "box",
        "layout": "horizontal",          # วางของในกล่องนี้เรียงซ้าย -> ขวา
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#6B7280", "flex": 2},
            {"type": "text", "text": value, "size": "sm", "color": "#111827", "flex": 5, "wrap": True},
        ],
    }


class LineClient:

    def _build_text(self, event: dict) -> str:
        # ข้อความสั้นที่โชว์ในแจ้งเตือนมือถือ / แชทลิสต์ (LINE บังคับต้องมี)
        label = event.get("violation", {}).get("label", "-")
        zone = event.get("location", {}).get("zone", "-")
        return f"🚨 {label} — {zone}"

    def build_flex(self, event: dict) -> dict:
        # หน้าตาการ์ดแจ้งเตือน (แก้ดีไซน์ที่นี่)
        violation = event.get("violation", {})
        device = event.get("device", {})
        location = event.get("location", {})

        place = f"{location.get('building', '-')} · {location.get('zone', '-')}"
        confidence = f"{violation.get('confidence', 0):.0%}"

        bubble = {
            "type": "bubble",

            # ---------- ส่วนหัว: ชื่อระบบ + ป้าย CRITICAL ----------
            "header": {
                "type": "box",
                "layout": "horizontal",          # เรียงซ้าย -> ขวา
                "alignItems": "center",          # จัดให้อยู่กึ่งกลางแนวตั้ง
                "paddingBottom": "8px",
                "contents": [
                    {"type": "text", "text": "HELTECT Safety Alert",
                     "weight": "bold", "size": "md", "color": "#111827", "flex": 1},
                    {
                        # ป้าย CRITICAL พื้นชมพูอ่อน ตัวอักษรแดง
                        "type": "box",
                        "layout": "vertical",
                        "flex": 0,                   # กว้างเท่าที่ข้อความต้องใช้
                        "backgroundColor": "#FEE2E2",
                        "cornerRadius": "md",
                        "paddingAll": "4px",
                        "paddingStart": "8px",
                        "paddingEnd": "8px",
                        "contents": [
                            {"type": "text", "text": "CRITICAL", "size": "xxs",
                             "weight": "bold", "color": "#DC2626"},
                        ],
                    },
                ],
            },

            # ---------- เนื้อหา: เหตุการณ์ + รายละเอียด ----------
            "body": {
                "type": "box",
                "layout": "vertical",            # เรียงบน -> ล่าง
                "spacing": "md",
                "paddingTop": "4px",
                "contents": [
                    {"type": "text", "text": "SAFETY VIOLATION", "size": "xxs",
                     "color": "#6B7280", "weight": "bold"},
                    {"type": "text", "text": violation.get("label", "-"),
                     "weight": "bold", "size": "xl", "color": "#DC2626", "wrap": True},
                    {"type": "separator", "margin": "md", "color": "#E5E7EB"},
                    {
                        # กลุ่มแถวข้อมูล
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "margin": "md",
                        "contents": [
                            info_row("สถานที่", place),
                            info_row("กล้อง", device.get("device_name", "-")),
                            info_row("ความมั่นใจ", confidence),
                            info_row("เวลา", to_thai_time(event.get("occurred_at"))),
                        ],
                    },
                ],
            },

            # ---------- ท้ายการ์ด: ข้อความแนะนำ ----------
            "footer": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#F9FAFB",
                "contents": [
                    {"type": "text", "text": "กรุณาตรวจสอบพื้นที่โดยด่วน",
                     "size": "xs", "color": "#6B7280", "align": "center"},
                ],
            },
        }

        # ---------- ภาพหลักฐาน (ใส่เฉพาะเมื่อมีภาพ + มี URL สาธารณะ) ----------
        snapshot_file = event.get("snapshot_file")
        if snapshot_file and PUBLIC_BASE_URL:
            image_url = f"{PUBLIC_BASE_URL}/snapshots/{snapshot_file}"
            bubble["hero"] = {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "4:3",            # ตรงกับกล้อง 640x480
                "aspectMode": "cover",
                "action": {"type": "uri", "label": "ดูภาพ", "uri": image_url},  # แตะเพื่อเปิดภาพเต็ม
            }

        return bubble

    def send_alert(self, event: dict) -> bool:
        # True = ส่งสำเร็จอย่างน้อย 1 คน, False = ส่งไม่สำเร็จเลย
        flex_message = {
            "type": "flex",
            "altText": self._build_text(event),   # ข้อความที่เด้งบนหน้าจอมือถือ
            "contents": self.build_flex(event),
        }
        result = send_alert_to_all_sync(
            self._build_text(event),
            retry_key=event.get("event_id"),
            messages=[flex_message],
        )
        return result["success"]