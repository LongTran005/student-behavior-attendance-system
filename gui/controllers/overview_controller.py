# gui/controllers/overview_controller.py
import os
import shutil
import json
from db_helper import DatabaseHelper
from config import DATASET_ENROLLMENT_DIR

try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None

class OverviewController:
    def __init__(self):
        # Khởi tạo đối tượng kết nối Database
        self.db = DatabaseHelper()

    def get_stats_data(self):
        """Lấy dữ liệu thống kê tổng quan cho các thẻ Stats Cards"""
        try:
            # 1. Tổng số sinh viên trong hệ thống (Bảng Student)
            total_students = self.db.count_students()

            # 2. Số sinh viên có mặt trong buổi học gần nhất (Bảng Attendance)
            session_id = self.db.get_latest_session_id()
            
            present_students = 0
            if session_id:
                present_students = self.db.count_present_by_session(session_id)

            # Tính tỷ lệ chuyên cần chuyên sâu
            attendance_rate = "0%"
            if total_students > 0:
                attendance_rate = f"{int((present_students / total_students) * 100)}%"

            # 3. Thống kê cảnh báo AI (Số lượng sinh viên đang ngủ hoặc mất tập trung ở phiên gần nhất)
            ai_alerts = 0
            if session_id:
                ai_alerts = self.db.count_alert_students_by_session(session_id)

            return {
                "total": str(total_students),
                "present": str(present_students),
                "rate": attendance_rate,
                "alerts": str(ai_alerts)
            }
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu thống kê: {e}")
            return {"total": "0", "present": "0", "rate": "0%", "alerts": "0"}

    def load_all_students(self):
        """Tải toàn bộ danh sách sinh viên từ database"""
        try:
            return self.db.get_all_students_with_classroom()
        except Exception as e:
            print(f"Lỗi load_all_students: {e}")
            return []

    def load_all_sessions(self):
        """Tải danh sách các buổi học đã diễn ra"""
        try:
            sessions = self.db.get_all_sessions()
            return [
                (
                    session["session_id"],
                    session["course_name"],
                    session["lecture_date"],
                    self._format_session_time(session),
                )
                for session in sessions
            ]
        except Exception as e:
            print(f"Lỗi load_all_sessions: {e}")
            return []

    def get_session_attendance_details(self, session_id):
        """Lấy chi tiết điểm danh và trạng thái học tập AI của một buổi học cụ thể"""
        try:
            return self.db.get_session_attendance_details(session_id)
        except Exception as e:
            print(f"Lỗi get_session_attendance_details: {e}")
            return []

    def get_student_by_id(self, student_id):
        """Lấy thông tin chi tiết sinh viên theo MSSV"""
        try:
            return self.db.get_student_by_id(student_id)
        except Exception as e:
            print(f"Lỗi get_student_by_id: {e}")
            return None

    def handle_update_student(self, student_id, full_name, class_name, email, phone, new_image_path=None):
        """
        Xử lý logic cập nhật thông tin sinh viên.
        Nếu có ảnh mới: re-extract Face Embedding + copy ảnh vào dataset.
        Nếu không đổi ảnh: chỉ cập nhật thông tin cá nhân.
        """
        # 1. Kiểm tra trường bắt buộc
        if not full_name or not class_name or not email:
            return {"status": "error", "message": "Vui lòng nhập đầy đủ: Họ tên, Lớp và Email!"}

        # 2. Kiểm tra email trùng lặp (với sinh viên khác, không phải chính mình)
        current_student = self.db.get_student_by_id(student_id)
        if not current_student:
            return {"status": "error", "message": f"Không tìm thấy sinh viên có MSSV: {student_id}"}

        if email != current_student["email"] and self.db.check_exists("email", email):
            return {"status": "error", "message": f"Email '{email}' đã được sử dụng bởi sinh viên khác!"}

        if phone and phone != (current_student["phone"] or "") and self.db.check_exists("phone", phone):
            return {"status": "error", "message": f"Số điện thoại '{phone}' đã được sử dụng trong hệ thống!"}

        # 3. Xử lý ảnh mới (nếu có)
        avatar_path = None
        embedding_json = None

        if new_image_path and os.path.exists(new_image_path):
            # 3a. Trích xuất Face Embedding từ ảnh mới
            if DeepFace is not None:
                try:
                    embedding_objs = DeepFace.represent(
                        img_path=new_image_path,
                        model_name="ArcFace",
                        detector_backend="retinaface",
                        enforce_detection=True,
                        align=True
                    )
                    if embedding_objs and len(embedding_objs) > 0:
                        embedding_vector = embedding_objs[0]["embedding"]
                        if all(v == 0 for v in embedding_vector):
                            return {"status": "error", "message": "Không thể trích xuất đặc trưng từ ảnh mới! Vui lòng chọn ảnh rõ mặt hơn."}
                        embedding_json = json.dumps(embedding_vector)
                    else:
                        return {"status": "error", "message": "Không tìm thấy khuôn mặt trong ảnh mới. Vui lòng chọn ảnh chân dung khác!"}
                except Exception as e:
                    return {"status": "error", "message": f"Lỗi nhận diện khuôn mặt từ ảnh mới: {str(e)}"}
            else:
                print("[Warning] DeepFace chưa cài đặt. Bỏ qua bước trích xuất embedding.")

            # 3b. Copy ảnh mới vào thư mục dataset
            try:
                ext = os.path.splitext(new_image_path)[1].lower() or ".jpg"
                clean_name = full_name.strip().replace(" ", "_")
                target_filename = f"{student_id.strip()}_{clean_name}{ext}"
                target_file_path = os.path.join(DATASET_ENROLLMENT_DIR, target_filename)

                # Xóa ảnh cũ nếu khác file mới
                old_avatar = current_student.get("avatar_path")
                if old_avatar and os.path.exists(old_avatar) and old_avatar != target_file_path:
                    try:
                        os.remove(old_avatar)
                    except OSError:
                        pass

                shutil.copy2(new_image_path, target_file_path)
                avatar_path = target_file_path
            except Exception as e:
                return {"status": "error", "message": f"Lỗi sao chép ảnh mới: {str(e)}"}

        # 4. Gọi tầng Database cập nhật
        success = self.db.update_student(
            student_id=student_id,
            full_name=full_name.strip(),
            class_name=class_name.strip(),
            email=email.strip(),
            phone=phone.strip() if phone else None,
            avatar_path=avatar_path,
            face_embedding=embedding_json,
        )

        if success:
            return {"status": "success", "message": f"Đã cập nhật thông tin sinh viên {full_name} thành công!"}
        else:
            return {"status": "error", "message": "Đã xảy ra lỗi khi cập nhật dữ liệu trong database."}

    def handle_delete_student(self, student_id):
        """Xử lý logic xóa sinh viên: xóa file ảnh vật lý + xóa bản ghi DB"""
        # 1. Lấy thông tin sinh viên để tìm file ảnh cần xóa
        student = self.db.get_student_by_id(student_id)
        if not student:
            return {"status": "error", "message": f"Không tìm thấy sinh viên có MSSV: {student_id}"}

        student_name = student["full_name"]

        # 2. Xóa file ảnh vật lý nếu tồn tại
        avatar_path = student.get("avatar_path")
        if avatar_path and os.path.exists(avatar_path):
            try:
                os.remove(avatar_path)
            except OSError as e:
                print(f"[Warning] Không thể xóa file ảnh: {e}")

        # 3. Xóa bản ghi trong database (cascade: attendance + learning_status)
        success = self.db.delete_student(student_id)
        if success:
            return {"status": "success", "message": f"Đã xóa sinh viên {student_name} ({student_id}) và toàn bộ dữ liệu liên quan."}
        else:
            return {"status": "error", "message": "Đã xảy ra lỗi khi xóa sinh viên khỏi database."}

    @staticmethod
    def _format_session_time(session):
        start_time = session.get("start_time") or "--:--"
        end_time = session.get("end_time") or "--:--"
        return f"{start_time} - {end_time}"
