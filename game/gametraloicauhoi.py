import asyncio
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
import logging

logger = logging.getLogger(__name__)

from handlers.checkin_handler import load_user_points, save_user_points

game_state = {}

# Danh sách câu hỏi
QUESTIONS = [
        {"question": "Thành phố nào có cảng biển lớn nhất Việt Nam?", "options": ["Hải Phòng", "Hồ Chí Minh", "Đà Nẵng", "Quy Nhơn"], "correct": "Hải Phòng"},
        {"question": "Thành phố nào là thủ đô của Pháp?", "options": ["Paris", "Marseille", "Lyon", "Nice"], "correct": "Paris"},
        {"question": "Tỉnh nào ở Việt Nam nổi tiếng với đặc sản phở?", "options": ["Hà Nội", "Nam Định", "Hà Giang", "Lào Cai"], "correct": "Nam Định"},
        {"question": "Ngày quốc tế lao động là ngày nào?", "options": ["1/5", "8/3", "2/9", "20/11"], "correct": "1/5"},
        {"question": "Thành phố nào là thủ đô của Nhật Bản?", "options": ["Tokyo", "Osaka", "Kyoto", "Nagoya"], "correct": "Tokyo"},
        {"question": "Ai là người phát minh ra bóng đèn điện?", "options": ["Thomas Edison", "Albert Einstein", "Nikola Tesla", "Isaac Newton"], "correct": "Thomas Edison"},
        {"question": "Đại dương nào bao phủ diện tích lớn nhất trên Trái Đất?", "options": ["Thái Bình Dương", "Đại Tây Dương", "Ấn Độ Dương", "Bắc Băng Dương"], "correct": "Thái Bình Dương"},
        {"question": "Loại hoa nào thường được tặng vào ngày Tình Yêu?", "options": ["Hoa Hồng", "Hoa Lan", "Hoa Cẩm Chướng", "Hoa Tulip"], "correct": "Hoa Hồng"},
        {"question": "Tác giả của cuốn tiểu thuyết 'Chiến tranh và hòa bình' là ai?", "options": ["Leo Tolstoy", "F. Scott Fitzgerald", "Ernest Hemingway", "Mark Twain"], "correct": "Leo Tolstoy"},
        {"question": "Quốc gia nào là nơi sinh của Đức Phật?", "options": ["Nepal", "Ấn Độ", "Sri Lanka", "Thái Lan"], "correct": "Nepal"},
        {"question": "Việt Nam gia nhập Liên Hiệp Quốc vào năm nào?", "options": ["1977", "1975", "1986", "1980"], "correct": "1977"},
        {"question": "Tỉnh nào có diện tích lớn nhất Việt Nam?", "options": ["Nghệ An", "Thanh Hóa", "Sơn La", "Hà Giang"], "correct": "Nghệ An"},
        {"question": "Quốc gia nào là quê hương của môn bóng đá?", "options": ["Anh", "Brazil", "Đức", "Ý"], "correct": "Anh"},
        {"question": "Châu lục nào có diện tích nhỏ nhất?", "options": ["Châu Úc", "Châu Âu", "Châu Nam Cực", "Châu Phi"], "correct": "Châu Úc"},
        {"question": "Thành phố nào là thủ đô của Đức?", "options": ["Berlin", "Frankfurt", "Munich", "Hamburg"], "correct": "Berlin"},
        {"question": "Môn thể thao nào là môn thể thao vua?", "options": ["Bóng đá", "Bóng rổ", "Quần vợt", "Bóng chày"], "correct": "Bóng đá"},
        {"question": "Quốc gia nào có đường bờ biển dài nhất thế giới?", "options": ["Canada", "Australia", "Indonesia", "Brazil"], "correct": "Canada"},
        {"question": "Đại lục nào có diện tích lớn nhất?", "options": ["Châu Á", "Châu Phi", "Châu Âu", "Châu Mỹ"], "correct": "Châu Á"},
        {"question": "Món ăn nào là đặc sản của miền Nam Việt Nam?", "options": ["Hủ tiếu", "Phở", "Bún bò Huế", "Bánh cuốn"], "correct": "Hủ tiếu"},
        {"question": "Loại nhạc cụ nào phổ biến nhất trên thế giới?", "options": ["Đàn guitar", "Đàn piano", "Sáo", "Trống"], "correct": "Đàn guitar"},
        {"question": "Ai là người lãnh đạo cuộc Cách mạng tháng Tám năm 1945 ở Việt Nam?", "options": ["Hồ Chí Minh", "Nguyễn Ái Quốc", "Trường Chinh", "Phạm Văn Đồng"], "correct": "Hồ Chí Minh"},
        {"question": "Ai là nhà khoa học đã phát minh ra bóng đèn điện?", "options": ["Thomas Edison", "Isaac Newton", "Albert Einstein", "Galileo Galilei"], "correct": "Thomas Edison"},
        {"question": "Quốc gia nào nổi tiếng với điệu nhảy Flamenco?", "options": ["Tây Ban Nha", "Pháp", "Italy", "Bồ Đào Nha"], "correct": "Tây Ban Nha"},
        {"question": "Bản giao hưởng 'Khiêu vũ với bầy sói' do ai sáng tác?", "options": ["John Barry", "Hans Zimmer", "John Williams", "James Horner"], "correct": "John Barry"},
        {"question": "Ai là vị vua đầu tiên của nước Việt Nam?", "options": ["Hùng Vương", "Lý Thái Tổ", "Lê Lợi", "Trần Nhân Tông"], "correct": "Hùng Vương"},
        {"question": "Loại trái cây nào được gọi là 'vua của các loại trái cây'?", "options": ["Sầu riêng", "Xoài", "Dừa", "Bưởi"], "correct": "Sầu riêng"},
        {"question": "Ai là tác giả của tác phẩm 'Truyện Kiều'?", "options": ["Nguyễn Du", "Nguyễn Trãi", "Hồ Xuân Hương", "Nguyễn Khuyến"], "correct": "Nguyễn Du"},
        {"question": "Ngày nhà giáo Việt Nam là ngày nào?", "options": ["20/11", "15/11", "5/10", "19/5"], "correct": "20/11"},
        {"question": "Thủ đô của nước Anh là gì?", "options": ["London", "Manchester", "Liverpool", "Birmingham"], "correct": "London"},
        {"question": "Sông nào dài nhất thế giới?", "options": ["Sông Nile", "Sông Amazon", "Sông Mississippi", "Sông Dương Tử"], "correct": "Sông Nile"},
        {"question": "Quốc gia nào nổi tiếng với kim tự tháp?", "options": ["Ai Cập", "Mexico", "Peru", "Trung Quốc"], "correct": "Ai Cập"},
        {"question": "Thực vật nào được biết đến là loài có hoa lớn nhất thế giới?", "options": ["Hoa Titan Arum", "Hoa Sen", "Hoa Hướng Dương", "Hoa Đào"], "correct": "Hoa Titan Arum"},
        {"question": "Việt Nam gia nhập WTO vào năm nào?", "options": ["2007", "2005", "2003", "2001"], "correct": "2007"},
        {"question": "Quốc gia nào là nơi tổ chức Thế vận hội mùa đông 2022?", "options": ["Trung Quốc", "Nhật Bản", "Hàn Quốc", "Nga"], "correct": "Trung Quốc"},
        {"question": "Bản Tuyên ngôn độc lập của Việt Nam được công bố vào ngày nào?", "options": ["2/9/1945", "1/5/1945", "19/8/1945", "20/11/1945"], "correct": "2/9/1945"},
        {"question": "Chữ cái nào đứng đầu trong bảng chữ cái tiếng Anh?", "options": ["A", "B", "C", "D"], "correct": "A"},
        {"question": "Thành phố nào là thủ đô của nước Nga?", "options": ["Moscow", "Saint Petersburg", "Vladivostok", "Sochi"], "correct": "Moscow"},
        {"question": "Nguyên tố hóa học nào có ký hiệu là Fe?", "options": ["Sắt", "Vàng", "Bạc", "Đồng"], "correct": "Sắt"},
        {"question": "Thành phố nào có cảng biển lớn nhất Việt Nam?", "options": ["Hải Phòng", "Hồ Chí Minh", "Đà Nẵng", "Quy Nhơn"], "correct": "Hải Phòng"},
        {"question": "Loài vật nào được biết đến là loài có trí nhớ tốt nhất?", "options": ["Voi", "Khỉ", "Dolphin", "Chó"], "correct": "Voi"},
        {"question": "Quốc gia nào có tên gọi là 'Đất nước của những chú chuột túi'?", "options": ["Australia", "New Zealand", "Canada", "Nam Phi"], "correct": "Australia"},
        {"question": "Đỉnh núi cao nhất Việt Nam là gì?", "options": ["Fansipan", "Phu Si Lung", "Pu Ta Leng", "Ngọc Linh"], "correct": "Fansipan"},
        {"question": "Việt Nam có bao nhiêu tỉnh thành?", "options": ["63", "64", "62", "60"], "correct": "63"},
        {"question": "Thành phố nào có dân số đông nhất thế giới?", "options": ["Tokyo", "New York", "Thượng Hải", "Mumbai"], "correct": "Tokyo"},
        {"question": "Ai là tổng thống Mỹ vào thời điểm chiến tranh Việt Nam kết thúc?", "options": ["Gerald Ford", "Richard Nixon", "Lyndon B. Johnson", "John F. Kennedy"], "correct": "Gerald Ford"},
        {"question": "Sông nào dài nhất thế giới?", "options": ["Sông Nile", "Sông Amazon", "Sông Mississippi", "Sông Dương Tử"], "correct": "Sông Nile"},
        {"question": "Ai là người sáng lập ra Facebook?", "options": ["Mark Zuckerberg", "Bill Gates", "Steve Jobs", "Elon Musk"], "correct": "Mark Zuckerberg"},
        {"question": "Ai là người sáng lập ra Microsoft?", "options": ["Bill Gates", "Steve Jobs", "Mark Zuckerberg", "Larry Page"], "correct": "Bill Gates"},
        {"question": "Ai là người sáng lập ra Apple Inc.?", "options": ["Steve Jobs", "Bill Gates", "Elon Musk", "Mark Zuckerberg"], "correct": "Steve Jobs"},
        {"question": "Bản Tuyên ngôn độc lập của Việt Nam được công bố vào ngày nào?", "options": ["2/9/1945", "1/5/1945", "19/8/1945", "20/11/1945"], "correct": "2/9/1945"},
        {"question": "Ngày quốc tế phụ nữ là ngày nào?", "options": ["8/3", "1/5", "20/10", "25/12"], "correct": "8/3"},
        {"question": "Ai là người phát minh ra bóng đèn điện?", "options": ["Thomas Edison", "Albert Einstein", "Nikola Tesla", "Isaac Newton"], "correct": "Thomas Edison"},
        {"question": "Mùa nào được gọi là 'mùa thu vàng'?", "options": ["Mùa thu", "Mùa hè", "Mùa đông", "Mùa xuân"], "correct": "Mùa thu"},
        {"question": "Ai là người lãnh đạo cuộc Cách mạng tháng Tám năm 1945 ở Việt Nam?", "options": ["Hồ Chí Minh", "Nguyễn Ái Quốc", "Trường Chinh", "Phạm Văn Đồng"], "correct": "Hồ Chí Minh"},
        {"question": "Quốc gia nào có nền kinh tế lớn nhất thế giới?", "options": ["Mỹ", "Trung Quốc", "Nhật Bản", "Đức"], "correct": "Mỹ"},
        {"question": "Ai là người sáng lập ra Apple Inc.?", "options": ["Steve Jobs", "Bill Gates", "Elon Musk", "Mark Zuckerberg"], "correct": "Steve Jobs"},
        {"question": "Loại nhạc cụ nào phổ biến nhất trên thế giới?", "options": ["Đàn guitar", "Đàn piano", "Sáo", "Trống"], "correct": "Đàn guitar"},
        {"question": "Quốc gia nào có nền kinh tế phát triển nhanh nhất thế giới?", "options": ["Trung Quốc", "Ấn Độ", "Mỹ", "Brazil"], "correct": "Trung Quốc"},
        {"question": "Loại nước nào chiếm phần lớn bề mặt Trái Đất?", "options": ["Nước biển", "Nước ngọt", "Nước mặn", "Nước băng"], "correct": "Nước biển"},
        {"question": "Ai là người sáng lập ra Microsoft?", "options": ["Bill Gates", "Steve Jobs", "Mark Zuckerberg", "Larry Page"], "correct": "Bill Gates"},
        {"question": "Ngày nào được gọi là Ngày Quốc tế Phụ nữ?", "options": ["8/3", "1/5", "2/9", "20/11"], "correct": "8/3"},
        {"question": "Chất khí nào chiếm phần lớn trong không khí chúng ta hít thở?", "options": ["Nitơ", "Oxi", "Cacbon dioxit", "Hydro"], "correct": "Nitơ"},
        {"question": "Thủ đô của nước Nga là gì?", "options": ["Moscow", "Saint Petersburg", "Vladivostok", "Sochi"], "correct": "Moscow"},
        {"question": "Quốc gia nào nổi tiếng với nền ẩm thực sushi?", "options": ["Nhật Bản", "Trung Quốc", "Hàn Quốc", "Việt Nam"], "correct": "Nhật Bản"},
        {"question": "Mùa nào được gọi là 'mùa thu vàng'?", "options": ["Mùa thu", "Mùa hè", "Mùa đông", "Mùa xuân"], "correct": "Mùa thu"},
        {"question": "Loài vật nào được biết đến là loài có thể sống lâu nhất?", "options": ["Rùa", "Cá voi xanh", "Đại bàng", "Con sứa bất tử"], "correct": "Con sứa bất tử"},
        {"question": "Ai là tổng thống Mỹ đầu tiên bị ám sát?", "options": ["Abraham Lincoln", "John F. Kennedy", "James A. Garfield", "William McKinley"], "correct": "Abraham Lincoln"},
        {"question": "Nhà bác học nào phát hiện ra định luật vạn vật hấp dẫn?", "options": ["Isaac Newton", "Albert Einstein", "Galileo Galilei", "Nikola Tesla"], "correct": "Isaac Newton"},
        {"question": "Bộ phim nào giành giải Oscar cho phim hay nhất năm 2020?", "options": ["Parasite", "1917", "Joker", "Once Upon a Time in Hollywood"], "correct": "Parasite"},
        {"question": "Quốc gia nào có nhiều di sản văn hóa thế giới nhất?", "options": ["Ý", "Trung Quốc", "Mỹ", "Pháp"], "correct": "Ý"},
        {"question": "Thành phố nào được mệnh danh là 'Thành phố ánh sáng'?", "options": ["Paris", "New York", "London", "Tokyo"], "correct": "Paris"},
        {"question": "Sự kiện nào xảy ra vào ngày 11/9/2001?", "options": ["Vụ tấn công khủng bố tại Mỹ", "Vụ đắm tàu Titanic", "Thế chiến thứ hai bắt đầu", "Chương trình Apollo 11"], "correct": "Vụ tấn công khủng bố tại Mỹ"},
        {"question": "Loại thức ăn nào được biết đến là món ăn nhanh phổ biến nhất trên thế giới?", "options": ["Pizza", "Burger", "Sushi", "Taco"], "correct": "Burger"},
        {"question": "Quốc gia nào nổi tiếng với nền văn hóa trà đạo?", "options": ["Nhật Bản", "Trung Quốc", "Ấn Độ", "Hàn Quốc"], "correct": "Nhật Bản"},
        {"question": "Loài hoa nào là biểu tượng của tình yêu?", "options": ["Hoa Hồng", "Hoa Lan", "Hoa Cẩm Chướng", "Hoa Tulip"], "correct": "Hoa Hồng"},
        {"question": "Quốc gia nào là quê hương của môn bóng đá?", "options": ["Anh", "Brazil", "Đức", "Ý"], "correct": "Anh"},
        {"question": "Ngày nào được gọi là Ngày Tình Yêu?", "options": ["14/2", "1/5", "25/12", "31/10"], "correct": "14/2"},
        {"question": "Quốc gia nào nổi tiếng với nền văn hóa trà đạo?", "options": ["Nhật Bản", "Trung Quốc", "Ấn Độ", "Hàn Quốc"], "correct": "Nhật Bản"},
        {"question": "Đơn vị đo chiều dài nào được sử dụng trong hệ mét?", "options": ["Met", "Yard", "Feet", "Inch"], "correct": "Met"},
        {"question": "Loại hoa nào là biểu tượng của tình yêu?", "options": ["Hoa Hồng", "Hoa Lan", "Hoa Cẩm Chướng", "Hoa Tulip"], "correct": "Hoa Hồng"},
        {"question": "Thành phố nào được mệnh danh là 'Thành phố sương mù'?", "options": ["San Francisco", "London", "Paris", "New York"], "correct": "San Francisco"},
        {"question": "Đâu là quốc gia có hệ thống kênh đào nổi tiếng nhất thế giới?", "options": ["Hà Lan", "Venice, Italy", "Dubai, UAE", "Thụy Điển"], "correct": "Venice, Italy"},
        {"question": "Loài chim nào là biểu tượng của hòa bình?", "options": ["Bồ câu", "Đại bàng", "Chim sẻ", "Chim én"], "correct": "Bồ câu"},
        {"question": "Cơ quan nào trong cơ thể người chịu trách nhiệm về hô hấp?", "options": ["Phổi", "Gan", "Thận", "Tim"], "correct": "Phổi"},
        {"question": "Quốc gia nào có nền kinh tế lớn thứ hai thế giới?", "options": ["Trung Quốc", "Nhật Bản", "Đức", "Ấn Độ"], "correct": "Trung Quốc"},
        {"question": "Đơn vị tiền tệ của Việt Nam là gì?", "options": ["Đồng", "Yên", "Nhân dân tệ", "Riel"], "correct": "Đồng"},
        {"question": "Biển lớn nhất thế giới là gì?", "options": ["Thái Bình Dương", "Đại Tây Dương", "Ấn Độ Dương", "Bắc Băng Dương"], "correct": "Thái Bình Dương"},
        {"question": "Ai là người sáng lập ra Facebook?", "options": ["Mark Zuckerberg", "Bill Gates", "Steve Jobs", "Elon Musk"], "correct": "Mark Zuckerberg"},
        {"question": "Môn thể thao nào phổ biến nhất trên thế giới?", "options": ["Bóng đá", "Bóng rổ", "Bóng chày", "Quần vợt"], "correct": "Bóng đá"},
        {"question": "Thế chiến thứ hai kết thúc vào năm nào?", "options": ["1945", "1918", "1939", "1953"], "correct": "1945"},
        {"question": "Thủ đô của nước Anh là gì?", "options": ["London", "Manchester", "Liverpool", "Birmingham"], "correct": "London"},
        {"question": "Ai là người phát minh ra máy bay?", "options": ["Anh em Wright", "Alexander Graham Bell", "Thomas Edison", "Henry Ford"], "correct": "Anh em Wright"},
        {"question": "Quốc gia nào có dân số đông nhất thế giới?", "options": ["Trung Quốc", "Ấn Độ", "Mỹ", "Indonesia"], "correct": "Trung Quốc"},
        {"question": "Việt Nam nằm trong khu vực khí hậu nào?", "options": ["Nhiệt đới", "Ôn đới", "Cận nhiệt đới", "Xích đạo"], "correct": "Nhiệt đới"},
        {"question": "Việt Nam có bao nhiêu đơn vị hành chính?", "options": ["63", "64", "62", "61"], "correct": "63"},
        {"question": "Loại động vật nào được biết đến là loài có trí nhớ tốt nhất?", "options": ["Voi", "Khỉ", "Dolphin", "Chó"], "correct": "Voi"},
        {"question": "Ai là người được biết đến là 'Cha đẻ của máy tính'?", "options": ["Charles Babbage", "Alan Turing", "Thomas Edison", "Nikola Tesla"], "correct": "Charles Babbage"},
        {"question": "Quốc gia nào có tên gọi là 'Đất nước của những chú chuột túi'?", "options": ["Australia", "New Zealand", "Canada", "Nam Phi"], "correct": "Australia"},
        {"question": "Loại nước nào chiếm phần lớn bề mặt Trái Đất?", "options": ["Nước biển", "Nước ngọt", "Nước mặn", "Nước băng"], "correct": "Nước biển"},
        {"question": "Màu sắc nào trên lá cờ của Việt Nam?", "options": ["Đỏ và Vàng", "Đỏ và Trắng", "Xanh và Vàng", "Trắng và Đen"], "correct": "Đỏ và Vàng"},
        {"question": "Quốc gia nào có nền kinh tế lớn thứ hai thế giới?", "options": ["Trung Quốc", "Nhật Bản", "Đức", "Ấn Độ"], "correct": "Trung Quốc"},
        {"question": "Tổng thống đầu tiên của nước Mỹ là ai?", "options": ["George Washington", "Abraham Lincoln", "Thomas Jefferson", "John Adams"], "correct": "George Washington"},
        {"question": "Đơn vị đo nào dùng để đo cường độ dòng điện?", "options": ["Ampere", "Volt", "Watt", "Ohm"], "correct": "Ampere"},
        {"question": "Ai là người phát minh ra máy bay?", "options": ["Anh em Wright", "Alexander Graham Bell", "Thomas Edison", "Henry Ford"], "correct": "Anh em Wright"},
        {"question": "Ngày quốc tế lao động là ngày nào?", "options": ["1/5", "8/3", "2/9", "20/11"], "correct": "1/5"},
        {"question": "Thành phố nào được mệnh danh là 'thành phố ngàn hoa'?", "options": ["Đà Lạt", "Huế", "Hội An", "Nha Trang"], "correct": "Đà Lạt"},
        {"question": "Nhà văn nào viết 'Số đỏ'?", "options": ["Vũ Trọng Phụng", "Nguyễn Tuân", "Nam Cao", "Ngô Tất Tố"], "correct": "Vũ Trọng Phụng"},
        {"question": "Ai là tác giả của 'Lão Hạc'?", "options": ["Nam Cao", "Vũ Trọng Phụng", "Nguyễn Công Hoan", "Ngô Tất Tố"], "correct": "Nam Cao"},
        {"question": "Nhà văn nào viết 'Chí Phèo'?", "options": ["Nam Cao", "Nguyễn Tuân", "Vũ Trọng Phụng", "Ngô Tất Tố"], "correct": "Nam Cao"},
        {"question": "Nhà thơ nào viết 'Truyện Kiều'?", "options": ["Nguyễn Du", "Nguyễn Trãi", "Hồ Xuân Hương", "Tố Hữu"], "correct": "Nguyễn Du"},
        {"question": "Tác phẩm nào thuộc thể loại thơ Đường?", "options": ["Thu Hứng", "Chí Phèo", "Lão Hạc", "Vợ nhặt"], "correct": "Thu Hứng"},
        {"question": "Tác giả của 'Người lái đò sông Đà'?", "options": ["Nguyễn Tuân", "Nguyễn Du", "Nguyễn Trãi", "Nam Cao"], "correct": "Nguyễn Tuân"},
        {"question": "Nguyên tố nào có ký hiệu là Fe?", "options": ["Sắt", "Chì", "Kẽm", "Vàng"], "correct": "Sắt"},
        {"question": "Số Pi xấp xỉ bằng bao nhiêu?", "options": ["3.14", "2.71", "1.61", "3.16"], "correct": "3.14"},
        {"question": "Hệ số góc của đường thẳng y = 3x + 2 là?", "options": ["3", "2", "1", "0"], "correct": "3"},
        {"question": "Số nào là số nguyên tố?", "options": ["7", "8", "9", "10"], "correct": "7"},
        {"question": "Đạo hàm của x^2 là?", "options": ["2x", "x^2", "x", "2"], "correct": "2x"},
        {"question": "Số nào là số chính phương?", "options": ["16", "20", "30", "50"], "correct": "16"},
        {"question": "Đơn vị đo lực là gì?", "options": ["Newton", "Pascal", "Joule", "Watt"], "correct": "Newton"},
        {"question": "Vật liệu nào là chất dẫn điện tốt?", "options": ["Đồng", "Nhựa", "Gỗ", "Thủy tinh"], "correct": "Đồng"},
        {"question": "Định luật nào liên quan đến gia tốc?", "options": ["Định luật II Newton", "Định luật III Newton", "Định luật Ohm", "Định luật Archimedes"], "correct": "Định luật II Newton"},
        {"question": "Nhà toán học nào nổi tiếng với định lý về hình học phẳng?", "options": ["Pythagoras", "Euclid", "Archimedes", "Gauss"], "correct": "Pythagoras"},
        {"question": "Tác giả của 'Cung oán ngâm khúc'?", "options": ["Nguyễn Gia Thiều", "Nguyễn Du", "Nguyễn Đình Chiểu", "Nguyễn Khuyến"], "correct": "Nguyễn Gia Thiều"},
        {"question": "Định luật bảo toàn khối lượng do ai phát hiện?", "options": ["Lavoisier", "Newton", "Einstein", "Boyle"], "correct": "Lavoisier"},
        {"question": "Nguyên tố nào có ký hiệu là Na?", "options": ["Natri", "Nitơ", "Niken", "Neon"], "correct": "Natri"},
        {"question": "Phương trình bậc hai có tối đa bao nhiêu nghiệm?", "options": ["2", "1", "0", "Vô số"], "correct": "2"},
        {"question": "Ai là người phát hiện ra định luật vạn vật hấp dẫn?", "options": ["Newton", "Einstein", "Galileo", "Archimedes"], "correct": "Newton"},
        {"question": "Nhà văn nào viết 'Vợ nhặt'?", "options": ["Kim Lân", "Nam Cao", "Nguyễn Tuân", "Tô Hoài"], "correct": "Kim Lân"},
        {"question": "Câu thơ 'Nước non ngàn dặm ra đi' thuộc về tác giả nào?", "options": ["Tố Hữu", "Hồ Chí Minh", "Xuân Diệu", "Nguyễn Du"], "correct": "Tố Hữu"},
        {"question": "Số Pi là số gì?", "options": ["Vô tỷ", "Nguyên tố", "Nguyên", "Chính phương"], "correct": "Vô tỷ"},
        {"question": "Đơn vị đo công suất là gì?", "options": ["Watt", "Joule", "Newton", "Pascal"], "correct": "Watt"},
        {"question": "Ai là tác giả của 'Đồng chí'?", "options": ["Chính Hữu", "Nguyễn Đình Thi", "Tố Hữu", "Xuân Diệu"], "correct": "Chính Hữu"},
        {"question": "Đơn vị đo áp suất là gì?", "options": ["Pascal", "Joule", "Watt", "Newton"], "correct": "Pascal"},
        {"question": "Định lý Pitago chỉ áp dụng cho loại tam giác nào?", "options": ["Vuông", "Cân", "Đều", "Nhọn"], "correct": "Vuông"},
        {"question": "Tác phẩm 'Tắt đèn' do ai viết?", "options": ["Ngô Tất Tố", "Nam Cao", "Vũ Trọng Phụng", "Nguyễn Tuân"], "correct": "Ngô Tất Tố"},
        {"question": "Số e trong toán học là bao nhiêu?", "options": ["2.71", "3.14", "1.61", "2.17"], "correct": "2.71"},
        {"question": "Nguyên tố nào có ký hiệu là H?", "options": ["Hiđro", "Heli", "Kali", "Canxi"], "correct": "Hiđro"},
        {"question": "Người phát minh ra bóng đèn là ai?", "options": ["Thomas Edison", "Nikola Tesla", "Albert Einstein", "James Watt"], "correct": "Thomas Edison"},
        {"question": "Câu thơ 'Mặt trời chân lý chói qua tim' là của ai?", "options": ["Tố Hữu", "Xuân Diệu", "Huy Cận", "Nguyễn Đình Thi"], "correct": "Tố Hữu"},
        {"question": "Định lý cosin dùng để tính cạnh trong tam giác gì?", "options": ["Bất kỳ", "Vuông", "Cân", "Đều"], "correct": "Bất kỳ"},
        {"question": "Phương trình E = mc^2 là của ai?", "options": ["Einstein", "Newton", "Galileo", "Planck"], "correct": "Einstein"},
        {"question": "Tác giả của 'Đoàn thuyền đánh cá'?", "options": ["Huy Cận", "Xuân Diệu", "Chế Lan Viên", "Tố Hữu"], "correct": "Huy Cận"},
        {"question": "Nguyên tố nào có ký hiệu là C?", "options": ["Cacbon", "Oxi", "Natri", "Kali"], "correct": "Cacbon"},
        {"question": "Phương trình bậc ba có tối đa bao nhiêu nghiệm?", "options": ["3", "2", "1", "Vô số"], "correct": "3"},
        {"question": "Định luật III Newton còn gọi là gì?", "options": ["Định luật phản lực", "Định luật hấp dẫn", "Định luật quán tính", "Định luật gia tốc"], "correct": "Định luật phản lực"},
        {"question": "Số nào là số nguyên tố?", "options": ["13", "15", "21", "25"], "correct": "13"},
        {"question": "Nhà văn nào viết 'Vợ chồng A Phủ'?", "options": ["Tô Hoài", "Kim Lân", "Nguyễn Tuân", "Tố Hữu"], "correct": "Tô Hoài"},
        {"question": "Câu thơ 'Súng bên súng, đầu sát bên đầu' là của ai?", "options": ["Chính Hữu", "Hồ Chí Minh", "Tố Hữu", "Xuân Diệu"], "correct": "Chính Hữu"},
        {"question": "Số nào là số lẻ?", "options": ["7", "8", "12", "16"], "correct": "7"},
        {"question": "Nguyên tố nào có ký hiệu là O?", "options": ["Oxi", "Nitơ", "Hiđro", "Cacbon"], "correct": "Oxi"},
        {"question": "Ai là người phát hiện ra điện từ?", "options": ["Faraday", "Tesla", "Edison", "Newton"], "correct": "Faraday"},
        {"question": "Đơn vị đo nhiệt độ trong hệ SI?", "options": ["Kelvin", "Celsius", "Fahrenheit", "Rankine"], "correct": "Kelvin"},
        {"question": "Người phát hiện ra chu kỳ của các nguyên tố hóa học?", "options": ["Mendeleev", "Newton", "Einstein", "Galileo"], "correct": "Mendeleev"},
        {"question": "Nhà văn nào viết 'Vợ chồng A Phủ'?", "options": ["Tô Hoài", "Nam Cao", "Kim Lân", "Nguyễn Tuân"], "correct": "Tô Hoài"},
        {"question": "Số nào là số chính phương?", "options": ["25", "30", "35", "40"], "correct": "25"},
        {"question": "Đơn vị đo thời gian trong hệ SI là gì?", "options": ["Giây", "Phút", "Giờ", "Ngày"], "correct": "Giây"},
        {"question": "Phương trình bậc hai có tối đa bao nhiêu nghiệm?", "options": ["2", "1", "0", "Vô số"], "correct": "2"},
        {"question": "Nhà văn nào viết 'Vợ nhặt'?", "options": ["Kim Lân", "Ngô Tất Tố", "Nam Cao", "Vũ Trọng Phụng"], "correct": "Kim Lân"},
        {"question": "Tác giả của 'Người lái đò sông Đà'?", "options": ["Nguyễn Tuân", "Nam Cao", "Tô Hoài", "Kim Lân"], "correct": "Nguyễn Tuân"},
        {"question": "Số nào là số nguyên tố?", "options": ["11", "12", "14", "15"], "correct": "11"},
        {"question": "Nguyên tố nào có ký hiệu là Ag?", "options": ["Bạc", "Vàng", "Kẽm", "Chì"], "correct": "Bạc"},
        {"question": "Số nào là số chính phương?", "options": ["36", "38", "40", "42"], "correct": "36"},
        {"question": "Nhà văn nào viết 'Số đỏ'?", "options": ["Vũ Trọng Phụng", "Nguyễn Tuân", "Nam Cao", "Ngô Tất Tố"], "correct": "Vũ Trọng Phụng"},
        {"question": "Số nào là số chẵn?", "options": ["8", "7", "9", "5"], "correct": "8"},
        {"question": "Ai là người phát hiện ra định luật III Newton?", "options": ["Newton", "Einstein", "Faraday", "Galileo"], "correct": "Newton"},
        {"question": "Tác giả của 'Tắt đèn'?", "options": ["Ngô Tất Tố", "Nam Cao", "Nguyễn Tuân", "Kim Lân"], "correct": "Ngô Tất Tố"},
        {"question": "Số nào là số nguyên tố?", "options": ["17", "18", "20", "22"], "correct": "17"},
        {"question": "Nhà văn nào viết 'Lão Hạc'?", "options": ["Nam Cao", "Nguyễn Tuân", "Vũ Trọng Phụng", "Ngô Tất Tố"], "correct": "Nam Cao"},
        {"question": "Nguyên tố nào có ký hiệu là K?", "options": ["Kali", "Hiđro", "Cacbon", "Oxi"], "correct": "Kali"},
        {"question": "Ai là người phát hiện ra vi khuẩn?", "options": ["Louis Pasteur", "Newton", "Einstein", "Mendel"], "correct": "Louis Pasteur"},
        {"question": "Nguyên tố nào có ký hiệu là Mg?", "options": ["Magie", "Mangan", "Magiê", "Molypden"], "correct": "Magie"},
        {"question": "Phương trình bậc hai có tối đa bao nhiêu nghiệm?", "options": ["2", "1", "0", "Vô số"], "correct": "2"},
        {"question": "Số nào là số nguyên tố?", "options": ["19", "21", "23", "25"], "correct": "19"},
        {"question": "Tác giả của 'Chí Phèo'?", "options": ["Nam Cao", "Nguyễn Tuân", "Tô Hoài", "Kim Lân"], "correct": "Nam Cao"},
        {"question": "Nguyên tố nào có ký hiệu là Cu?", "options": ["Đồng", "Chì", "Sắt", "Kẽm"], "correct": "Đồng"},
        {"question": "Số nào là số chẵn?", "options": ["10", "11", "13", "15"], "correct": "10"},
        {"question": "Nhà văn nào viết 'Vợ chồng A Phủ'?", "options": ["Tô Hoài", "Nam Cao", "Kim Lân", "Nguyễn Tuân"], "correct": "Tô Hoài"},
        {"question": "Số nào là số nguyên tố?", "options": ["23", "24", "26", "28"], "correct": "23"},
        {"question": "Nguyên tố nào có ký hiệu là Zn?", "options": ["Kẽm", "Sắt", "Chì", "Đồng"], "correct": "Kẽm"},
        {"question": "Phương trình bậc ba có tối đa bao nhiêu nghiệm?", "options": ["3", "2", "1", "Vô số"], "correct": "3"},
        {"question": "Người phát minh ra động cơ hơi nước?", "options": ["James Watt", "Thomas Edison", "Albert Einstein", "Nikola Tesla"], "correct": "James Watt"},
        {"question": "Số nào là số nguyên tố?", "options": ["29", "30", "32", "34"], "correct": "29"},
        {"question": "Nguyên tố nào có ký hiệu là Al?", "options": ["Nhôm", "Sắt", "Chì", "Đồng"], "correct": "Nhôm"},
        {"question": "Số nào là số chính phương?", "options": ["49", "50", "51", "52"], "correct": "49"},
        {"question": "Ai là tác giả của 'Truyện Kiều'?", "options": ["Nguyễn Du", "Nguyễn Trãi", "Nguyễn Đình Chiểu", "Nguyễn Khuyến"], "correct": "Nguyễn Du"},
        {"question": "Nguyên tố nào có ký hiệu là Pb?", "options": ["Chì", "Sắt", "Kẽm", "Đồng"], "correct": "Chì"},
        {"question": "Số nào là số nguyên tố?", "options": ["31", "33", "35", "37"], "correct": "31"},
        {"question": "Nguyên tố nào có ký hiệu là Au?", "options": ["Vàng", "Bạc", "Đồng", "Chì"], "correct": "Vàng"},
        {"question": "Phương trình bậc hai có tối đa bao nhiêu nghiệm?", "options": ["2", "1", "0", "Vô số"], "correct": "2"},
]

