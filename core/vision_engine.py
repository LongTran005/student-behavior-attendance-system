# core/vision_engine.py
import cv2
import json
import time
import numpy as np
from ultralytics import YOLO
from deepface import DeepFace
from db_helper import DatabaseHelper

class VisionEngine:
    def __init__(self):
        self.db = DatabaseHelper()
        self.model_yolo = YOLO("yolo11n.pt") 
        self.is_running = False
        self.session_attendance = {}
        self.known_students = []
        self.load_known_embeddings()

    def load_known_embeddings(self):
        rows = self.db.get_all_valid_embeddings()
        self.known_students = []
        for row in rows:
            try:
                emb_list = json.loads(row['face_embedding'])
                self.known_students.append({
                    "student_id": row['student_id'],
                    "full_name": row['full_name'],
                    "avatar_path": row['avatar_path'],
                    "embedding": np.array(emb_list, dtype=np.float32)
                })
            except Exception as e:
                print(f"[X] Lỗi đọc Vector SV {row['student_id']}: {e}")

    def compute_cosine_distance(self, emb1, emb2):
        dot_product = np.dot(emb1, emb2)
        norm_emb1 = np.linalg.norm(emb1)
        norm_emb2 = np.linalg.norm(emb2)
        return 1.0 - (dot_product / (norm_emb1 * norm_emb2))

    def stop_stream(self):
        self.is_running = False

    def start_stream(self, session_id, ui_update_callback, student_detected_callback, session_end_callback, log_callback):
        self.is_running = True
        self.session_attendance = {}
        cap = cv2.VideoCapture(0)
        
        # Đọc độ phân giải gốc của Camera
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        log_callback("[HỆ THỐNG] Bắt đầu phiên điểm danh realtime (30s)...")
        start_time = time.time()

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                break

            elapsed_time = time.time() - start_time
            if elapsed_time > 30.0:
                self.is_running = False
                break

            current_phase_status = "Có mặt" if elapsed_time <= 10.0 else "Đi trễ"

            results = self.model_yolo(frame, verbose=False)
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0].item())
                    cls = int(box.cls[0].item())

                    if cls == 0 and conf > 0.45: # Nhận diện người học
                        # Mở rộng vùng cắt 15px để tránh việc mất một phần khuôn mặt làm DeepFace lỗi
                        h_f, w_f, _ = frame.shape
                        pad = 15
                        x1_p = max(0, x1 - pad)
                        y1_p = max(0, y1 - pad)
                        x2_p = min(w_f, x2 + pad)
                        y2_p = min(h_f, y2 + pad)

                        student_crop = frame[y1_p:y2_p, x1_p:x2_p]
                        if student_crop.size == 0:
                            continue

                        color = (0, 255, 255)
                        label_text = "Scanning..."

                        try:
                            # Đặt detector_backend="opencv" kết hợp enforce_detection=False để tối ưu tốc độ
                            emb_objs = DeepFace.represent(
                                img_path=student_crop,
                                model_name="Facenet",
                                detector_backend="opencv",
                                enforce_detection=False
                            )
                            
                            if emb_objs and len(emb_objs) > 0:
                                current_emb = np.array(emb_objs[0]["embedding"], dtype=np.float32)
                                min_dist = 1.0
                                match_student = None
                                
                                for student in self.known_students:
                                    dist = self.compute_cosine_distance(current_emb, student["embedding"])
                                    if dist < min_dist:
                                        min_dist = dist
                                        match_student = student
                                
                                # Ngưỡng Face Match an toàn là < 0.5 đối với Facenet Cosine
                                if min_dist < 0.55 and match_student:
                                    student_id = match_student["student_id"]
                                    name = match_student["full_name"]
                                    avatar = match_student["avatar_path"]
                                    
                                    behavior = "Focusing" if int(elapsed_time) % 5 < 3 else "Distracted"
                                    
                                    if student_id not in self.session_attendance:
                                        self.db.insert_attendance(session_id, student_id, current_phase_status)
                                        self.session_attendance[student_id] = {
                                            "full_name": name,
                                            "attendance_status": current_phase_status,
                                            "behavior": behavior,
                                            "avatar_path": avatar
                                        }
                                        log_callback(f"[GHI NHẬN] SV {name} - {current_phase_status}")
                                    else:
                                        self.session_attendance[student_id]["behavior"] = behavior

                                    if int(elapsed_time) % 5 == 0:
                                        self.db.insert_learning_status(session_id, student_id, behavior)

                                    student_detected_callback(student_id, name, current_phase_status, avatar)
                                    color = (0, 255, 0) if current_phase_status == "Có mặt" else (0, 165, 255)
                                    label_text = f"{name} ({behavior})"
                                else:
                                    color = (0, 0, 255)
                                    label_text = "Unknown"
                        except Exception as e:
                            pass

                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            ui_update_callback(frame)
            time.sleep(0.01)

        cap.release()
        session_end_callback()