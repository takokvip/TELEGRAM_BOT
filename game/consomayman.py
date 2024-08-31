import asyncio
import random
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import logging

logger = logging.getLogger(__name__)

game_state = {}

async def start_consomayman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in game_state and game_state[chat_id].get("game_started", False):
        await update.message.reply_html("Trò chơi đã được bắt đầu, vui lòng chờ đến khi trò chơi kết thúc để bắt đầu trò chơi mới.")
        return

    game_state[chat_id] = {
        "game_started": True,
        "players": {},
        "messages": []
    }

    announcement = await update.message.reply_html(
        "Xin mời tất cả thành viên trong nhóm chọn 1 con số đảm bảo không trùng với thành viên nào vì phần thưởng không thể chia đôi!\n"
        "Cách thức tham gia:\n"
        "/chon <code>{số}</code> mà bạn thích <code>(ví dụ: /chon 99)</code> game sẽ start sau 120s."
    )
    game_state[chat_id]["messages"].append(announcement.message_id)

    # Đặt timer 120 giây để kết thúc giai đoạn chọn số
    context.job_queue.run_once(end_selection, 30, chat_id=chat_id, name=f'end_selection_{chat_id}')

async def chon_so(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in game_state or not game_state[chat_id].get("game_started", False):
        await update.message.reply_text("Hiện tại chưa có game nào được tạo. Hãy sử dụng lệnh /consomayman để tạo game mới.")
        return

    if game_state[chat_id].get("selection_ended", False):
        await update.message.reply_html("Thời gian chọn số đã hết. Vui lòng quay lại sau.")
        return

    if len(context.args) != 1 or not context.args[0].isdigit() or not (0 <= int(context.args[0]) <= 99):
        # Nếu không có số được cung cấp, BOT sẽ chọn ngẫu nhiên một số từ 00-99 đảm bảo không trùng với bất kỳ ai
        available_numbers = set(range(100)) - set(game_state[chat_id]["players"].values())
        if not available_numbers:
            await update.message.reply_html("Không còn số nào khả dụng để chọn.")
            return
        chosen_number = random.choice(list(available_numbers))
        await update.message.reply_html(f"Bạn không cung cấp số, BOT đã chọn ngẫu nhiên số <b>{chosen_number}</b> cho bạn.")
    else:
        chosen_number = int(context.args[0])
        if chosen_number in game_state[chat_id]["players"].values():
            await update.message.reply_html(f"Số <b>{chosen_number}</b> đã được chọn bởi người khác. Vui lòng chọn số khác.")
            return

    if user.id in game_state[chat_id]["players"]:
        await update.message.reply_html(f"Bạn đã chọn số <b>{game_state[chat_id]['players'][user.id]}</b>. Bạn không thể thay đổi số của mình.")
        return

    game_state[chat_id]["players"][user.id] = chosen_number
    await update.message.reply_html(f"Bạn đã chọn số <b>{chosen_number}</b>.")

async def end_selection(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id

    if chat_id not in game_state or not game_state[chat_id]["players"]:
        await context.bot.send_message(chat_id=chat_id, text="Không có người chơi nào tham gia. Trò chơi kết thúc.")
        del game_state[chat_id]
        return

    players = game_state[chat_id]["players"]
    total_players = len(players)
    result_message = f"CHỐT DANH SÁCH THAM GIA QUAY SỐ MAY MẮN\n--------Tổng số người tham gia là: <b>{total_players} 👨‍👩‍👦‍👦</b>--------\n\n"

    for index, (user_id, number) in enumerate(players.items()):
        user = await context.bot.get_chat(user_id)
        result_message += f"{index + 1}. <b>{user.full_name}</b> - chọn <b>{number}</b>\n"

    result_message += "\n15s nữa BOT sẽ random con số may mắn hôm nay để nhận thưởng!"
    await context.bot.send_message(chat_id=chat_id, text=result_message, parse_mode='HTML')

    # Đặt cờ để đánh dấu rằng giai đoạn chọn số đã kết thúc
    game_state[chat_id]["selection_ended"] = True

    # Đặt timer 15 giây để chọn con số may mắn
    context.job_queue.run_once(select_lucky_number, 15, chat_id=chat_id, name=f'select_lucky_number_{chat_id}')

async def select_lucky_number(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id

    lucky_number = random.randint(0, 99)
    players = game_state[chat_id]["players"]

    closest_user = None
    closest_diff = 100  # Số lớn nhất có thể để tìm khoảng cách gần nhất

    for user_id, chosen_number in players.items():
        diff = abs(chosen_number - lucky_number)
        if diff < closest_diff:
            closest_diff = diff
            closest_user = user_id

    closest_user_chat = await context.bot.get_chat(closest_user)
    closest_user_name = f"<b>{closest_user_chat.full_name}</b> (@{closest_user_chat.username})" if closest_user_chat.username else f"<b>{closest_user_chat.full_name}</b>"

    if closest_diff == 0:
        result_message = f"Con số may mắn hôm nay là: <b>{lucky_number}</b>\nXin chúc mừng {closest_user_name} với số chọn là: <b>{lucky_number}</b> đã trúng thưởng!"
    else:
        result_message = f"Con số may mắn hôm nay là: <b>{lucky_number}</b>\nKhông có ai chọn đúng số may mắn, nhưng {closest_user_name} đã chọn số gần đúng nhất và chiến thắng!"

    await context.bot.send_message(chat_id=chat_id, text=result_message, parse_mode='HTML')

    # Kết thúc trò chơi và reset trạng thái
    del game_state[chat_id]

def register_handlers(application):
    application.add_handler(CommandHandler("consomayman", start_consomayman))
    application.add_handler(CommandHandler("chon", chon_so))
