# Helmet detection — Windows 11 / RX 9070 XT

โปรเจกต์นี้เทรนแบบ local ด้วย Ultralytics YOLO11n (yolo11n.pt) + AMD PyTorch ROCm

## ติดตั้ง

ใช้ Python 3.12 x64 และไดรเวอร์ AMD ที่รองรับ ROCm 7.2.1 (คู่มือ AMD ระบุ 26.2.2)
เปิด PowerShell ในโฟลเดอร์โปรเจกต์:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

สคริปต์ใช้ .venv แยกจาก Python หลัก ดาวน์โหลดไลบรารีจาก AMD และ PyPI
ไม่ติดตั้ง/เปลี่ยนไดรเวอร์ และไม่เริ่มเทรนอัตโนมัติ

## ใส่ dataset

Export Roboflow เป็น YOLO object detection แล้วแตก ZIP ลง dataset/:

```text
dataset/
  data.yaml
  train/images/   train/labels/
  valid/images/   valid/labels/
  test/images/    test/labels/  (ถ้ามี)
```

คลาสอ่านจาก data.yaml โดยตรง ต้องมี annotation สีและหมวกประเภทอื่นในข้อมูลจริง
ตัวอย่างชื่อ: safety_white, safety_yellow, safety_blue, non_safety_hat
อย่าเปลี่ยนเฉพาะชื่อคลาสโดยไม่ได้แก้ annotation ให้ตรงกัน
ถ้าต้องการตรวจคนไม่ใส่หมวก ให้เพิ่มคลาสและกรอบศีรษะที่ไม่ใส่หมวกด้วย

## ตรวจและเทรน

```powershell
.\.venv\Scripts\python.exe check_gpu.py
.\.venv\Scripts\python.exe train.py --check-data
.\.venv\Scripts\python.exe train.py --epochs 1
.\.venv\Scripts\python.exe train.py --epochs 100
```

weights จะอยู่ใน runs/helmet-yolo11*/weights/best.pt ดู path จริงจาก output ของ YOLO
การรันแต่ละครั้งสร้างโฟลเดอร์ใหม่ ไม่ทับผลเดิม
รอบแรกดาวน์โหลด pretrained weights; ใช้ --model กับไฟล์ .pt ในเครื่องได้
เริ่ม batch 4, workers 0, AMP ปิดสำหรับการตรวจระบบก่อน
หากหน่วยความจำไม่พอ ใช้ --batch 2
ลดการเปลี่ยนสีระหว่าง augmentation เพื่อรักษา label สีหมวก
ตั้ง MIOPEN_FIND_MODE=FAST ภายในโปรเจกต์เพื่อหลีกเลี่ยง solver benchmarking ที่ช้า/แจ้ง timing error บน Windows; อาจไม่เลือก kernel ที่เร็วที่สุด
แยกภาพจากคนละวิดีโอ/สถานที่ใน train/validation/test และประเมินรายคลาสบน test ที่ไม่ใช้เทรน

## ทดสอบภาพหรือวิดีโอ

```powershell
.\.venv\Scripts\python.exe predict.py --weights runs\helmet-yolo11\weights\best.pt --source "C:\path\video.mp4"
```

## อ้างอิง

- https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installrad/windows/install-pytorch.html
- https://docs.ultralytics.com/integrations/amd/

โมเดลจำแนกหมวกจากลักษณะในภาพ ไม่สามารถยืนยันการผ่านมาตรฐานความปลอดภัยของหมวกจริงได้

# YOLO11

เปลี่ยนโมเดลเริ่มต้นของ C:\Users\petom\helmet-yolo เป็น YOLO11n (yolo11n.pt) แล้ว
train.py และ train-full.ps1 ใช้โมเดลรุ่นนี้; train-full.ps1 รองรับ -Model สำหรับเลือกขนาดอื่น

ทดลองเทรน 1 epoch และ validation สำเร็จบน AMD RX 9070 XT ด้วย dataset-detect เดิม
validation mAP50 = 0.341 / mAP50-95 = 0.189 ผลนี้เป็นการตรวจระบบ ยังไม่ใช่การประเมินหลังเทรนเต็ม

โมเดลทดลอง: C:\Users\petom\helmet-yolo\runs\helmet-yolo11\weights\best.pt
ผลแต่ละรอบจะสร้างโฟลเดอร์ใหม่ใน runs/helmet-yolo11*

## เทรนเต็ม 100 epochs

```powershell
cd C:\Users\petom\helmet-yolo
powershell -ExecutionPolicy Bypass -File .\train-full.ps1
```

รอบเต็มยังไม่ได้เริ่ม

อ้างอิงชื่อไฟล์โมเดล: https://docs.ultralytics.com/models/yolo11/
# เทรน YOLO11n แบบเร็ว

เพิ่ม train-fast.ps1 ใน C:\Users\petom\helmet-yolo แล้ว

```powershell
cd C:\Users\petom\helmet-yolo
powershell -ExecutionPolicy Bypass -File .\train-fast.ps1
```

ค่าที่ใช้: YOLO11n, 100 epochs, batch 16, workers 4, AMP เปิด, cache RAM, imgsz 640, deterministic ปิด
ผลบันทึกใน runs/helmet-yolo11-fast* โดยสร้างโฟลเดอร์ใหม่แต่ละรอบ
train-full.ps1 ยังใช้ค่าชุดเดิม

## ผลทดสอบบนเครื่องนี้

- ทดสอบ 2 epochs ด้วย train 1,288 ภาพและ validation 138 ภาพ ผ่านครบและเซฟ weights
- GPU memory ประมาณ 2.45 GB บน RX 9070 XT
- time ใน results.csv เป็นเวลาสะสม: epoch 1 = 56.7622 วินาที, epoch 2 = 66.4055 วินาที
- รอบที่สองจึงใช้ประมาณ 9.64 วินาทีรวม validation ตามบันทึก trainer; รอบแรกมีต้นทุนเตรียมข้อมูล/workers/kernel
- validation mAP50 หลังรอบสอง = 0.47642 และ loss ไม่พบ NaN
- นี่เป็นการทดสอบสั้น; รอบเต็ม 100 epochs ยังไม่ได้เริ่ม
- รอบเต็มใช้ mosaic augmentation ในช่วงต้น ต่างจากการทดสอบสั้น 2 epochs ที่ปิด mosaic ตาม close_mosaic=10 ดังนั้นเวลารอบเต็มอาจมากกว่าตัวเลขนี้
- ไม่สรุปจำนวนเท่าที่เร็วขึ้นจากรอบเดิม เพราะผลเดิมมีเพียง epoch แรกและมีต้นทุนเริ่มต้นเช่นกัน
- batch และ precision ต่างจากค่าชุดเดิม จึงต้องประเมินความแม่นยำหลังเทรนเต็ม

## ตัวเลือก

```powershell
# ปิด AMP หากพบ NaN หรือปัญหา mixed precision
powershell -ExecutionPolicy Bypass -File .\train-fast.ps1 -NoAmp

# ลดการใช้หน่วยความจำ
powershell -ExecutionPolicy Bypass -File .\train-fast.ps1 -Batch 8

# หากมีปัญหา multiprocessing บน Windows
powershell -ExecutionPolicy Bypass -File .\train-fast.ps1 -Workers 0
```

ลดความละเอียดได้ด้วย -ImgSize 512 แต่ยังไม่ได้ทดสอบและอาจลดความแม่นยำกับหมวกขนาดเล็ก

อ้างอิงพารามิเตอร์: https://docs.ultralytics.com/modes/train/
อ้างอิง AMP บน AMD: https://docs.ultralytics.com/integrations/amd/

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

