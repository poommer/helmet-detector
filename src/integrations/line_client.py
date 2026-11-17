# ตัวกลางระหว่าง AlertService กับ LINE: แปลง event เป็นการ์ดแจ้งเตือน (Flex Message) แล้วส่งหาทุกคน
from datetime import datetime, timedelta, timezone

from ..config import PUBLIC_BASE_URL
from ..services.line_service import send_alert_to_all_sync

THAI_TZ = timezone(timedelta(hours=7))

RED = "#DC2626"
GREY = "#6B7280"
DARK = "#111827"


class LineClient:

    @staticmethod
    def _format_time(iso_time):
        # แปลงเวลา UTC จาก event เป็นเวลาไทย
        try:
            dt = datetime.fromisoformat(iso_time).astimezone(THAI_TZ)
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except (TypeError, ValueError):
            return str(iso_time)

    @staticmethod
    def _image_url(event):
        # URL รูปหลักฐาน (ต้องเป็น https ที่เปิดได้จากอินเทอร์เน็ต ไม่งั้น LINE โหลดไม่ได้)
        image_file = event.get("image_file")
        if image_file and PUBLIC_BASE_URL.startswith("https://"):
            return f"{PUBLIC_BASE_URL}/static/alerts/{image_file}"
        if image_file:
            print("[LineClient] ไม่ได้แนบรูป: ตั้ง PUBLIC_BASE_URL (https) ใน .env ก่อน")
        return None

    def _details(self, event):
        # ข้อมูลที่จะโชว์ในการ์ด เรียงจากบนลงล่าง
        violation = event.get("violation", {})
        device = event.get("device") or {}
        location = event.get("location") or {}

        place = " / ".join(
            part for part in (
                location.get("building"),
                location.get("floor"),
                location.get("zone"),
            ) if part
        ) or "-"

        track_id = event.get("track_id")

        return {
            "label": violation.get("label", "-"),
            "confidence": f"{violation.get('confidence', 0):.0%}",
            "place": place,
            "camera": f"{device.get('device_name', '-')} ({device.get('device_id', '-')})",
            "track": f"#{track_id}" if track_id is not None else "-",
            "time": self._format_time(event.get("occurred_at")),
        }

    @staticmethod
    def _row(title, value, value_color=DARK, bold=False):
        # 1 แถวในการ์ด: หัวข้อซ้าย / ค่าขวา
        return {
            "type": "box",
            "layout": "baseline",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": title, "size": "sm",
                 "color": GREY, "flex": 2},
                {"type": "text", "text": value, "size": "sm",
                 "color": value_color, "flex": 5, "wrap": True,
                 "weight": "bold" if bold else "regular"},
            ],
        }

    def _build_flex(self, event):
        d = self._details(event)
        image_url = self._image_url(event)

        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": RED,
                "paddingAll": "16px",
                "contents": [
                    {"type": "text", "text": "⚠️ แจ้งเตือนความปลอดภัย",
                     "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                    {"type": "text", "text": "Heltect · Helmet Detection",
                     "color": "#FEE2E2", "size": "xs", "margin": "sm"},
                ],
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {"type": "text", "text": d["label"], "weight": "bold",
                     "size": "xl", "color": RED, "wrap": True},
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "margin": "md",
                        "contents": [
                            self._row("ความมั่นใจ", d["confidence"], bold=True),
                            self._row("สถานที่", d["place"]),
                            self._row("กล้อง", d["camera"]),
                            self._row("Track ID", d["track"]),
                            self._row("เวลา", d["time"]),
                        ],
                    },
                ],
            },
        }

        if image_url:
            # รูปหลักฐานด้านบนการ์ด + ปุ่มเปิดดูรูปเต็ม
            bubble["hero"] = {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "4:3",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": image_url},
            }
            bubble["footer"] = {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "style": "primary", "color": RED,
                     "height": "sm",
                     "action": {"type": "uri", "label": "ดูภาพหลักฐาน",
                                "uri": image_url}},
                ],
            }

        return {
            "type": "flex",
            # ข้อความที่โชว์ในแจ้งเตือนมือถือ / รายการแชต (สูงสุด 400 ตัวอักษร)
            "altText": f"⚠️ {d['label']} ({d['confidence']}) · {d['place']}"[:400],
            "contents": bubble,
        }

    def send_alert(self, event: dict) -> bool:
        # True = ส่งสำเร็จอย่างน้อย 1 คน, False = ส่งไม่สำเร็จเลย
        result = send_alert_to_all_sync(
            [self._build_flex(event)],
            retry_key=event.get("event_id"),
        )
        return result["success"]
