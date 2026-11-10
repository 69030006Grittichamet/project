"""
SMART PARKING - Desktop App (Python + Tkinter)
ติดตั้ง:  python -m pip install "qrcode[pil]" pillow opencv-python
รัน:      python smart_parking.py   (หรือกด Run ใน VS Code)
"""
import math
import os
import re
import sys
import time
from urllib.parse import parse_qs
import tkinter as tk
from tkinter import filedialog, messagebox

import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageTk

try:  # กล้องสแกน QR (ถ้าไม่มี ยังใช้ช่องวางรหัสได้)
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:  # ฐานข้อมูล MySQL
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

# ------------------------------------------------------------------ CONFIG
FREE_MINUTES = 60
RATE_PER_HOUR = 20
CURRENCY = "฿"
QR_PREFIX = "SMARTPARKING"

CHARCOAL = "#242424"
MIDGRAY = "#898989"
WHITE = "#ffffff"
LIGHT = "#f5f5f5"
BORDER = "#e3e5e8"
OK_FG, OK_BG = "#0a7d3c", "#eaf7ee"
ERR_FG = "#c0392b"
BLUE = "#0c3f6e"
FREE_FG, FREE_BG = "#0099ff", "#eaf5ff"

PROMPTPAY_ID = os.environ.get("PROMPTPAY_ID", "")
ACCOUNT_NAME = os.environ.get("ACCOUNT_NAME", "")
PAYMENT_TIMEOUT_SECONDS = 300
CAM_SIZE = 300

# ---- MySQL (แก้ตรงนี้ หรือกำหนดผ่าน environment variable)
DB_NAME = "smart_parking"
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
}

