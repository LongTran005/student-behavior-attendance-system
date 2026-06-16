# database/attendance_crud.py

from database.connection import BaseRepository


class AttendanceRepository(BaseRepository):
    def insert_attendance(self, session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO Attendance
                    (session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[Error] Failed to insert attendance: {e}")
            return False
        finally:
            conn.close()

    def count_present_by_session(self, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM Attendance
                WHERE session_id = ? AND attendance_status = 'Có mặt'
                """,
                (session_id,),
            )
            return cursor.fetchone()[0] or 0
        except Exception as e:
            print(f"[Error] Failed to count present students: {e}")
            return 0
        finally:
            conn.close()

    def get_session_attendance_details(self, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    s.student_id,
                    s.full_name,
                    a.attendance_status,
                    (
                        SELECT ls.learning_behavior
                        FROM LearningStatus ls
                        WHERE ls.student_id = s.student_id
                          AND ls.session_id = ?
                        ORDER BY ls.status_id DESC
                        LIMIT 1
                    ) AS latest_behavior
                FROM LectureSession session
                JOIN Student s
                    ON s.classroom_id = session.classroom_id
                LEFT JOIN Attendance a
                    ON s.student_id = a.student_id
                   AND a.session_id = ?
                WHERE session.session_id = ?
                ORDER BY s.student_id ASC
                """,
                (session_id, session_id, session_id),
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"[Error] Failed to get session attendance details: {e}")
            return []
        finally:
            conn.close()

    def get_session_export_data(self, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    session.session_id,
                    session.course_code,
                    session.course_name,
                    session.lecture_date,
                    session.start_time,
                    session.end_time,
                    session.status,
                    classroom.class_code,
                    classroom.class_name,
                    classroom.department,
                    classroom.academic_year,
                    user.display_name AS teacher_name,
                    user.user_id AS teacher_id
                FROM LectureSession session
                LEFT JOIN Classroom classroom
                    ON classroom.classroom_id = session.classroom_id
                LEFT JOIN User user
                    ON user.user_id = session.created_by
                WHERE session.session_id = ?
                """,
                (session_id,),
            )
            session = cursor.fetchone()
            if not session:
                return None

            cursor.execute(
                """
                SELECT
                    s.student_id,
                    s.full_name,
                    classroom.class_name,
                    a.attendance_status,
                    (
                        SELECT ls.learning_behavior
                        FROM LearningStatus ls
                        WHERE ls.student_id = s.student_id
                          AND ls.session_id = ?
                        ORDER BY ls.status_id DESC
                        LIMIT 1
                    ) AS latest_behavior
                FROM LectureSession session
                JOIN Student s
                    ON s.classroom_id = session.classroom_id
                LEFT JOIN Classroom classroom
                    ON classroom.classroom_id = s.classroom_id
                LEFT JOIN Attendance a
                    ON a.student_id = s.student_id
                   AND a.session_id = session.session_id
                WHERE session.session_id = ?
                ORDER BY s.student_id ASC
                """,
                (session_id, session_id),
            )
            return {
                "session": dict(session),
                "students": [dict(row) for row in cursor.fetchall()],
            }
        except Exception as e:
            print(f"[Error] Failed to get session export data: {e}")
            return None
        finally:
            conn.close()