used_questions = set()

def shuffle_options(question):
    options = question["options"]
    correct_answer = question["correct"]
    
    # Tạo một danh sách các tuple (option, is_correct)
    options_with_flags = [(option, option == correct_answer) for option in options]
    
    # Hoán đổi vị trí các lựa chọn
    random.shuffle(options_with_flags)
    
    # Tách lại danh sách các lựa chọn và cờ đúng/sai
    shuffled_options = [option for option, is_correct in options_with_flags]
    correct_index = next(i for i, (option, is_correct) in enumerate(options_with_flags) if is_correct)
    
    return shuffled_options, correct_index

async def start_traloicauhoi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global used_questions
    chat_id = update.effective_chat.id
    user = update.effective_user
    logger.debug(f"Attempting to start Trả Lời Câu Hỏi game in chat {chat_id}")

    if chat_id in game_state and game_state[chat_id].get("game_started", False):
        if user.id in [p.id for p in game_state[chat_id]["players"]]:
            await update.message.reply_text("Bạn đã tham gia trận chiến rồi, vui lòng đợi đối thủ tham gia.")
        else:
            await update.message.reply_text("Đã có một người tham gia rồi, mời bạn bấm /jointraloicauhoi để tham gia.")
        return

    logger.debug(f"Starting Trả Lời Câu Hỏi game in chat {chat_id}")

    # Lọc ra các câu hỏi chưa được sử dụng
    available_questions = [q for q in QUESTIONS if q["question"] not in used_questions]
    
    # Nếu số lượng câu hỏi còn lại ít hơn 5, reset lại danh sách các câu hỏi đã sử dụng
    if len(available_questions) < 5:
        used_questions = set()
        available_questions = QUESTIONS.copy()

    # Lấy 5 câu hỏi ngẫu nhiên từ danh sách các câu hỏi chưa được sử dụng
    selected_questions = random.sample(available_questions, 5)
    
    # Cập nhật danh sách các câu hỏi đã sử dụng
    used_questions.update(q["question"] for q in selected_questions)

    # Hoán đổi vị trí các lựa chọn cho mỗi câu hỏi
    for question in selected_questions:
        question["options"], question["correct_index"] = shuffle_options(question)

    game_state[chat_id] = {
        "game_started": True,
        "players": [user],
        "questions": selected_questions,
        "current_question": 0,
        "scores": {},
        "answers": {},
        "messages": []
    }

    # Gửi thông báo chung vào group
    announcement = await update.message.reply_text(
        "Kính mời quan viên 2 họ tham gia trò chơi Trả Lời Câu Hỏi\n/jointraloicauhoi"
    )
    game_state[chat_id]["messages"].append(announcement.message_id)

    # Gửi thông báo với ảnh (nếu có)
    image_path = os.path.join(os.path.dirname(__file__), 'solo.jpg')
    
    if os.path.exists(image_path):
        caption = f"Sân chơi đã có 1 người tham gia:\n\n<b>{user.full_name}</b>\nvs\n......."
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