STR = {
    "th": {
        "home_badge": "จุดรับรถเข้า",
        "home_title": "รับบัตรจอดรถ",
        "home_sub": "กดปุ่มด้านล่างเพื่อออกบัตรตามเวลาปัจจุบัน",
        "issue_btn": "รับบัตรจอดรถ",
        "exit_btn": "ออกจากลานจอด",
        "ticket_badge": "เข้าจอดแล้ว",
        "ticket_title": "บัตรจอดรถของคุณ",
        "ticket_sub": "บันทึกเป็นรูปภาพ แล้วแสดง QR ด้านล่างตอนออกจากลานจอด",
        "label_id": "หมายเลขบัตร",
        "label_checkin": "เวลาเข้าจอด",
        "ticket_qr_note": "แสดง QR นี้ให้เครื่องสแกนตอนออก",
        "save_btn": "บันทึกบัตรเป็นรูปภาพ",
        "saved": "บันทึกแล้ว",
        "back_home": "กลับหน้าแรก",
        "footnote": f"ชั่วโมงแรกฟรี จากนั้นคิด {CURRENCY}{RATE_PER_HOUR} ต่อชั่วโมง",
        "exit_badge": "จุดออก",
        "exit_title": "สแกน QR เพื่อออกจากลานจอด",
        "exit_sub": "เล็งกล้องไปที่ QR บนบัตร หรือวางรหัสด้านล่างแล้วกด Enter",
        "calc_btn": "คำนวณ",
        "paste_btn": "วางจากคลิปบอร์ด",
        "label_duration": "ระยะเวลาจอด",
        "label_fee": "ค่าจอดรถ",
        "min": "นาที",
        "hr": "ชม.",
        "free": "ฟรี",
        "not_found_title": "ไม่พบข้อมูลบัตร",
        "not_found_sub": "รหัสไม่ถูกต้อง",
        "scan_status_opening": "กำลังเปิดกล้อง...",
        "scan_status_scanning": "กำลังสแกน...",
        "cam_fail": "เปิดกล้องไม่สำเร็จ ใช้ช่องวางรหัสแทนได้",
        "no_cv2": "ยังไม่ได้ติดตั้ง opencv-python ใช้ช่องวางรหัสแทนได้",
        "read_fail_title": "อ่าน QR ไม่สำเร็จ",
        "read_fail_sub": "โค้ดที่สแกนไม่ใช่บัตรจอดรถของระบบนี้ ลองใหม่อีกครั้ง",
        "retry_btn": "สแกนใหม่",
        "badge_free": "อยู่ในชั่วโมงฟรี",
        "badge_paid": "ชำระค่าบริการ",
        "receipt_title": "ออกจากลานจอดแล้ว",
        "label_checkout": "เวลาออก",
        "baht": "บาท",
        "free_note": "ไม่เกิน {m} นาทีแรก (ฟรี)",
        "paid_note": "คิด {h} ชม. x {c}{r}",
        "fname_label": "ชื่อบัญชี",
        "timer_label": "ชำระภายใน",
        "timer_expired_msg": "ราคาหมดอายุ กรุณาคำนวณใหม่ก่อนชำระเงิน",
        "refresh_price_btn": "คำนวณราคาใหม่",
        "save_receipt_btn": "บันทึกใบเสร็จเป็นรูปภาพ",
        "next_scan_btn": "สแกนคันถัดไป",
        "not_in_db_sub": "ไม่พบบัตรนี้ในระบบ",
        "already_exited_sub": "บัตรนี้ออกจากลานจอดไปแล้ว",
        "db_error_title": "เชื่อมต่อฐานข้อมูลไม่ได้",
        "db_error_sub": "ตรวจว่า MySQL เปิดอยู่ และรหัสผ่านถูกต้อง (ตัวแปร MYSQL_PASSWORD)",
        "badge_paid_done": "ชำระแล้ว",
        "confirm_paid_btn": "ยืนยันรับชำระเงินแล้ว",
        "lang_btn": "EN",
    },
    "en": {
        "home_badge": "Entry point",
        "home_title": "Get a parking ticket",
        "home_sub": "Press the button below to issue a ticket at the current time.",
        "issue_btn": "Get parking ticket",
        "exit_btn": "Exit parking",
        "ticket_badge": "Checked in",
        "ticket_title": "Your parking ticket",
        "ticket_sub": "Save it as an image. Show the QR below when you leave.",
        "label_id": "Ticket No.",
        "label_checkin": "Check-in time",
        "ticket_qr_note": "Show this QR to the scanner when you exit",
        "save_btn": "Save ticket as image",
        "saved": "Saved",
        "back_home": "Back to home",
        "footnote": f"First hour free, then {CURRENCY}{RATE_PER_HOUR} per hour",
        "exit_badge": "Exit point",
        "exit_title": "Scan QR to leave the car park",
        "exit_sub": "Point the camera at the ticket QR, or paste the code below and press Enter.",
        "calc_btn": "Calculate",
        "paste_btn": "Paste from clipboard",
        "label_duration": "Duration",
        "label_fee": "Parking fee",
        "min": "min",
        "hr": "h",
        "free": "Free",
        "not_found_title": "Ticket not found",
        "not_found_sub": "Invalid code.",
        "scan_status_opening": "Opening camera...",
        "scan_status_scanning": "Scanning...",
        "cam_fail": "Camera failed to open. Use the code box instead.",
        "no_cv2": "opencv-python is not installed. Use the code box instead.",
        "read_fail_title": "Couldn't read the QR",
        "read_fail_sub": "The scanned code isn't a parking ticket for this system. Please try again.",
        "retry_btn": "Scan again",
        "badge_free": "Within free hour",
        "badge_paid": "Payment due",
        "receipt_title": "Exited the car park",
        "label_checkout": "Check-out time",
        "baht": "THB",
        "free_note": "Within the first {m} minutes (free)",
        "paid_note": "{h} h x {c}{r}",
        "fname_label": "Account name",
        "timer_label": "Pay within",
        "timer_expired_msg": "Price expired, please recalculate before paying",
        "refresh_price_btn": "Recalculate price",
        "save_receipt_btn": "Save receipt as image",
        "next_scan_btn": "Scan next car",
        "not_in_db_sub": "This ticket is not in the system.",
        "already_exited_sub": "This ticket has already exited.",
        "db_error_title": "Database connection failed",
        "db_error_sub": "Check that MySQL is running and the password is correct (MYSQL_PASSWORD).",
        "badge_paid_done": "Paid",
        "confirm_paid_btn": "Confirm payment received",
        "lang_btn": "TH",
    },
}


# ------------------------------------------------------------------ LOGIC
def gen_ticket_id() -> str:
    t_hex = hex(int(time.time() * 1000))[2:].upper()
    return "P-" + t_hex[-6:]


