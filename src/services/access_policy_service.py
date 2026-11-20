import json
from pathlib import Path


HELMET_COLORS = {
    "helmet_blue": "blue",
    "helmet_white": "white",
    "helmet_yellow": "yellow",
    "helmet_red": "red",
    "helmet_other": "other",
}

VIOLATION_CLASSES = {
    "not_helmet",
    "non_industrial_headwear",
}

REASON_LABELS = {
    "not_helmet": "ตรวจพบว่าไม่สวมหมวกนิรภัย",
    "non_industrial_headwear": "ตรวจพบหมวกที่ไม่ใช่หมวกนิรภัยอุตสาหกรรม",
    "helmet_not_detected": "ไม่พบหมวกนิรภัยที่ยืนยันได้ จึงยังอนุมัติตามภาพไม่ได้",
    "no_detection": "ไม่พบวัตถุสำหรับประเมินในภาพ",
    "below_confidence": "ผลตรวจยังไม่ถึงเกณฑ์ความมั่นใจของพื้นที่",
    "unknown_color": "จำแนกสีหมวกไม่ได้ ต้องตรวจสอบเพิ่มเติม",
    "color_not_allowed": "สีหมวกไม่อยู่ในรายการที่พื้นที่อนุญาต",
    "allowed_color": "สีหมวกที่ตรวจพบอยู่ในรายการที่อนุญาต",
    "unmatched_person": "ยังยืนยันหมวกนิรภัยในกรอบบริเวณศีรษะของบุคคลไม่ได้",
}


class AccessPolicyService:
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir or Path(__file__).resolve().parents[1] / "data")

    def _load_json(self, filename, default):
        try:
            with (self.data_dir / filename).open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            return default

    def get_configuration(self):
        policy = self._load_json("access_policy.json", {})
        location_data = self._load_json("location.json", {})
        return {
            "policy": policy,
            "location": location_data.get("location", {}),
        }

    def evaluate(self, predictions):
        configuration = self.get_configuration()
        policy = configuration["policy"]
        allowed_colors = set(policy.get("allowed_helmet_colors", []))
        minimum_confidence = float(policy.get("minimum_confidence", 0.45))

        evaluated = []
        reasons = []
        saw_low_confidence = False
        saw_allowed_helmet = False
        has_denial = False
        needs_review = False

        for original in predictions:
            prediction = {**original}
            class_name = prediction.get("class")
            confidence = float(prediction.get("confidence", 0.0))
            color = HELMET_COLORS.get(class_name)

            if color is None and class_name not in VIOLATION_CLASSES:
                prediction["access_status"] = "review"
                prediction["access_reason"] = "helmet_not_detected"
                evaluated.append(prediction)
                continue

            if confidence < minimum_confidence:
                prediction["access_status"] = "review"
                prediction["access_reason"] = "below_confidence"
                evaluated.append(prediction)
                saw_low_confidence = True
                needs_review = True
                continue

            if class_name in VIOLATION_CLASSES:
                prediction["access_status"] = "denied"
                prediction["access_reason"] = class_name
                evaluated.append(prediction)
                has_denial = True
                reasons.append(class_name)
                continue

            if color == "other":
                prediction["access_status"] = "review"
                prediction["access_reason"] = "unknown_color"
                evaluated.append(prediction)
                needs_review = True
                reasons.append("unknown_color")
            elif color in allowed_colors:
                prediction["access_status"] = "allowed"
                prediction["access_reason"] = "allowed_color"
                evaluated.append(prediction)
                saw_allowed_helmet = True
            else:
                prediction["access_status"] = "denied"
                prediction["access_reason"] = "color_not_allowed"
                evaluated.append(prediction)
                has_denial = True
                reasons.append("color_not_allowed")

        if "person_helmet_match_required" in policy.get("conditions", []):
            persons = [
                prediction for prediction in evaluated
                if prediction.get("category") == "person"
            ]
            helmets = [
                prediction for prediction in evaluated
                if prediction.get("class") in HELMET_COLORS
                and prediction.get("access_status") in {"allowed", "denied"}
            ]

            for person in persons:
                person_box = person.get("bbox_xyxy")
                matched = any(
                    self._helmet_is_in_head_area(person_box, helmet.get("bbox_xyxy"))
                    for helmet in helmets
                )
                if not matched:
                    needs_review = True
                    reasons.append("unmatched_person")

        relevant_detections = [
            prediction for prediction in evaluated
            if prediction.get("class") in HELMET_COLORS
            or prediction.get("class") in VIOLATION_CLASSES
        ]

        if has_denial:
            status = "denied"
        elif needs_review or not relevant_detections or not saw_allowed_helmet:
            status = "review"
            if saw_low_confidence:
                reasons.append("below_confidence")
            elif not relevant_detections:
                reasons.append("no_detection" if not predictions else "helmet_not_detected")
            elif not saw_allowed_helmet and "unknown_color" not in reasons:
                reasons.append("helmet_not_detected")
        else:
            status = "allowed"
            reasons.append("allowed_color")

        labels = {
            "allowed": "ผ่านเงื่อนไขสีหมวก",
            "denied": "ไม่ผ่านเงื่อนไขพื้นที่",
            "review": "ต้องตรวจสอบเพิ่มเติม",
        }

        return {
            "predictions": evaluated,
            "access_evaluation": {
                "status": status,
                "label": labels[status],
                "reasons": list(dict.fromkeys(REASON_LABELS.get(reason, reason) for reason in reasons)),
                "allowed_helmet_colors": sorted(allowed_colors),
                "minimum_confidence": minimum_confidence,
                "mode": policy.get("mode", "assessment_only"),
            },
        }

    @staticmethod
    def _helmet_is_in_head_area(person_box, helmet_box):
        if (
            not isinstance(person_box, list)
            or not isinstance(helmet_box, list)
            or len(person_box) != 4
            or len(helmet_box) != 4
        ):
            return False

        person_left, person_top, person_right, person_bottom = person_box
        helmet_left, helmet_top, helmet_right, helmet_bottom = helmet_box
        helmet_center_x = (helmet_left + helmet_right) / 2
        helmet_center_y = (helmet_top + helmet_bottom) / 2
        head_area_bottom = person_top + (person_bottom - person_top) * 0.4

        return (
            person_left <= helmet_center_x <= person_right
            and person_top <= helmet_center_y <= head_area_bottom
        )
