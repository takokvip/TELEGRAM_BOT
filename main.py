import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from config.settings import TOKEN, CHECKIN_KEYWORD
from handlers.checkin_handler import checkin, checkdiem, sendmoney, myid, danhsachgiauco, button_callback
from handlers.filter_handler import filter_message
from game.game_handler import start_ontuti, join_ontuti, handle_choice as handle_ontuti_choice
from game.gametraloicauhoi import start_traloicauhoi, join_traloicauhoi, handle_answer as handle_traloicauhoi_answer
from game.consomayman import register_handlers as register_consomayman_handlers

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

        welcome_message = (
            f"Chào mừng {user_mention} vừa tham gia nhóm!\n"
            "Để sử dụng chức năng của BOT vui lòng chat <b>/rule</b> để được hướng dẫn.\n"
            "Chúc bạn có những giây phút thật vui vẻ khi sinh hoạt trong nhóm."
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
        logger.debug(f"Message content: {update.message.text}")
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
        "<b>okpay</b> : Giúp bạn điểm danh tích điểm mỗi ngày.\n"
        "<b>/checkdiem</b> : Giúp bạn kiểm tra số điểm mà bạn có.\n"
        "<b>/sendmoney @username {số điểm}</b> : Giúp bạn gửi điểm cho người khác.\n"
        "<b>/myid</b> : Giúp bạn lấy ID của chính mình (nhắn tin riêng cho BOT).\n"
        "<b>/danhsachgiauco</b> : Giúp bạn xem danh sách những người có nhiều điểm nhất trong nhóm.\n"
        "<b>/ontuti</b> : Bắt đầu trò chơi Oẳn Tù Tì.\n"
        "<b>/traloicauhoi</b> : Bắt đầu trò chơi Trả Lời Câu Hỏi.\n"
        "<b>/consomayman</b> : Bắt đầu trò chơi Con Số May Mắn.\n"
    )

    await update.message.reply_text(rule_message, parse_mode="HTML")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if update.effective_message:
        await update.effective_message.reply_text("Đã xảy ra lỗi khi xử lý yêu cầu của bạn.")

def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("choice:"):
        # Xử lý cho trò chơi Oẳn Tù Tì
        return handle_ontuti_choice(update, context)
    elif data.startswith("answer:"):
        # Xử lý cho trò chơi Trả Lời Câu Hỏi
        return handle_traloicauhoi_answer(update, context)
    else:
        # Xử lý cho các callback khác (nếu có)
        return button_callback(update, context)

def main():
    # Khởi tạo ứng dụng bot
    application = Application.builder().token(TOKEN).build()

    # Thêm các handler vào ứng dụng
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("checkdiem", checkdiem_handler))
    application.add_handler(CommandHandler("sendmoney", sendmoney_handler))
    application.add_handler(CommandHandler("myid", myid_handler))
    application.add_handler(CommandHandler("danhsachgiauco", danhsachgiauco))
    application.add_handler(CommandHandler("rule", rule))
    application.add_handler(MessageHandler(filters.Regex(f'^{CHECKIN_KEYWORD}$'), checkin_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_message_handler))
    
    # Handlers cho trò chơi Oẳn Tù Tì
    application.add_handler(CommandHandler("ontuti", start_ontuti))
    application.add_handler(CommandHandler("joinontuti", join_ontuti))
    
    # Handlers cho trò chơi Trả Lời Câu Hỏi
    application.add_handler(CommandHandler("traloicauhoi", start_traloicauhoi))
    application.add_handler(CommandHandler("jointraloicauhoi", join_traloicauhoi))
    
    # Đăng ký handlers cho trò chơi Con Số May Mắn
    register_consomayman_handlers(application)
    
    # Handler chung cho tất cả các callback
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    print("Bot is running...")
    
    # Chạy bot
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()