def make_payload(ticket_id: str, t_ms: int) -> str:
    return f"{QR_PREFIX}|{ticket_id}|{t_ms}"


def parse_payload(text: str):
    """คืน (id, t_ms) หรือ None  (รองรับรูปแบบเดสก์ท็อป และลิงก์ QR จากเว็บเดิม)"""
    text = (text or "").strip()
    parts = text.split("|")
    if len(parts) == 3 and parts[0] == QR_PREFIX and parts[2].isdigit():
        return parts[1], int(parts[2])
    qs = text.split("#", 1)[-1].split("?", 1)[-1]
    q = parse_qs(qs)
    tid = (q.get("id") or [""])[0]
    t = (q.get("t") or [""])[0]
    if tid and t.isdigit() and int(t) > 0:
        return tid, int(t)
    return None


def calc_fee(t_ms: int, now_ms: int) -> dict:
    minutes = max(0, round((now_ms - t_ms) / 60000))
    if minutes <= FREE_MINUTES:
        return {"minutes": minutes, "hours_billed": 0, "fee": 0, "free": True}
    hours = math.ceil((minutes - FREE_MINUTES) / 60)
    return {"minutes": minutes, "hours_billed": hours, "fee": hours * RATE_PER_HOUR, "free": False}


def crc16(data: str) -> str:
    crc = 0xFFFF
    for ch in data:
        crc ^= ord(ch) << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def _tlv(i: str, v: str) -> str:
    return f"{i}{len(v):02d}{v}"


def promptpay_payload(phone: str, amount: float) -> str:
    """EMV PromptPay QR (เบอร์โทร + จำนวนเงิน) เรียง tag ตามลำดับ 00,01,29,53,54,58,63"""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("0"):
        digits = "66" + digits[1:]
    digits = digits.zfill(13)
    merchant = _tlv("00", "A000000677010111") + _tlv("01", digits)
    payload = _tlv("00", "01") + _tlv("01", "12" if amount else "11") + _tlv("29", merchant)
    payload += _tlv("53", "764")
    if amount:
        payload += _tlv("54", f"{amount:.2f}")
    payload += _tlv("58", "TH") + "6304"
    return payload + crc16(payload)


def fmt_duration(minutes: int, s: dict) -> str:
    h, m = divmod(minutes, 60)
    return f"{m} {s['min']}" if h <= 0 else f"{h} {s['hr']} {m} {s['min']}"


def fmt_dt(ms: int) -> str:
    return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(ms / 1000))


def _connect(with_db: bool = True):
    if not HAS_MYSQL:
        raise RuntimeError
    cfg = dict(DB_CONFIG)
    if with_db:
        cfg["database"] = DB_NAME
    return mysql.connector.connect(**cfg)


def init_db():
    con = _connect(with_db=False)
    try:
        cur = con.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4")
        cur.execute(f"USE `{DB_NAME}`")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS tickets ("
            " ticket_id VARCHAR(12) PRIMARY KEY,"
            " checkin_ms BIGINT NOT NULL,"
            " checkout_ms BIGINT NULL,"
            " fee INT NULL,"
            " status ENUM('parked','exited') NOT NULL DEFAULT 'parked')"
        )
        con.commit()
    finally:
        con.close()


def save_ticket(ticket_id: str, t_ms: int):
    con = _connect()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO tickets (ticket_id, checkin_ms) VALUES (%s, %s)", (ticket_id, t_ms))
        con.commit()
    finally:
        con.close()


def get_ticket(ticket_id: str):
    con = _connect()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM tickets WHERE ticket_id = %s", (ticket_id,))
        return cur.fetchone()
    finally:
        con.close()


def mark_exit(ticket_id: str, now_ms: int, fee: int):
    con = _connect()
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE tickets SET checkout_ms=%s, fee=%s, status='exited'"
            " WHERE ticket_id=%s AND status='parked'",
            (now_ms, fee, ticket_id),
        )
        con.commit()
    finally:
        con.close()


def make_qr_image(text: str, size: int) -> Image.Image:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img.resize((size, size), Image.NEAREST)


def find_thai_font():
    cands = [
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\LeelawUI.ttf",
        "/System/Library/Fonts/Supplemental/Tahoma.ttf",
        "/Library/Fonts/Tahoma.ttf",
        "/usr/share/fonts/truetype/tlwg/Loma.ttf",
        "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansThai-Regular.ttf",
    ]
    for p in cands:
        if os.path.exists(p):
            return p
    return None


