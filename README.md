# Telegram Group Bot

## Giới Thiệu

Bot này được phát triển để quản lý nhóm Telegram của bạn, hỗ trợ các lệnh điểm danh, kiểm tra điểm, gửi điểm, và nhiều chức năng khác. Bot cũng giúp lọc và xóa các tin nhắn không phù hợp dựa trên danh sách từ khóa cấm.

## Chức Năng

### 1. Điểm danh mỗi ngày

- **Lệnh**: `okpay`
- **Mô tả**: Giúp bạn điểm danh và tích lũy điểm mỗi ngày. Mỗi ngày bạn sẽ nhận được số điểm cố định.

### 2. Kiểm tra điểm hiện tại

- **Lệnh**: `/checkdiem`
- **Mô tả**: Giúp bạn kiểm tra số điểm hiện tại mà bạn đang có và số ngày bạn đã điểm danh.

### 3. Gửi điểm cho người dùng khác

- **Lệnh**: `/sendmoney @username {số điểm}`
- **Mô tả**: Cho phép bạn gửi một số điểm nhất định cho người dùng khác. Điểm của bạn sẽ bị trừ đi và được cộng vào tài khoản của người nhận.

### 4. Xem ID của bạn

- **Lệnh**: `/myid`
- **Mô tả**: Giúp bạn kiểm tra ID Telegram của mình.

### 5. Xem danh sách người dùng có điểm cao nhất

- **Lệnh**: `/danhsachgiauco`
- **Mô tả**: Hiển thị danh sách các thành viên có số điểm cao nhất trong nhóm.

### 6. Luật chơi trong nhóm

- **Lệnh**: `/rule`
- **Mô tả**: Hiển thị luật chơi và các lệnh cơ bản của bot để người dùng mới có thể tham gia sử dụng dễ dàng.

## Cách Cấu Hình

### 1. Tệp `config/settings.py`

Tệp này chứa các cấu hình chính của bot, bao gồm:

- **TOKEN**: Token của bot Telegram, lấy từ BotFather.
- **CHECKIN_KEYWORD**: Từ khóa để thực hiện lệnh điểm danh (ví dụ: `"okpay"`).
- **ADMIN_KEYWORDS**: Danh sách các từ khóa cấm mà bot sẽ xóa nếu phát hiện trong tin nhắn.
- **ADMIN_CHAT_ID**: ID của Admin để nhận thông báo khi có sự kiện vi phạm.

### 2. Tệp `user_points.json`

Tệp này lưu trữ thông tin về điểm số, số ngày điểm danh, và số lần cảnh báo của mỗi người dùng trong nhóm.

- **points**: Số điểm hiện tại của người dùng.
- **last_checkin**: Ngày gần nhất người dùng điểm danh.
- **warnings**: Số lần cảnh báo người dùng đã nhận.

### 3. Tệp `bot.log`

Tệp này lưu lại log hoạt động của bot để bạn có thể theo dõi quá trình chạy bot và phát hiện lỗi (nếu có).

## Cài Đặt

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
