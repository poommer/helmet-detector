# YOLO11x สำหรับ RX 9070 XT / Windows 11

โปรเจกต์: C:\Users\petom\helmet-yolo

## คำสั่งเทรนเต็ม

```powershell
cd C:\Users\petom\helmet-yolo
powershell -ExecutionPolicy Bypass -File .\train-x.ps1
```

ใช้ 100 epochs และ dataset-detect เดิม รอบเต็มยังไม่ได้เริ่ม
train-fast.ps1 เป็นโหมด YOLO11n เดิม; ใช้ train-x.ps1 เมื่อต้องการ YOLO11x

## ค่าที่ปรับและทดสอบแล้ว

| ค่า | การตั้งค่า |
|---|---|
| โมเดล | yolo11x.pt pretrained |
| Batch | 8 |
| ขนาดภาพ | 640 |
| Workers | 4 |
| Cache | RAM |
| Training precision | BF16 mixed precision |
| Validation precision | FP32 |
| Optimizer | AdamW |
| Learning rate | 0.0001 |
| Warmup bias learning rate | 0 |
| Deterministic | ปิด |
| การเปลี่ยน hue/saturation | ปิด เพื่อรักษา label สีหมวก |

FP16 พบ NaN กับ YOLO11x บนชุด PyTorch/ROCm นี้ จึงไม่ใช้เป็นค่าเริ่มต้นของรุ่น x
Ultralytics 8.4.177 ใช้ FP16 ใน training validation แม้ตั้ง training เป็น BF16 จึงเพิ่ม callback ใน train.py ให้ validation ใช้ FP32 โดยไม่แก้ไลบรารีที่ติดตั้ง
การลด learning rate ช่วยให้รอบทดลองไม่เกิด validation loss สูงแบบค่าที่ทดลองก่อนหน้า แต่ผลหลังเทรนเต็มยังต้องประเมิน
ค่าชุดนี้เป็นโปรไฟล์ที่ทดสอบผ่าน ไม่ได้พิสูจน์ว่าเป็นค่าที่เร็วที่สุดในทุกสถานการณ์

## ผลทดสอบสุดท้าย

- เทรน 1 epoch ด้วย train 1,288 ภาพ / validation 138 ภาพ ผ่านครบและเซฟโมเดล
- GPU memory ระหว่างเทรนประมาณ 8.08 GB
- train loss และ validation loss เป็นค่าปกติ ไม่มี NaN
- validation mAP50: 0.54118 / mAP50-95: 0.33404
- เวลาสะสมใน results.csv สำหรับรอบแรก 116.713 วินาที รวมต้นทุนเริ่มต้นและ validation; ไม่ใช่เวลาคงที่ต่อ epoch ของรอบเต็ม
- การทดลองสั้นปิด mosaic ตาม close_mosaic=10 ส่วนรอบเต็มเปิด mosaic ในช่วงต้น ทำให้เวลาและหน่วยความจำต่างกันได้
- weights รอบทดลองที่ผ่าน: C:\Users\petom\helmet-yolo\runs\helmet-yolo11x-6\weights\best.pt
- ผลรอบก่อนหน้าใน helmet-yolo11x ถึง helmet-yolo11x-5 เป็นการทดลอง ไม่ใช่โปรไฟล์สุดท้าย

คะแนนนี้เป็น validation หลังเทรนสั้น ไม่ใช่ accuracy ร้อยละ และยังไม่ใช่คะแนน test หลังเทรนเต็ม
helmet_green และ helmet_other มีตัวอย่างน้อย จึงยังต้องเพิ่มข้อมูลและประเมินรายคลาส

## ปรับค่าเอง

```powershell
# เปลี่ยนจำนวน epochs
powershell -ExecutionPolicy Bypass -File .\train-x.ps1 -Epochs 50

# ลดหน่วยความจำ
powershell -ExecutionPolicy Bypass -File .\train-x.ps1 -Batch 4

# FP32 ทั้งการเทรนและ validation (ช้ากว่า ใช้หน่วยความจำมากขึ้นต่อภาพ)
powershell -ExecutionPolicy Bypass -File .\train-x.ps1 -Precision fp32 -Batch 4
```

บันทึกผลแต่ละรอบเป็นโฟลเดอร์ใหม่ใน runs/helmet-yolo11x*
การเพิ่ม batch เกิน 8 ยังไม่ได้ทดสอบ ไม่รับประกันว่าจะเร็วขึ้นหรือพอดีกับ VRAM

โมเดลอ้างอิง: https://docs.ultralytics.com/models/yolo11/
