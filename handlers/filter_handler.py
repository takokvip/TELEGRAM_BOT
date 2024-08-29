from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config.settings import ADMIN_KEYWORDS, ADMIN_CHAT_ID
import json
import logging
import re

logger = logging.getLogger(__name__)

USER_POINTS_FILE = "user_points.json"
MAX_WARNINGS = 5

def load_user_points():
    try:
        with open(USER_POINTS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_points(data):
    with open(USER_POINTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def is_forbidden_message(message_text, forbidden_keywords):
    # Sử dụng \b để khớp toàn bộ từ, đồng thời xử lý các trường hợp nối từ khóa với dấu câu
    for keyword in forbidden_keywords:
        # Cập nhật pattern để chỉ khớp từ khóa khi nó đứng độc lập hoặc giữa các dấu câu
        pattern = r'(?<!\w)' + re.escape(keyword) + r'(?!\w)'
        if re.search(pattern, message_text, re.IGNORECASE):
            return True
    return False

async def filter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = str(update.message.chat_id)
    username = update.message.from_user.username
    full_name = update.message.from_user.full_name
    message_text = update.message.text.lower()
    chat_title = update.message.chat.title[:80] if update.message.chat.title else "Unknown Group"

    if not username:
        await update.message.reply_text("Bạn cần đặt username để sử dụng bot trong nhóm này.")
        return

    user_data = load_user_points()

    if chat_id not in user_data:
        user_data[chat_id] = {}

    if username not in user_data[chat_id]:
        user_data[chat_id][username] = {"points": 0, "last_checkin": None, "warnings": 0}

    # Kiểm tra nếu tin nhắn chứa link
    if "http" in message_text or "www" in message_text:
        try:
            await update.message.delete()
            user_mention = f"{full_name} (@{username})"
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Chào bạn <b>{user_mention}</b>, nhóm của chúng ta không cho phép chia sẻ liên kết. "
                     f"Tin nhắn của bạn đã bị xóa và báo cáo đến Admin.",
                parse_mode=ParseMode.HTML
            )
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"Nhóm: <b>{chat_title}</b>\n"
                     f"User: <b>{user_mention}</b>\n"
                     f"Đã chia sẻ link: {update.message.text}",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error deleting message or notifying admin: {e}")
        return

    # Kiểm tra từ khóa cấm
    if is_forbidden_message(message_text, ADMIN_KEYWORDS):
        warnings = user_data[chat_id][username]["warnings"] + 1
        user_data[chat_id][username]["warnings"] = warnings
        save_user_points(user_data)

        remaining_warnings = MAX_WARNINGS - warnings

        user_mention = f"{full_name} (@{username})"

        if warnings >= MAX_WARNINGS:
            try:
                await context.bot.ban_chat_member(chat_id=chat_id, user_id=update.message.from_user.id)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"User <b>{user_mention}</b> đã bị kick khỏi nhóm vì vi phạm nội quy quá <b>{MAX_WARNINGS}</b> lần.",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"User {user_mention} has been kicked from chat {chat_id} due to excessive warnings")
            except Exception as e:
                logger.error(f"Error kicking user: {e}")
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Cảnh báo cho bạn <b>{user_mention}</b>: Vi phạm {warnings}/{MAX_WARNINGS}\n"
                     f"Còn {remaining_warnings} lần cảnh báo nữa sẽ bị kick khỏi nhóm.",
                parse_mode=ParseMode.HTML
            )

        try:
            await update.message.delete()
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    logger.info(f"Processed message from user {full_name} (@{username}) in chat {chat_id}")
