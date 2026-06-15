# database/learning_status_crud.py

from database.connection import BaseRepository


class LearningStatusRepository(BaseRepository):
    def aggregate_session_behavior_simple(self, session_id):
        """
        Thuật toán tối giản: Tổng hợp toàn bộ sinh viên trong buổi học bằng 1 câu lệnh SQL duy nhất.
        Đếm và so sánh trực tiếp số lần Tập trung vs Không tập trung của TẤT CẢ sinh viên cùng lúc.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Sử dụng kỹ thuật conditional aggregation (SUM(CASE WHEN...)) phối hợp với UPDATE FROM 
            # để tính toán và cập nhật hàng loạt cho mọi sinh viên trong session_id này chỉ bằng 1 câu truy vấn.
            cursor.execute(
                """
                WITH Summary AS (
                    SELECT 
                        student_id,
                        SUM(CASE WHEN learning_behavior = 'Focusing' THEN 1 ELSE 0 END) as focus_count,
                        SUM(CASE WHEN learning_behavior IN ('Distracted', 'Sleeping') THEN 1 ELSE 0 END) as bad_count
                    FROM LearningStatus
                    WHERE session_id = ?
                    GROUP BY student_id
                )
                UPDATE Attendance
                SET initial_behavior = CASE 
                    WHEN (SELECT focus_count FROM Summary WHERE Summary.student_id = Attendance.student_id) > 
                         (SELECT bad_count FROM Summary WHERE Summary.student_id = Attendance.student_id) 
                    THEN 'Focusing'
                    ELSE 'Distracted'
                END
                WHERE session_id = ? 
                  AND student_id IN (SELECT student_id FROM Summary);
                """,
                (session_id, session_id)
            )
            
            conn.commit()
            print(f"[HỆ THỐNG] Đã tổng hợp hành vi hàng loạt cực nhanh cho phiên học: {session_id}")
            return True
        except Exception as e:
            print(f"[LỖI] Không thể tổng hợp hành vi cuối buổi: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def insert_learning_status(self, session_id, student_id, learning_behavior, is_raising_hand):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO LearningStatus
                    (session_id, student_id, learning_behavior, is_raising_hand)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, student_id, learning_behavior, is_raising_hand),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[Error] Failed to insert learning status: {e}")
            return False
        finally:
            conn.close()

    def count_alert_students_by_session(self, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(DISTINCT student_id)
                FROM LearningStatus
                WHERE session_id = ?
                  AND learning_behavior IN ('Sleeping', 'Distracted')
                """,
                (session_id,),
            )
            return cursor.fetchone()[0] or 0
        except Exception as e:
            print(f"[Error] Failed to count AI alert students: {e}")
            return 0
        finally:
            conn.close()

    def get_behavior_stats(self):
        """Thống kê tổng hợp hành vi sinh viên: Focusing vs Distracted"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT learning_behavior, COUNT(*) as count
                FROM LearningStatus
                GROUP BY learning_behavior
                """
            )
            result = {}
            for row in cursor.fetchall():
                result[row["learning_behavior"]] = row["count"]
            return result
        except Exception as e:
            print(f"[Error] Failed to get behavior stats: {e}")
            return {}
        finally:
            conn.close()
