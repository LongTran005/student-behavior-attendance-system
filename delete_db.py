# Dùng phần này để xóa toàn bộ dữ liệu trong database khi cần thiết, đặc biệt là trước khi chạy các bài test để đảm bảo môi trường sạch sẽ và không bị ảnh hưởng bởi dữ liệu cũ. Hãy cẩn thận khi sử dụng chức năng này vì nó sẽ xóa tất cả dữ liệu hiện có trong database!
import sqlite3
from config import DB_PATH

def clear_all_database_data():
    """Hàm xóa sạch toàn bộ dữ liệu trong tất cả các bảng của hệ thống"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Bật chế độ ràng buộc khóa ngoại để đảm bảo an toàn dữ liệu (nếu cần)
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        print("[*] Đang bắt đầu dọn dẹp Database...")
        
        # 1. Xóa các bảng chứa dữ liệu phụ/log trước để tránh lỗi Foreign Key Constraint
        cursor.execute("DELETE FROM LearningStatus;")
        cursor.execute("DELETE FROM Attendance;")
        
        # 2. Xóa các bảng chứa dữ liệu chính sau
        cursor.execute("DELETE FROM LectureSession;")
        cursor.execute("DELETE FROM Student;")
        cursor.execute("DELETE FROM Classroom;")
        
        # 3. Reset các tiến trình đếm ID tự động (AUTOINCREMENT) về lại 0
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('LearningStatus', 'Attendance', 'LectureSession', 'Classroom');")
        
        conn.commit()
        print("[+] ĐÃ XÓA SẠCH TOÀN BỘ DỮ LIỆU TRONG DATABASE THÀNH CÔNG!")
        
        conn.close()
    except Exception as e:
        print(f"[X] Lỗi khi thao tác dọn dẹp Database: {e}")

if __name__ == "__main__":
    # Xác nhận lại một lần nữa trước khi chạy code xóa sạch data
    confirm = input("Bạn có chắc chắn muốn XÓA TOÀN BỘ dữ liệu trong database không? (y/n): ")
    if confirm.lower() == 'y':
        clear_all_database_data()
    else:
        print("[-] Đã hủy thao tác xóa dữ liệu.")