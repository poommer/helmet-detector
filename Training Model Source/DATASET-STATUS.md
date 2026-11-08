# ผลตรวจ dataset และรอบทดลอง

โปรเจกต์: C:\Users\petom\helmet-yolo

- 1,564 ภาพ: train 1,288 / validation 138 / test 138
- 10 คลาส รวมสีหมวก หมวกประเภทอื่น คนไม่ใส่หมวก และ person
- ต้นฉบับอยู่ใน dataset และไม่ได้เปลี่ยนแปลง
- สร้าง dataset-detect แยกไว้ แปลง polygon 88 annotation เป็น bounding box (train 76 / validation 3 / test 9)
- ตรวจภาพและ label ในชุด detection ผ่าน ไม่มี label หายหรือพิกัดผิดรูปแบบ
- YOLO พบ annotation ซ้ำใน train 2 รายการและตัดออกจาก cache อัตโนมัติ
- เทรน YOLO26n 1 epoch และ validation สำเร็จบน RX 9070 XT
- weights: C:\Users\petom\helmet-yolo\runs\helmet-2\weights\best.pt
- validation mAP50 0.385 / mAP50-95 0.229 เป็นผลรอบทดลอง 1 epoch ยังไม่ใช่โมเดลพร้อมใช้งานจริง

ข้อจำกัดข้อมูล: helmet_green มี train 10 กรอบ / validation 3 / test 0; helmet_other มี train 4 / validation 0 / test 3 จึงควรเพิ่มตัวอย่างและกระจายทั้งสามชุดเพื่อประเมินสองคลาสนี้ได้

## เทรนเต็ม

เปิด PowerShell:

```powershell
cd C:\Users\petom\helmet-yolo
powershell -ExecutionPolicy Bypass -File .\train-full.ps1
```

ใช้ dataset-detect, 100 epochs, batch 4 และบันทึกผลเป็นโฟลเดอร์ใหม่ใน runs
รอบเต็มยังไม่ได้เริ่ม

หากแก้ dataset ต้นฉบับในอนาคต ต้องสร้างชุด detection ใหม่ให้ตรงกับข้อมูลล่าสุด; สคริปต์ prepare_detect.py จะไม่ทับ dataset-detect ที่มีอยู่
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

