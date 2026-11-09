class LineClient:

    def send_alert(self, event: dict) -> bool:
        """
        รับ Alert Event จาก AlertService

        Returns:
            True  = ส่ง LINE สำเร็จ
            False = ส่ง LINE ไม่สำเร็จ
        """

        print(f"event: {event}")

        pass