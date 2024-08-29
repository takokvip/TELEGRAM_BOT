import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_KEYWORDS = ["lồn", "cặc", "buồi"]  # Các từ khóa mà quản trị viên muốn xóa
CHECKIN_KEYWORD = "okpay"  # Từ khóa để điểm danh
DIEMMOINGAY = 10  # Số điểm mỗi ngày
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", 0))  # ID chat của admin, đọc từ biến môi trường