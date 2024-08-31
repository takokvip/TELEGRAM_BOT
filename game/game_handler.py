import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
import random
import logging
import os
from telegram import InputFile, Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

from handlers.checkin_handler import load_user_points, save_user_points

game_state = {}

async def user_has_interacted_before(user_id, bot):
    try:
        chat_member = await bot.get_chat_member(chat_id=user_id, user_id=user_id)
        return chat_member.status != "left"
    except:
        return False
    
async def start_ontuti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Kiểm tra xem người dùng đã tương tác với bot chưa
    if not await user_has_interacted_before(user.id, context.bot):
        await context.bot.send_message(chat_id=user.id, text="Vui lòng nhắn tin bất kỳ cho bot trước khi bắt đầu trò chơi.")
        return
    
    logger.debug(f"Attempting to start Oẳn Tù Tì game in chat {chat_id}")

    if chat_id in game_state and game_state[chat_id].get("game_started", False):
        if user.id in [p.id for p in game_state[chat_id]["players"]]:
            await update.message.reply_text("Bạn đã tham gia trận chiến rồi, vui lòng đợi đối thủ tham gia.")
        else:
            await update.message.reply_text("Đã có một người tham gia rồi, mời bạn bấm /joinontuti để tham gia.")
        return

    logger.debug(f"Starting Oẳn Tù Tì game in chat {chat_id}")
    game_state[chat_id] = {
        "game_started": True,
        "players": [user],
        "choices": {},
        "messages": []
    }

    # Gửi thông báo chung vào group
    announcement = await update.message.reply_text(
        "Làm tí Oẳn Tù Tì ai thua mời nước cả tổ nhé anh em!\n/joinontuti"
    )
    game_state[chat_id]["messages"].append(announcement.message_id)

    image_path = os.path.join(os.path.dirname(__file__), 'solo.jpg')
    
    if os.path.exists(image_path):
        caption = f"Sân chơi đã có 1 người tham gia:\n<b>{user.full_name}</b>\nvs\n......."
        with open(image_path, 'rb') as photo:
            message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=InputFile(photo),
                caption=caption,
                parse_mode='HTML'
            )
    else:
        logger.error(f"Image file not found: {image_path}")
        message = await update.message.reply_html(
            f"Sân chơi đã có 1 người tham gia:\n\n<b>{user.full_name}</b>\nvs\n......."
        )
    
    game_state[chat_id]["messages"].append(message.message_id)

    # Đặt timer 60 giây để hủy game nếu không đủ người chơi
    context.job_queue.run_once(cancel_game_timeout, 60, chat_id=chat_id, name=f'cancel_game_{chat_id}')

async def join_ontuti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Kiểm tra xem người dùng đã tương tác với bot chưa
    if not await user_has_interacted_before(user.id, context.bot):
        await context.bot.send_message(chat_id=user.id, text="Vui lòng nhắn tin bất kỳ cho bot trước khi tham gia trò chơi.")
        return
    
    logger.debug(f"User {user.id} trying to join game in chat {chat_id}")
    
    if chat_id not in game_state or not game_state[chat_id].get("game_started", False):
        await update.message.reply_text("Hiện tại chưa có game nào được tạo. Hãy sử dụng lệnh /ontuti để tạo game mới.")
        return

    if user.id in [p.id for p in game_state[chat_id]["players"]]:
        await update.message.reply_text("Bạn đã tham gia trận chiến rồi, vui lòng đợi đối thủ tham gia.")
        return

    if len(game_state[chat_id]["players"]) >= 2:
        await update.message.reply_text("Không thể tham gia game lúc này. Game đã đủ người chơi.")
        return

    game_state[chat_id]["players"].append(user)
    logger.debug(f"Game state after join: {game_state[chat_id]}")
    players = game_state[chat_id]["players"]

    # Hủy timer hủy game vì đã đủ người chơi
    current_jobs = context.job_queue.get_jobs_by_name(f'cancel_game_{chat_id}')
    for job in current_jobs:
        job.schedule_removal()

    for message_id in game_state[chat_id].get("messages", []):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
    
    game_state[chat_id]["messages"] = []

    message = await update.message.reply_html(
        f"Sân chơi đã có 2 người tham gia:\n\n<b>{players[0].full_name}</b>\nvs\n<b>{players[1].full_name}</b>\n\nTrò chơi sẽ bắt đầu trong 5s nữa"
    )
    game_state[chat_id]["messages"].append(message.message_id)
    await asyncio.sleep(5)
    await start_game(update, context)

