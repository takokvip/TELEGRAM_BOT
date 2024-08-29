from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import json
from datetime import datetime
import logging
from config.settings import DIEMMOINGAY
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

USER_POINTS_FILE = "user_points.json"

def load_user_points():
    try:
        with open(USER_POINTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File {USER_POINTS_FILE} not found. Creating new data structure.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding {USER_POINTS_FILE}. Resetting data.")
        return {}

def save_user_points(points):
    try:
        with open(USER_POINTS_FILE, 'w') as f:
            json.dump(points, f, indent=4)
    except IOError as e:
        logger.error(f"Error saving user points: {e}")

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    username = update.message.from_user.username
    user_name = update.message.from_user.full_name
    
    if not username:
        await update.message.reply_text("Bạn cần đặt username để có thể điểm danh.")
        return

    user_data = load_user_points()

    if chat_id not in user_data:
        user_data[chat_id] = {}

    if username not in user_data[chat_id]:
        user_data[chat_id][username] = {
            "points": 0,
            "last_checkin": None,
            "warnings": 0,
            "checkin_count": 0
        }

    now = datetime.now()
    today = now.date()

    last_checkin_date = user_data[chat_id][username]["last_checkin"]
    if last_checkin_date:
        last_checkin_date = datetime.strptime(last_checkin_date, "%Y-%m-%d %H:%M:%S").date()
        if last_checkin_date == today:
            await update.message.reply_html(
                f"Chào <b>{user_name}</b>, bạn đã điểm danh hôm nay rồi. Hãy quay lại vào ngày mai nhé!"
            )
            return

    user_data[chat_id][username]["points"] += DIEMMOINGAY
    user_data[chat_id][username]["last_checkin"] = now.strftime("%Y-%m-%d %H:%M:%S")
    user_data[chat_id][username]["checkin_count"] += 1
    save_user_points(user_data)

    await update.message.reply_html(
        f"Chào <b>{user_name}</b>, chúc bạn một ngày tốt lành!\n"
        f"Điểm danh thành công <b>+{DIEMMOINGAY} điểm</b>\n"
        f"Tổng bạn có <b>{user_data[chat_id][username]['points']} điểm</b>\n"
        f"Số ngày điểm danh: <b>{user_data[chat_id][username]['checkin_count']} ngày</b>"
    )
    logger.info(f"User {username} checked in successfully in chat {chat_id}")

async def checkdiem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    username = update.message.from_user.username
    
    if not username:
        await update.message.reply_text("Bạn cần đặt username để có thể kiểm tra điểm.")
        return

    user_data = load_user_points()

    if chat_id in user_data and username in user_data[chat_id]:
        points = user_data[chat_id][username]["points"]
        checkin_count = user_data[chat_id][username]["checkin_count"]
        last_checkin = user_data[chat_id][username]["last_checkin"]
        last_checkin_datetime = datetime.strptime(last_checkin, "%Y-%m-%d %H:%M:%S")
        last_checkin_formatted = last_checkin_datetime.strftime("%d/%m/%Y - %H:%M")

        await update.message.reply_html(
            f"Số điểm của bạn là: <b>{points}</b>\n"
            f"Số ngày điểm danh: <b>{checkin_count}</b>\n"
            f"Ngày điểm danh gần nhất: <b>{last_checkin_formatted}</b>"
        )
    else:
        await update.message.reply_text("Bạn chưa có điểm nào. Hãy bắt đầu điểm danh để tích lũy điểm!")

async def sendmoney(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    sender_username = update.message.from_user.username
    sender_name = update.message.from_user.full_name

    if not sender_username:
        await update.message.reply_text("Bạn cần đặt username để có thể gửi điểm.")
        return

    user_data = load_user_points()

    if chat_id not in user_data:
        user_data[chat_id] = {}

    if sender_username not in user_data[chat_id]:
        await update.message.reply_text("Bạn chưa có điểm nào để gửi.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Vui lòng nhập đúng cú pháp: /sendmoney @username {số điểm}")
        return

    recipient_username = context.args[0].lstrip('@')
    try:
        points_to_send = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Số điểm phải là một số nguyên.")
        return

    if points_to_send <= 0:
        await update.message.reply_text("Số điểm phải lớn hơn 0.")
        return

    if recipient_username not in user_data[chat_id]:
        user_data[chat_id][recipient_username] = {
            "points": 0,
            "last_checkin": None,
            "warnings": 0,
            "checkin_count": 0
        }

    if user_data[chat_id][sender_username]["points"] < points_to_send:
        await update.message.reply_text("Bạn không đủ điểm để gửi.")
        return

    # Trừ điểm của người gửi và cộng điểm cho người nhận
    user_data[chat_id][sender_username]["points"] -= points_to_send
    user_data[chat_id][recipient_username]["points"] += points_to_send
    save_user_points(user_data)

    # Tải lại dữ liệu để đảm bảo rằng chúng ta đang làm việc với dữ liệu mới nhất
    updated_user_data = load_user_points()
    sender_points = updated_user_data[chat_id][sender_username]["points"]
    recipient_points = updated_user_data[chat_id][recipient_username]["points"]

    await update.message.reply_html(
        f"<b>{sender_name}</b> vừa gửi <b>{points_to_send} điểm</b> cho <b>@{recipient_username}</b> thành công!\n"
        f"Số điểm hiện tại của <b>{sender_name}</b>: {sender_points}\n"
        f"Số điểm hiện tại của <b>@{recipient_username}</b>: {recipient_points}"
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kiểm tra xem lệnh có được gửi trong tin nhắn riêng không
    if update.message.chat.type != 'private':
        await update.message.reply_text("Vui lòng sử dụng lệnh này trong tin nhắn riêng với bot.")
        return

    user = update.effective_user
    await update.message.reply_text(f"ID của bạn là: {user.id}")
    
async def danhsachgiauco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    user_data = load_user_points()
    
    if chat_id not in user_data:
        await update.message.reply_text("Chưa có dữ liệu về nhóm này.")
        return

    # Sắp xếp người dùng theo điểm
    sorted_users = sorted(user_data[chat_id].items(), key=lambda x: x[1]['points'], reverse=True)
    total_users = len(sorted_users)

    # Hiển thị 20 người đầu tiên
    content = f"DANH SÁCH GIÀU CÓ TRONG NHÓM\n------—--—TỔNG: <b>{total_users:,}</b> NGƯỜI------—--—\n\n"
    for i, (username, data) in enumerate(sorted_users[:20], 1):
        name = data.get('name', username)
        if len(name) > 15:
            name = name[:12] + "..."
        content += f"{i}. @{name} - Số Money có: {data['points']:,}\n"

    # Tạo nút "Xem thêm" nếu có nhiều hơn 20 người
    keyboard = []
    if total_users > 20:
        keyboard.append([InlineKeyboardButton("Xem thêm", callback_data="next_page_1")])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_html(content, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = str(query.message.chat_id)
    user_data = load_user_points()
    sorted_users = sorted(user_data[chat_id].items(), key=lambda x: x[1]['points'], reverse=True)
    total_users = len(sorted_users)

    page = int(query.data.split('_')[-1])
    start = page * 20
    end = start + 20

    content = f"DANH SÁCH GIÀU CÓ TRONG NHÓM (Trang {page + 1})\n-------TỔNG: <b>{total_users:,}</b> NGƯỜI-------\n\n"
    for i, (username, data) in enumerate(sorted_users[start:end], start + 1):
        name = data.get('name', username)
        if len(name) > 15:
            name = name[:12] + "..."
        content += f"{i}. {name} - Số Money có: {data['points']:,}\n"

    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton("« Trước", callback_data=f"next_page_{page-1}"))
    if end < total_users:
        keyboard.append(InlineKeyboardButton("Sau »", callback_data=f"next_page_{page+1}"))

    reply_markup = InlineKeyboardMarkup([keyboard]) if keyboard else None
    await query.edit_message_text(content, reply_markup=reply_markup, parse_mode='HTML')