async def join_traloicauhoi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    logger.debug(f"User {user.id} trying to join Trả Lời Câu Hỏi game in chat {chat_id}")
    
    if chat_id not in game_state or not game_state[chat_id].get("game_started", False):
        await update.message.reply_text("Hiện tại chưa có game nào được tạo. Hãy sử dụng lệnh /traloicauhoi để tạo game mới.")
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

    for player in players:
        game_state[chat_id]["scores"][player.id] = 0
        game_state[chat_id]["answers"][player.id] = []

    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update:
        chat_id = update.effective_chat.id
    elif context.job:
        chat_id = context.job.chat_id
    else:
        # Lấy chat_id từ game_state nếu không có update hoặc job
        chat_id = next(iter(game_state.keys()))

    current_question = game_state[chat_id]["current_question"]
    question_data = game_state[chat_id]["questions"][current_question]

    # Sử dụng các đáp án đã trộn từ shuffle_options
    options = question_data["options"]
    correct_index = question_data["correct_index"]

    logger.debug(f"Asking question {current_question + 1}/5 for chat {chat_id}")

    # Tạo các button từ danh sách đáp án đã trộn
    keyboard = [
        [
            InlineKeyboardButton(options[0], callback_data=f"answer:{chat_id}:{current_question}:{0}"),
            InlineKeyboardButton(options[1], callback_data=f"answer:{chat_id}:{current_question}:{1}")
        ],
        [
            InlineKeyboardButton(options[2], callback_data=f"answer:{chat_id}:{current_question}:{2}"),
            InlineKeyboardButton(options[3], callback_data=f"answer:{chat_id}:{current_question}:{3}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    question_text = f"Câu hỏi {current_question + 1}/5:\n{question_data['question']}\n\nBạn có 5s để trả lời!"

    for player in game_state[chat_id]["players"]:
        message = await context.bot.send_message(
            chat_id=player.id,
            text=question_text,
            reply_markup=reply_markup
        )
        # Lưu lại ID của tin nhắn câu hỏi
        if "question_messages" not in game_state[chat_id]:
            game_state[chat_id]["question_messages"] = []
        game_state[chat_id]["question_messages"].append(message.message_id)

    # Lưu lại chỉ số của đáp án đúng để so sánh sau này
    game_state[chat_id]["correct_index"] = correct_index

    # Đặt timer cho câu hỏi
    context.job_queue.run_once(question_timeout, 10, chat_id=chat_id, name=f'question_timeout_{chat_id}')

    # Đặt timer để xóa tin nhắn câu hỏi sau 2 giây
    context.job_queue.run_once(delete_old_question_messages, 2, chat_id=chat_id, name=f'delete_question_{chat_id}')

async def delete_old_question_messages(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id

    if chat_id in game_state and "question_messages" in game_state[chat_id]:
        for message_id in game_state[chat_id]["question_messages"]:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logger.error(f"Error deleting question message: {e}")
        # Xóa danh sách tin nhắn câu hỏi sau khi đã xóa
        game_state[chat_id]["question_messages"] = []

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        user = query.from_user
        data = query.data.split(":")
        chat_id = int(data[1])
        question_number = int(data[2])
        answer_index = int(data[3])

        logger.debug(f"Received answer from user {user.id} for question {question_number}: option {answer_index}")

        if chat_id not in game_state:
            logger.warning(f"Chat ID {chat_id} not found in game_state")
            return
        if user.id not in [p.id for p in game_state[chat_id]["players"]]:
            logger.warning(f"User {user.id} not found in players for chat {chat_id}")
            return

        if question_number != game_state[chat_id]["current_question"]:
            logger.warning(f"Question number mismatch: received {question_number}, current is {game_state[chat_id]['current_question']}")
            await query.edit_message_text("Câu hỏi này đã kết thúc.")
            return

        # Kiểm tra chỉ số của đáp án đúng từ game_state
        correct_index = game_state[chat_id]["correct_index"]
        is_correct = (answer_index == correct_index)

        selected_answer = game_state[chat_id]["questions"][question_number]["options"][answer_index]
        correct_answer = game_state[chat_id]["questions"][question_number]["options"][correct_index]

        await query.edit_message_text(f"Bạn đã chọn đáp án: {selected_answer}")

        if is_correct:
            game_state[chat_id]["scores"][user.id] += 1
            game_state[chat_id]["answers"][user.id].append("🔵")
        else:
            game_state[chat_id]["answers"][user.id].append("🔴")

        logger.debug(f"Current game state for chat {chat_id}: {game_state[chat_id]}")

        # Kiểm tra xem tất cả người chơi đã trả lời chưa
        all_answered = all(len(game_state[chat_id]["answers"][p.id]) == question_number + 1 for p in game_state[chat_id]["players"])
        logger.debug(f"All players answered: {all_answered}")

        if all_answered:
            # Hủy timer của câu hỏi hiện tại
            current_jobs = context.job_queue.get_jobs_by_name(f'question_timeout_{chat_id}')
            for job in current_jobs:
                job.schedule_removal()

            # Hiển thị đáp án đúng cho tất cả người chơi
            for player in game_state[chat_id]["players"]:
                await context.bot.send_message(
                    chat_id=player.id,
                    text=f"Đáp án đúng là: {correct_answer}"
                )

            # Cập nhật kết quả trong nhóm
            await update_group_score(context, chat_id)

            # Chuyển sang câu hỏi tiếp theo hoặc kết thúc trò chơi
            game_state[chat_id]["current_question"] += 1
            logger.debug(f"Moving to next question. Current question: {game_state[chat_id]['current_question']}")
            if game_state[chat_id]["current_question"] < 5:
                await asyncio.sleep(2)  # Đợi 2 giây trước khi chuyển câu hỏi
                await ask_question(None, context)
            else:
                await end_game(None, context)

    except Exception as e:
        logger.error(f"Error in handle_answer: {e}", exc_info=True)
        await context.bot.send_message(chat_id=chat_id, text=f"Đã xảy ra lỗi khi xử lý câu trả lời của bạn: {str(e)}")

async def question_timeout(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id

    if chat_id not in game_state:
        return

    current_question = game_state[chat_id]["current_question"]
    correct_answer = game_state[chat_id]["questions"][current_question]["correct"]

    for player in game_state[chat_id]["players"]:
        if len(game_state[chat_id]["answers"][player.id]) <= current_question:
            game_state[chat_id]["answers"][player.id].append("🔴")
            await context.bot.send_message(
                chat_id=player.id,
                text=f"Hết thời gian! Đáp án đúng là: {correct_answer}"
            )

    # Cập nhật kết quả trong nhóm
    await update_group_score(context, chat_id)

    # Chuyển sang câu hỏi tiếp theo hoặc kết thúc trò chơi
    game_state[chat_id]["current_question"] += 1
    if game_state[chat_id]["current_question"] < 5:
        await ask_question(None, context)
    else:
        await end_game(None, context)
        
async def update_group_score(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    players = game_state[chat_id]["players"]
    result = "Sân thi đấu của 2 thành viên hiện tại đang rất căng thẳng:\n\n"
    for player in players:
        answers = game_state[chat_id]["answers"][player.id]
        correct_answers = answers.count("🔵")
        result += f"👦 <b>{player.full_name}</b> trả lời Đúng: {''.join(answers)} {correct_answers}/5\n"

    # Xóa tin nhắn cũ nếu có
    if "last_score_message" in game_state[chat_id]:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=game_state[chat_id]["last_score_message"])
        except Exception as e:
            logger.error(f"Error deleting old score message: {e}")

    # Gửi tin nhắn mới và lưu ID
    message = await context.bot.send_message(chat_id=chat_id, text=result, parse_mode='HTML')
    game_state[chat_id]["last_score_message"] = message.message_id

async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update:
        chat_id = update.effective_chat.id
    elif context.job:
        chat_id = context.job.chat_id
    else:
        # Lấy chat_id từ game_state nếu không có update hoặc job
        chat_id = next(iter(game_state.keys()))

    players = game_state[chat_id]["players"]
    scores = game_state[chat_id]["scores"]

    logger.debug(f"Ending game for chat {chat_id}")

    result = "Kết quả cuối cùng:\n\n"
    for player in players:
        answers = game_state[chat_id]["answers"][player.id]
        correct_answers = answers.count("🔵")
        result += f"{player.full_name}: {''.join(answers)} {correct_answers}/5\n"

    max_score = max(scores.values())
    winners = [p for p in players if scores[p.id] == max_score]

    if len(winners) > 1 or max_score == 0:
        result += "\nKết quả: Hòa! Không có người chiến thắng."
    else:
        winner = winners[0]
        result += f"\nNgười chiến thắng là 👑 <b>{winner.full_name}</b> với <b>{max_score}</b> câu trả lời đúng!"
        result += "\nPhần thưởng sẽ được người thua cuộc mời 1 ly nước."

    # Xóa tin nhắn kết quả tạm thời nếu có
    if "last_score_message" in game_state[chat_id]:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=game_state[chat_id]["last_score_message"])
        except Exception as e:
            logger.error(f"Error deleting last score message: {e}")

    await context.bot.send_message(chat_id=chat_id, text=result, parse_mode='HTML')
    del game_state[chat_id]

def register_handlers(application):
    application.add_handler(CommandHandler("traloicauhoi", start_traloicauhoi))
    application.add_handler(CommandHandler("jointraloicauhoi", join_traloicauhoi))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer:"))