async def cancel_game_timeout(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id

    if chat_id in game_state and len(game_state[chat_id]["players"]) < 2:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Không đủ 2 người chơi, trận đấu không thể bắt đầu. Vui lòng bắt đầu lại để tìm đối thủ!"
        )
        # Xóa các tin nhắn cũ
        for message_id in game_state[chat_id].get("messages", []):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
        
        # Xóa trạng thái game
        del game_state[chat_id]
        
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    players = game_state[chat_id]["players"]
    logger.debug(f"Starting game for chat {chat_id} with players {[p.id for p in players]}")

    keyboard = [
        [
            InlineKeyboardButton("Kéo ✌️", callback_data=f"choice:keo:{chat_id}"),
            InlineKeyboardButton("Lá 🖐️", callback_data=f"choice:la:{chat_id}"),
            InlineKeyboardButton("Búa 👊", callback_data=f"choice:bua:{chat_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for player in players:
        await context.bot.send_message(
            chat_id=player.id,
            text="Mời bạn chọn phương thức kết liễu kẻ địch.\n\nBạn có 5 giây để chọn",
            reply_markup=reply_markup
        )

    # Đặt timer để kết thúc game sau 5 giây
    context.job_queue.run_once(end_game_callback, 5, chat_id=chat_id, name=f'end_game_{chat_id}')

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data.split(':')
    if len(data) != 3 or data[0] != 'choice':
        logger.warning(f"Invalid callback data: {query.data}")
        return

    choice, chat_id = data[1], int(data[2])
    logger.debug(f"Handling choice '{choice}' from user {user.id} in chat {chat_id}")

    if chat_id not in game_state or user.id not in [p.id for p in game_state[chat_id]["players"]]:
        logger.warning(f"Invalid choice from user {user.id} in chat {chat_id}")
        return

    game_state[chat_id]["choices"][user.id] = choice
    await query.edit_message_text(f"Bạn đã chọn: {format_choice(choice)}")

    logger.debug(f"Current game state: {game_state[chat_id]}")

    if len(game_state[chat_id]["choices"]) == 2:
        # Hủy timer nếu cả hai người chơi đã chọn
        current_jobs = context.job_queue.get_jobs_by_name(f'end_game_{chat_id}')
        for job in current_jobs:
            job.schedule_removal()
        await end_game(update, context, chat_id)

async def end_game_callback(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await end_game(None, context, job.chat_id)

def format_choice(choice):
    choice_map = {
        "keo": "Kéo ✌️",
        "la": "Lá 🖐️",
        "bua": "Búa 👊"
    }
    return choice_map.get(choice, choice)

async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    await asyncio.sleep(1)
    logger.debug(f"Ending game for chat {chat_id}")
    players = game_state[chat_id]["players"]
    choices = game_state[chat_id]["choices"]

    timeout_players = [p for p in players if p.id not in choices]
    if timeout_players:
        # Có ít nhất một người chơi không chọn trong thời gian quy định
        for player in timeout_players:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Thành viên <b>{player.full_name}</b> đã bỏ chạy vì quá sợ hãi",
                parse_mode='HTML'
            )
        del game_state[chat_id]
        return

    player1, player2 = players
    choice1, choice2 = choices[player1.id], choices[player2.id]

    winner = determine_winner(choice1, choice2)

    user_data = load_user_points()
    chat_id_str = str(chat_id)

    result = "Trận đấu đã kết thúc\n\n"
    result += f"<b>{player1.full_name}</b> chọn {format_choice(choice1)}\n"
    result += f"<b>{player2.full_name}</b> chọn {format_choice(choice2)}\n\n"

    if winner == 0:
        result += "Kết quả: Hòa! Không ai thắng cả.\nLàm lại ván nữa cho nguy nga nhé /ontuti"
    elif winner == 1:
        result += f"Chúc mừng bạn <b>{player1.full_name}</b> đã dành chiến thắng."
        if chat_id_str in user_data and player1.username in user_data[chat_id_str]:
            user_data[chat_id_str][player1.username]["points"] += 50
    else:
        result += f"Chúc mừng bạn <b>{player2.full_name}</b> đã dành chiến thắng."
        if chat_id_str in user_data and player2.username in user_data[chat_id_str]:
            user_data[chat_id_str][player2.username]["points"] += 50

    save_user_points(user_data)

    await context.bot.send_message(chat_id=chat_id, text=result, parse_mode='HTML')
    del game_state[chat_id]
    
def determine_winner(choice1, choice2):
    if choice1 == choice2:
        return 0
    elif (choice1 == "keo" and choice2 == "la") or \
         (choice1 == "la" and choice2 == "bua") or \
         (choice1 == "bua" and choice2 == "keo"):
        return 1
    else:
        return 2

# Hàm để đăng ký các handlers cho trò chơi Oẳn Tù Tì
def register_handlers(application):
    application.add_handler(CommandHandler("ontuti", start_ontuti))
    application.add_handler(CommandHandler("joinontuti", join_ontuti))
    application.add_handler(CallbackQueryHandler(handle_choice))