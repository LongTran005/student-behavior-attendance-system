# database/student_crud.py

from database.classroom_crud import ClassroomRepository
from database.connection import BaseRepository


class StudentRepository(BaseRepository):
    ALLOWED_CHECK_FIELDS = {"student_id", "email", "phone"}

    def __init__(self, db_path=None, classroom_repo=None):
        super().__init__(db_path)
        self.classroom_repo = classroom_repo or ClassroomRepository(self.db_path)

    def check_exists(self, field_name, value):
        if field_name not in self.ALLOWED_CHECK_FIELDS:
            raise ValueError(f"Khong ho tro kiem tra trung lap truong: {field_name}")

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT 1 FROM Student WHERE {field_name} = ?", (value,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def insert_student(self, student_id, full_name, class_name, email, phone, avatar_path, face_embedding=None):
        classroom_id = self.classroom_repo.get_or_create_classroom(class_name)

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Student
                    (student_id, full_name, classroom_id, email, phone, avatar_path, face_embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (student_id, full_name, classroom_id, email, phone, avatar_path, face_embedding),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[Error] Failed to insert student: {e}")
            return False
        finally:
            conn.close()

    def get_all_valid_embeddings(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT student_id, full_name, face_embedding, avatar_path
                FROM Student
                WHERE face_embedding IS NOT NULL
                """
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def count_students(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM Student")
            return cursor.fetchone()[0] or 0
        finally:
            conn.close()

    def get_all_students_with_classroom(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT s.student_id, s.full_name, c.class_name
                FROM Student s
                LEFT JOIN Classroom c ON s.classroom_id = c.classroom_id
                ORDER BY s.student_id ASC
                """
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def get_student_by_id(self, student_id):
        """Lấy toàn bộ thông tin của một sinh viên theo MSSV"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT s.student_id, s.full_name, s.classroom_id, c.class_name,
                       s.email, s.phone, s.face_embedding, s.avatar_path
                FROM Student s
                LEFT JOIN Classroom c ON s.classroom_id = c.classroom_id
                WHERE s.student_id = ?
                """,
                (student_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "student_id": row["student_id"],
                "full_name": row["full_name"],
                "classroom_id": row["classroom_id"],
                "class_name": row["class_name"],
                "email": row["email"],
                "phone": row["phone"],
                "face_embedding": row["face_embedding"],
                "avatar_path": row["avatar_path"],
            }
        finally:
            conn.close()

    def update_student(self, student_id, full_name, class_name, email, phone, avatar_path=None, face_embedding=None):
        """Cập nhật thông tin sinh viên (bao gồm cả ảnh và embedding nếu có)"""
        classroom_id = self.classroom_repo.get_or_create_classroom(class_name)

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if avatar_path is not None and face_embedding is not None:
                # Cập nhật đầy đủ kèm ảnh mới và embedding mới
                cursor.execute(
                    """
                    UPDATE Student
                    SET full_name = ?, classroom_id = ?, email = ?, phone = ?,
                        avatar_path = ?, face_embedding = ?
                    WHERE student_id = ?
                    """,
                    (full_name, classroom_id, email, phone, avatar_path, face_embedding, student_id),
                )
            else:
                # Chỉ cập nhật thông tin cá nhân, giữ nguyên ảnh và embedding cũ
                cursor.execute(
                    """
                    UPDATE Student
                    SET full_name = ?, classroom_id = ?, email = ?, phone = ?
                    WHERE student_id = ?
                    """,
                    (full_name, classroom_id, email, phone, student_id),
                )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[Error] Failed to update student: {e}")
            return False
        finally:
            conn.close()

    def delete_student(self, student_id):
        """Xóa sinh viên và toàn bộ dữ liệu liên quan (attendance, learning_status)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Xóa bản ghi trạng thái học tập (LearningStatus) liên quan
            cursor.execute("DELETE FROM LearningStatus WHERE student_id = ?", (student_id,))
            # 2. Xóa bản ghi điểm danh (Attendance) liên quan
            cursor.execute("DELETE FROM Attendance WHERE student_id = ?", (student_id,))
            # 3. Xóa bản ghi sinh viên chính
            cursor.execute("DELETE FROM Student WHERE student_id = ?", (student_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[Error] Failed to delete student: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_students_by_classroom(self, classroom_id):
        """Lấy danh sách sinh viên thuộc một lớp cụ thể"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT student_id, full_name, avatar_path
                FROM Student
                WHERE classroom_id = ?
                ORDER BY student_id ASC
                """,
                (classroom_id,),
            )
            return cursor.fetchall()
        finally:
            conn.close()
