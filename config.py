# config.py
import os

# Đường dẫn gốc của dự án
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Thư mục lưu trữ dữ liệu vật lý vật lý
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DATABASE_DIR, "classroom.db")

# Thư mục chứa ảnh thẻ sinh viên phục vụ đăng ký khuôn mặt gốc (Giai đoạn 1)
DATASET_ENROLLMENT_DIR = os.path.join(BASE_DIR, "dataset_enrollment")

# Tự động khởi tạo các thư mục nếu chưa tồn tại trên ổ đĩa
os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(DATASET_ENROLLMENT_DIR, exist_ok=True)