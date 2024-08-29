import logging
from telegram import Update, ChatMemberUpdated
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ChatMemberHandler, ContextTypes
from config.settings import TOKEN, CHECKIN_KEYWORD
from handlers.checkin_handler import checkin, checkdiem, sendmoney, myid, danhsachgiauco, button_callback
from handlers.filter_handler import filter_message
from telegram.constants import ChatMemberStatus

# Thiết lập logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'  # Lưu log vào file
)
logger = logging.getLogger(__name__)

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    new_members = update.message.new_chat_members
    for member in new_members:
        if member.is_bot:
            continue

        user_name = member.full_name
        user_username = member.username

        if user_username:
            user_mention = f"<b>{user_name} (@{user_username})</b>"
        else:
            user_mention = f"<b>{user_name}</b>"

        chat_title = update.message.chat.title

        welcome_message = (
            f"Chào mừng {user_mention} mới tham gia nhóm <b>{chat_title}</b>!\n"
            "Để sử dụng chức năng của BOT vui lòng chat <b>/rule</b> để được hướng dẫn.\n"
            "Chúc bạn có những giây phút thật vui vẻ khi tham gia nhóm."
        )

        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=welcome_message,
            parse_mode="HTML"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        user_name = update.message.from_user.full_name
        await update.message.reply_text(f"Chào mừng bạn đến với bot, {user_name}!")

async def checkin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        user_name = update.message.from_user.full_name
        logger.info(f"Received '{CHECKIN_KEYWORD}' from {user_name} in chat {update.message.chat_id}")
        await checkin(update, context)

async def checkdiem_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        user_name = update.message.from_user.full_name
        logger.info(f"Received '/checkdiem' from {user_name} in chat {update.message.chat_id}")
        await checkdiem(update, context)

async def sendmoney_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        user_name = update.message.from_user.full_name
        logger.info(f"Received '/sendmoney' from {user_name} in chat {update.message.chat_id}")
        await sendmoney(update, context)

async def filter_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        user_name = update.message.from_user.full_name
        logger.info(f"Message received in group from {user_name}")
        await filter_message(update, context)

async def myid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await myid(update, context)

async def rule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rule_message = (
        "Dưới đây là cấu trúc và cách hoạt động của nhóm:\n\n"
        "<b>okpay</b> : Giúp bạn điểm danh tích tiền mỗi ngày.\n"
        "<b>/checkdiem</b> : Giúp bạn kiểm tra số tiền mà bạn có.\n"
        "<b>/sendmoney @username {số tiền}</b> : Giúp bạn gửi tiền cho người khác.\n"
        "<b>/myid</b> : Giúp bạn lấy ID của chính mình (nhắn tin riêng cho BOT).\n"
        "<b>/danhsachgiauco</b> : Giúp bạn xem danh sách những người có nhiều tiền nhất trong nhóm.\n"
    )

    await update.message.reply_text(rule_message, parse_mode="HTML")
    
def main():
    # Khởi tạo ứng dụng bot
    application = Application.builder().token(TOKEN).build()

    # Thêm handler để chào mừng thành viên mới
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # Thêm các handler vào ứng dụng
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("checkdiem", checkdiem_handler))
    application.add_handler(CommandHandler("sendmoney", sendmoney_handler))
    application.add_handler(CommandHandler("myid", myid_handler))
    application.add_handler(CommandHandler("danhsachgiauco", danhsachgiauco))
    application.add_handler(CommandHandler("rule", rule))
    application.add_handler(MessageHandler(filters.Regex(f'^{CHECKIN_KEYWORD}$'), checkin_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_message_handler))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Chạy bot
    print("Bot is running...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
