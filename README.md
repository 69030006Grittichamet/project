# SMART PARKING

โปรแกรมลานจอดรถ เขียนด้วย Python + Tkinter มี 2 โปรแกรมแยกกัน

| ไฟล์ | หน้าที่ |
|---|---|
| `smart_parking.py` | จุดรับตั๋วขาเข้า: ออกบัตร QR บันทึกเวลาเข้าลง MySQL (มีหน้าสแกนออกในตัวด้วย) |
| `smart_parking_exit.py` | จุดทางออก: สแกน QR ตั๋ว คิดค่าจอด และสร้าง PromptPay QR (เวอร์ชันนี้ไม่ต่อฐานข้อมูล) |

ชั่วโมงแรกฟรี จากนั้นชั่วโมงละ 20 บาท (แก้ได้ที่ `FREE_MINUTES` และ `RATE_PER_HOUR` ในไฟล์)

## ติดตั้ง
```
python -m pip install -r requirements.txt
```
ต้องมี MySQL ติดตั้งและเปิดอยู่ (สำหรับ `smart_parking.py`)

## ตั้งค่า (environment variable)
| ตัวแปร | ความหมาย |
|---|---|
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` | ที่อยู่และผู้ใช้ MySQL (ค่าเริ่มต้น localhost / 3306 / root) |
| `MYSQL_PASSWORD` | รหัสผ่าน MySQL |
| `PROMPTPAY_ID` | เบอร์พร้อมเพย์ที่รับเงิน |
| `ACCOUNT_NAME` | ชื่อบัญชีที่แสดงบนหน้าชำระเงิน |

ตัวอย่าง (Windows PowerShell):
```
$env:MYSQL_PASSWORD="รหัสผ่านของคุณ"
$env:PROMPTPAY_ID="0812345678"
$env:ACCOUNT_NAME="ชื่อ นามสกุล"
```

## รัน
```
python smart_parking.py
python smart_parking_exit.py
```
ตารางในฐานข้อมูลจะถูกสร้างอัตโนมัติเมื่อเปิด `smart_parking.py` ครั้งแรก

## หมายเหตุ
- ถ้าไม่มีกล้องหรือไม่ได้ติดตั้ง `opencv-python` ใช้ช่องวางรหัส QR แทนได้
- รันได้บน Windows / macOS / Linux (ต้องมีฟอนต์ไทยถึงจะบันทึกรูปเป็นภาษาไทยได้)