def render_ticket_png(path: str, ticket_id: str, t_ms: int, lang: str):
    font_path = find_thai_font()
    s = STR[lang] if font_path else STR["en"]  # ไม่มีฟอนต์ไทย -> ใช้อังกฤษ

    def font(size):
        return ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()

    W, H = 640, 960
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 20, W - 20, H - 20), radius=28, outline=BORDER, width=2)

    d.text((60, 60), "SMART PARKING", font=font(34), fill=CHARCOAL)
    d.text((60, 120), s["ticket_title"], font=font(44), fill=CHARCOAL)
    d.text((60, 190), s["ticket_sub"], font=font(20), fill=MIDGRAY)

    y = 270
    for label, value in ((s["label_id"], ticket_id), (s["label_checkin"], fmt_dt(t_ms))):
        d.line((60, y - 14, W - 60, y - 14), fill=BORDER, width=1)
        d.text((60, y), label, font=font(24), fill=MIDGRAY)
        d.text((W - 60, y), value, font=font(26), fill=CHARCOAL, anchor="ra")
        y += 70

    qr = make_qr_image(make_payload(ticket_id, t_ms), 360)
    img.paste(qr, ((W - 360) // 2, y + 20))
    d.text((W // 2, y + 410), s["ticket_qr_note"], font=font(22), fill=MIDGRAY, anchor="ma")
    img.save(path)


def render_receipt_png(path: str, ticket_id: str, t_ms: int, now_ms: int, res: dict, lang: str):
    font_path = find_thai_font()
    s = STR[lang] if font_path else STR["en"]

    def font(size):
        return ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()

    W = 640
    H = 640 if res["free"] else 1060
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 20, W - 20, H - 20), radius=28, outline=BORDER, width=2)
    d.text((60, 60), "SMART PARKING", font=font(34), fill=CHARCOAL)
    d.text((60, 120), s["receipt_title"], font=font(40), fill=CHARCOAL)
    d.text((60, 180), f"{s['label_id']} {ticket_id}", font=font(22), fill=MIDGRAY)
    d.text((W // 2, 230), f"{CURRENCY}{res['fee']:,} {s['baht']}", font=font(60), fill=CHARCOAL, anchor="ma")

    y = 340
    rows = (
        (s["label_checkin"], fmt_dt(t_ms)),
        (s["label_checkout"], fmt_dt(now_ms)),
        (s["label_duration"], fmt_duration(res["minutes"], s)),
    )
    for label, value in rows:
        d.line((60, y - 14, W - 60, y - 14), fill=BORDER, width=1)
        d.text((60, y), label, font=font(22), fill=MIDGRAY)
        d.text((W - 60, y), value, font=font(24), fill=CHARCOAL, anchor="ra")
        y += 64

    if not res["free"]:
        qr = make_qr_image(promptpay_payload(PROMPTPAY_ID, res["fee"]), 320)
        d.text((W // 2, y + 10), "PromptPay", font=font(26), fill=BLUE, anchor="ma")
        img.paste(qr, ((W - 320) // 2, y + 60))
        d.text((60, y + 410), s["fname_label"], font=font(22), fill=MIDGRAY)
        d.text((W - 60, y + 410), ACCOUNT_NAME, font=font(24), fill=CHARCOAL, anchor="ra")
    img.save(path)


def ding(root: tk.Tk):
    try:
        if sys.platform.startswith("win"):
            import winsound
            winsound.Beep(1318, 90)
            winsound.Beep(1760, 160)
        else:
            root.bell()
    except Exception:
        pass


# ------------------------------------------------------------------ UI
class FlatButton(tk.Label):
    def __init__(self, parent, text, command, primary=True, **kw):
        bg, fg = (CHARCOAL, WHITE) if primary else (LIGHT, CHARCOAL)
        super().__init__(parent, text=text, bg=bg, fg=fg, cursor="hand2",
                         font=("Segoe UI", 11, "bold"), pady=11, **kw)
        self._bg, self._cmd = bg, command
        self.bind("<Button-1>", lambda e: self._cmd())
        self.bind("<Enter>", lambda e: self.config(bg=MIDGRAY if primary else BORDER))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SMART PARKING")
        self.configure(bg=WHITE)
        self.geometry("480x920")
        self.minsize(440, 700)
        self.lang = "th"
        self._img_refs = []
        self._paid = set()
        self._cap = None
        self._cam_job = None
        self._timer_job = None
        self._deadline = None
        self._deadline_key = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._screen = self.show_home
        self._screen_args = ()

        header = tk.Frame(self, bg=WHITE)
        header.pack(fill="x", padx=24, pady=(24, 8))
        tk.Label(header, text="SMART ", font=("Segoe UI", 16, "bold"), bg=WHITE, fg=CHARCOAL).pack(side="left")
        tk.Label(header, text="PARKING", font=("Segoe UI", 16), bg=WHITE, fg=MIDGRAY).pack(side="left")
        self.lang_btn = tk.Label(header, bg=LIGHT, fg=CHARCOAL, cursor="hand2",
                                 font=("Segoe UI", 9, "bold"), padx=12, pady=5)
        self.lang_btn.pack(side="right")
        self.lang_btn.bind("<Button-1>", lambda e: self.toggle_lang())

        self.body = tk.Frame(self, bg=WHITE)
        self.body.pack(fill="both", expand=True, padx=24, pady=8)

        self.show_home()
        self.after(300, self._check_db)

    # ---- helpers
    def t(self, key):
        return STR[self.lang][key]

    def toggle_lang(self):
        self.lang = "en" if self.lang == "th" else "th"
        self._screen(*self._screen_args)

    def _on_close(self):
        self._stop_camera()
        self.destroy()

    def _stop_camera(self):
        if self._cam_job:
            self.after_cancel(self._cam_job)
            self._cam_job = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _reset(self, screen, *args):
        self._stop_camera()
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None
        self._screen, self._screen_args = screen, args
        for w in self.body.winfo_children():
            w.destroy()
        self._img_refs.clear()
        self.lang_btn.config(text="🌐 " + self.t("lang_btn"))

    def _card(self):
        card = tk.Frame(self.body, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 16))
        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill="x", padx=24, pady=24)
        return inner

    def _badge(self, parent, text, ok=False, free=False):
        fg, bg = (OK_FG, OK_BG) if ok else (FREE_FG, FREE_BG) if free else (MIDGRAY, LIGHT)
        tk.Label(parent, text=text, font=("Segoe UI", 8, "bold"),
                 fg=fg, bg=bg, padx=10, pady=3).pack(anchor="w", pady=(0, 12))

    def _title(self, parent, title, sub):
        tk.Label(parent, text=title, font=("Segoe UI", 18, "bold"), bg=WHITE, fg=CHARCOAL,
                 anchor="w", justify="left", wraplength=360).pack(fill="x")
        tk.Label(parent, text=sub, font=("Segoe UI", 10), bg=WHITE, fg=MIDGRAY,
                 anchor="w", justify="left", wraplength=360).pack(fill="x", pady=(6, 18))

    def _row(self, parent, label, value, value_fg=CHARCOAL):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x")
        tk.Frame(row, bg=BORDER, height=1).pack(fill="x")
        inner = tk.Frame(row, bg=WHITE)
        inner.pack(fill="x", pady=10)
        tk.Label(inner, text=label, font=("Segoe UI", 10), bg=WHITE, fg=MIDGRAY).pack(side="left")
        tk.Label(inner, text=value, font=("Consolas", 11, "bold"), bg=WHITE, fg=value_fg).pack(side="right")

    # ---- screens
    def show_home(self):
        self._reset(self.show_home)
        c = self._card()
        self._badge(c, self.t("home_badge"))
        self._title(c, self.t("home_title"), self.t("home_sub"))
        FlatButton(c, self.t("issue_btn"), self.issue_ticket).pack(fill="x")
        FlatButton(c, self.t("exit_btn"), self.show_exit, primary=False).pack(fill="x", pady=(10, 0))
        tk.Label(self.body, text=self.t("footnote"), font=("Segoe UI", 9),
                 bg=WHITE, fg=MIDGRAY).pack(pady=8)

    def issue_ticket(self):
        ticket_id, t_ms = gen_ticket_id(), int(time.time() * 1000)
        try:
            save_ticket(ticket_id, t_ms)
        except Exception as e:
            messagebox.showerror(self.t("db_error_title"), f"{self.t('db_error_sub')}\n\n{e}")
            return
        self.show_ticket(ticket_id, t_ms)
        ding(self)

    def show_ticket(self, ticket_id, t_ms):
        self._reset(self.show_ticket, ticket_id, t_ms)
        c = self._card()
        self._badge(c, self.t("ticket_badge"), ok=True)
        self._title(c, self.t("ticket_title"), self.t("ticket_sub"))
        self._row(c, self.t("label_id"), ticket_id)
        self._row(c, self.t("label_checkin"), fmt_dt(t_ms))

        photo = ImageTk.PhotoImage(make_qr_image(make_payload(ticket_id, t_ms), 180))
        self._img_refs.append(photo)
        tk.Label(c, image=photo, bg=WHITE, highlightbackground=BORDER,
                 highlightthickness=1, padx=12, pady=12).pack(pady=(18, 8))
        tk.Label(c, text=self.t("ticket_qr_note"), font=("Segoe UI", 9),
                 bg=WHITE, fg=MIDGRAY).pack()

        FlatButton(self.body, self.t("save_btn"),
                   lambda: self.save_ticket(ticket_id, t_ms)).pack(fill="x")
        FlatButton(self.body, self.t("back_home"), self.show_home,
                   primary=False).pack(fill="x", pady=(10, 0))
        tk.Label(self.body, text=self.t("footnote"), font=("Segoe UI", 9),
                 bg=WHITE, fg=MIDGRAY).pack(pady=10)

    def save_ticket(self, ticket_id, t_ms):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=f"parking-ticket-{ticket_id}.png",
            filetypes=[("PNG image", "*.png")],
        )
        if not path:
            return
        try:
            render_ticket_png(path, ticket_id, t_ms, self.lang)
            messagebox.showinfo("SMART PARKING", f"{self.t('saved')}:\n{path}")
        except Exception as e:
            messagebox.showerror("SMART PARKING", str(e))

    # ---- database flow
    def _check_db(self):
        try:
            init_db()
        except Exception as e:
            messagebox.showerror(self.t("db_error_title"), f"{self.t('db_error_sub')}\n\n{e}")

    def handle_scan(self, parsed):
        if not parsed:
            return self.show_scan_error()
        ticket_id = parsed[0]
        try:
            row = get_ticket(ticket_id)
            if row is None:
                return self.show_scan_error("read_fail_title", "not_in_db_sub")
            if row["status"] == "exited":
                return self.show_scan_error("read_fail_title", "already_exited_sub")
            t_ms = int(row["checkin_ms"])  # ใช้เวลาจากฐานข้อมูล ไม่เชื่อเวลาใน QR
            now_ms = int(time.time() * 1000)
            if calc_fee(t_ms, now_ms)["free"]:
                mark_exit(ticket_id, now_ms, 0)
                self._paid.add(ticket_id)
        except Exception:
            return self.show_scan_error("db_error_title", "db_error_sub")
        self.show_receipt(ticket_id, t_ms, now_ms)

    def confirm_paid(self, ticket_id, t_ms, now_ms, fee):
        if time.time() > self._deadline:  # ราคาหมดอายุ -> คำนวณใหม่
            return self.show_receipt(ticket_id, t_ms)
        try:
            mark_exit(ticket_id, now_ms, fee)
        except Exception:
            return self.show_scan_error("db_error_title", "db_error_sub")
        self._paid.add(ticket_id)
        self.show_receipt(ticket_id, t_ms, now_ms)

    # ---- exit: scan
    def show_exit(self):
        self._reset(self.show_exit)
        c = self._card()
        self._badge(c, self.t("exit_badge"))
        self._title(c, self.t("exit_title"), self.t("exit_sub"))

        box = tk.Frame(c, bg="#000000", width=CAM_SIZE, height=CAM_SIZE)
        box.pack()
        box.pack_propagate(False)
        self.cam_label = tk.Label(box, bg="#000000")
        self.cam_label.pack(fill="both", expand=True)
        self.cam_status = tk.Label(c, text=self.t("scan_status_opening"), font=("Segoe UI", 10),
                                   bg=WHITE, fg=MIDGRAY, wraplength=360)
        self.cam_status.pack(pady=(10, 14))

        entry = tk.Entry(c, font=("Consolas", 11), relief="flat", bg=LIGHT, fg=CHARCOAL,
                         highlightbackground=BORDER, highlightthickness=1)
        entry.pack(fill="x", ipady=8)
        entry.focus_set()

        def submit(_=None):
            self.handle_scan(parse_payload(entry.get()))

        def paste():
            try:
                entry.delete(0, "end")
                entry.insert(0, self.clipboard_get())
            except tk.TclError:
                pass

        entry.bind("<Return>", submit)
        FlatButton(c, self.t("calc_btn"), submit).pack(fill="x", pady=(12, 0))
        FlatButton(c, self.t("paste_btn"), paste, primary=False).pack(fill="x", pady=(8, 0))
        FlatButton(self.body, self.t("back_home"), self.show_home, primary=False).pack(fill="x")

        if HAS_CV2:
            self.after(150, self._start_camera)
        else:
            self.cam_status.config(text=self.t("no_cv2"))

    def _start_camera(self):
        if self._screen != self.show_exit:
            return
        self.update_idletasks()
        backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
        cap = cv2.VideoCapture(0, backend)
        if not cap.isOpened():
            cap.release()
            self.cam_status.config(text=self.t("cam_fail"))
            return
        self._cap = cap
        self._detector = cv2.QRCodeDetector()
        self.cam_status.config(text=self.t("scan_status_scanning"))
        self._cam_loop()

    def _cam_loop(self):
        if self._cap is None:
            return
        ok, frame = self._cap.read()
        if ok:
            try:
                text, _, _ = self._detector.detectAndDecode(frame)
            except cv2.error:
                text = ""
            if text:
                parsed = parse_payload(text)
                self._stop_camera()
                self.handle_scan(parsed)
                return
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            w, h = img.size
            m = min(w, h)
            img = img.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2))
            photo = ImageTk.PhotoImage(img.resize((CAM_SIZE, CAM_SIZE)))
            self.cam_label.config(image=photo)
            self._cam_photo = photo
        self._cam_job = self.after(30, self._cam_loop)

    def show_scan_error(self, title_key="read_fail_title", sub_key="read_fail_sub"):
        self._reset(self.show_scan_error, title_key, sub_key)
        c = self._card()
        tk.Label(c, text=self.t(title_key), font=("Segoe UI", 18, "bold"),
                 bg=WHITE, fg=ERR_FG).pack(pady=(10, 6))
        tk.Label(c, text=self.t(sub_key), font=("Segoe UI", 10), bg=WHITE,
                 fg=MIDGRAY, wraplength=360, justify="center").pack(pady=(0, 18))
        FlatButton(c, self.t("retry_btn"), self.show_exit).pack(fill="x")

    # ---- exit: receipt + PromptPay
    def show_receipt(self, ticket_id, t_ms, now_ms=None):
        if now_ms is None:
            now_ms = int(time.time() * 1000)
        self._reset(self.show_receipt, ticket_id, t_ms, now_ms)
        res = calc_fee(t_ms, now_ms)
        c = self._card()
        paid = ticket_id in self._paid
        if res["free"]:
            self._badge(c, self.t("badge_free"), free=True)
        else:
            self._badge(c, self.t("badge_paid_done") if paid else self.t("badge_paid"), ok=True)
        self._title(c, self.t("receipt_title"), f"{self.t('label_id')} {ticket_id}")

        fee = tk.Frame(c, bg=WHITE)
        fee.pack(pady=(0, 2))
        tk.Label(fee, text=f"{CURRENCY}{res['fee']:,}", font=("Segoe UI", 30, "bold"),
                 bg=WHITE, fg=CHARCOAL).pack(side="left")
        tk.Label(fee, text=" " + self.t("baht"), font=("Segoe UI", 12, "bold"),
                 bg=WHITE, fg=MIDGRAY).pack(side="left", pady=(14, 0))
        note = (self.t("free_note").format(m=FREE_MINUTES) if res["free"] else
                self.t("paid_note").format(h=res["hours_billed"], c=CURRENCY, r=RATE_PER_HOUR))
        tk.Label(c, text=note, font=("Segoe UI", 9), bg=WHITE, fg=MIDGRAY).pack(pady=(0, 12))

        self._row(c, self.t("label_checkin"), fmt_dt(t_ms))
        self._row(c, self.t("label_checkout"), fmt_dt(now_ms))
        self._row(c, self.t("label_duration"), fmt_duration(res["minutes"], STR[self.lang]))

        if not res["free"] and not paid:
            key = (ticket_id, now_ms)
            if self._deadline_key != key:
                self._deadline_key = key
                self._deadline = time.time() + PAYMENT_TIMEOUT_SECONDS

            card = tk.Frame(c, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=(16, 0))
            hdr = tk.Frame(card, bg=BLUE)
            hdr.pack(fill="x")
            tk.Label(hdr, text="Thai QR Payment", font=("Segoe UI", 12, "bold"),
                     bg=BLUE, fg=WHITE, pady=10).pack()
            body = tk.Frame(card, bg=WHITE)
            body.pack(fill="x", padx=16, pady=14)
            tk.Label(body, text="PromptPay  พร้อมเพย์", font=("Segoe UI", 9, "bold"), fg=BLUE,
                     bg=WHITE, highlightbackground=BLUE, highlightthickness=1,
                     padx=10, pady=3).pack(pady=(0, 10))

            self.pay_box = tk.Frame(body, bg=WHITE)
            self.pay_box.pack()
            photo = ImageTk.PhotoImage(make_qr_image(promptpay_payload(PROMPTPAY_ID, res["fee"]), 180))
            self._img_refs.append(photo)
            tk.Label(self.pay_box, image=photo, bg=WHITE).pack()
            self.pay_timer = tk.Label(self.pay_box, font=("Consolas", 11, "bold"), bg=WHITE, fg=CHARCOAL)
            self.pay_timer.pack(pady=(8, 0))

            frow = tk.Frame(body, bg=WHITE)
            frow.pack(fill="x", pady=(12, 0))
            tk.Label(frow, text=self.t("fname_label"), font=("Segoe UI", 10, "bold"),
                     bg=WHITE, fg=CHARCOAL).pack(side="left")
            tk.Label(frow, text=ACCOUNT_NAME, font=("Segoe UI", 10), bg=WHITE,
                     fg=CHARCOAL).pack(side="right")
            self._tick()

        if not res["free"] and not paid:
            FlatButton(self.body, self.t("confirm_paid_btn"),
                       lambda: self.confirm_paid(ticket_id, t_ms, now_ms, res["fee"])
                       ).pack(fill="x", pady=(0, 10))
        FlatButton(self.body, self.t("save_receipt_btn"),
                   lambda: self.save_receipt(ticket_id, t_ms, now_ms, res)).pack(fill="x")
        FlatButton(self.body, self.t("next_scan_btn"), self.show_exit,
                   primary=False).pack(fill="x", pady=(10, 0))

    def _tick(self):
        remaining = math.ceil(self._deadline - time.time())
        if remaining <= 0:
            for w in self.pay_box.winfo_children():
                w.destroy()
            tk.Label(self.pay_box, text=self.t("timer_expired_msg"), font=("Segoe UI", 10, "bold"),
                     bg=WHITE, fg=ERR_FG, wraplength=300).pack(pady=(4, 12))
            ticket_id, t_ms = self._screen_args[0], self._screen_args[1]
            FlatButton(self.pay_box, self.t("refresh_price_btn"),
                       lambda: self.show_receipt(ticket_id, t_ms)).pack(fill="x")
            return
        m, sec = divmod(remaining, 60)
        self.pay_timer.config(text=f"{self.t('timer_label')} {m}:{sec:02d}",
                              fg=ERR_FG if remaining <= 60 else CHARCOAL)
        self._timer_job = self.after(500, self._tick)

    def save_receipt(self, ticket_id, t_ms, now_ms, res):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=f"parking-receipt-{ticket_id}.png",
            filetypes=[("PNG image", "*.png")],
        )
        if not path:
            return
        try:
            render_receipt_png(path, ticket_id, t_ms, now_ms, res, self.lang)
            messagebox.showinfo("SMART PARKING", f"{self.t('saved')}:\n{path}")
        except Exception as e:
            messagebox.showerror("SMART PARKING", str(e))


if __name__ == "__main__":
    App().mainloop()
