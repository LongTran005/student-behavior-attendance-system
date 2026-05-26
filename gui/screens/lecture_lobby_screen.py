# gui/screens/lecture_lobby_screen.py
import customtkinter as ctk
from datetime import datetime
from gui.theme import THEME_COLORS, FONT_FAMILY
from db_helper import DatabaseHelper
from gui.controllers.lecture_lobby_controller import LectureLobbyController

class LectureLobbyScreen(ctk.CTkFrame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, fg_color="transparent")
        self.db = DatabaseHelper() 
        self.controller = controller if controller else LectureLobbyController()
        
        self.current_session = None
        self.lobby_job = None  
        self.last_scheduled_ids = None 
        
        self.init_ui()

    def init_ui(self):
        # --- 1. KHU VỰC TRÊN: BÀI GIẢNG SẮP / ĐANG DIỄN RA ---
        self.top_container = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        self.top_container.pack(fill="x", padx=40, pady=(30, 20))
        
        self.lbl_title = ctk.CTkLabel(self.top_container, text="SẢNH CHỜ LỚP HỌC THÔNG MINH (LOBBY)", font=(FONT_FAMILY, 22, "bold"), text_color=THEME_COLORS["text_title"])
        self.lbl_title.pack(pady=(30, 15))
        
        self.lbl_lecture_info = ctk.CTkLabel(self.top_container, text="Hệ thống đang đồng bộ danh sách bài giảng...", font=(FONT_FAMILY, 16), text_color=THEME_COLORS["text_main"])
        self.lbl_lecture_info.pack(pady=5)
        
        self.lbl_timer = ctk.CTkLabel(self.top_container, text="--:--:--", font=(FONT_FAMILY, 36, "bold"), text_color=THEME_COLORS["primary"])
        self.lbl_timer.pack(pady=15)
        
        self.lbl_status = ctk.CTkLabel(self.top_container, text="Trạng thái: Khởi động", font=(FONT_FAMILY, 13, "bold"), text_color=THEME_COLORS["text_muted"])
        self.lbl_status.pack(pady=(5, 30))

        # --- 2. KHU VỰC DƯỚI: DANH SÁCH CÁC BÀI GIẢNG ĐÃ ĐĂNG KÝ (CHƯA DIỄN RA) ---
        self.bottom_container = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_container.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        ctk.CTkLabel(
            self.bottom_container, text="DANH SÁCH CÁC BÀI GIẢNG SẮP TỚI", 
            font=(FONT_FAMILY, 15, "bold"), text_color=THEME_COLORS["text_title"]
        ).pack(anchor="w", pady=(0, 10))

        self.scroll_list = ctk.CTkScrollableFrame(self.bottom_container, fg_color=THEME_COLORS["bg_card"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        self.scroll_list.pack(fill="both", expand=True)

        self.start_lobby_loop()

    def refresh_and_load_data(self):
        self.current_session = None
        self.last_scheduled_ids = None 
        if self.lobby_job:
            self.after_cancel(self.lobby_job)
            self.lobby_job = None
        self.start_lobby_loop()

    def update_upcoming_list(self):
        """Giao tiếp với Controller để lấy danh sách cập nhật giao diện (Không viết SQL ở UI)"""
        scheduled_lectures = self.controller.load_scheduled_lectures()
        
        current_ids = [lec["id"] for lec in scheduled_lectures]
        
        # Chỉ vẽ lại giao diện nếu có sự thay đổi
        if current_ids != self.last_scheduled_ids:
            self.last_scheduled_ids = current_ids
            
            for widget in self.scroll_list.winfo_children():
                widget.destroy()
                
            # Loại bỏ bài giảng đang đếm ngược ở trên khỏi danh sách bên dưới
            display_rows = [lec for lec in scheduled_lectures if not (self.current_session and self.current_session["session_id"] == lec["id"])]

            if not display_rows:
                ctk.CTkLabel(self.scroll_list, text="Chưa có bài giảng nào khác được đăng ký trong hệ thống.", font=(FONT_FAMILY, 13, "italic"), text_color=THEME_COLORS["text_muted"]).pack(pady=30)
                return
                
            # Render thông tin từ Dict do Controller trả về
            for lec in display_rows:
                card = ctk.CTkFrame(self.scroll_list, fg_color=THEME_COLORS["bg_input"], corner_radius=8)
                card.pack(fill="x", pady=6, padx=10)
                
                course_text = f"[{lec['code']}] {lec['name']}"
                time_text = f"Ngày diễn ra: {lec['date']}  |  Giờ học: {lec['start']} - {lec['end']}"
                
                ctk.CTkLabel(card, text=course_text, font=(FONT_FAMILY, 14, "bold"), text_color=THEME_COLORS["text_main"]).pack(anchor="w", padx=15, pady=(10, 2))
                ctk.CTkLabel(card, text=time_text, font=(FONT_FAMILY, 12), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", padx=15, pady=(0, 10))

    def start_lobby_loop(self):
        if self.lobby_job:
            self.after_cancel(self.lobby_job)
            self.lobby_job = None
            
        try:
            if not self.current_session:
                session = self.db.get_session_by_status("ongoing")
                if not session:
                    session = self.db.get_next_upcoming_session()
                self.current_session = session
            
            if self.current_session:
                s_id = self.current_session["session_id"]
                name = self.current_session["course_name"]
                
                status_check = self.db.get_session_by_status("completed")
                if status_check and status_check["session_id"] == s_id:
                    self.current_session = None
                    self.lbl_lecture_info.configure(text="Buổi học vừa kết thúc hoàn tất thành công!")
                    self.lbl_timer.configure(text="--:--:--")
                    self.lbl_status.configure(text="Trạng thái sảnh: Chờ lịch trình kế tiếp", text_color=THEME_COLORS["text_muted"])
                    self.update_upcoming_list()
                    self.lobby_job = self.after(2000, self.start_lobby_loop)
                    return

                date_str = self.current_session["lecture_date"]
                start_str = self.current_session["start_time"]
                end_str = self.current_session["end_time"]
                
                try:
                    # Xử lý dữ liệu có thể chứa giây, microseconds, hoặc whitespace thừa
                    start_clean = start_str.strip().split('.')[0] if start_str else ""
                    end_clean = end_str.strip().split('.')[0] if end_str else ""
                    
                    try:
                        start_dt = datetime.strptime(f"{date_str} {start_clean}", "%Y-%m-%d %H:%M:%S")
                        end_dt = datetime.strptime(f"{date_str} {end_clean}", "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        start_dt = datetime.strptime(f"{date_str} {start_clean}", "%Y-%m-%d %H:%M")
                        end_dt = datetime.strptime(f"{date_str} {end_clean}", "%Y-%m-%d %H:%M")
                    
                    now = datetime.now()
                except ValueError as ve:
                    print(f"Lỗi parse ngày tháng: {ve}")
                    self.current_session = None
                    return

                if now > end_dt and self.current_session["status"] != "completed":
                    self.db.update_lecture_session_status(s_id, "completed")
                    self.current_session = None
                    self.lbl_lecture_info.configure(text="Buổi học đã tự động đóng do quá thời gian quy định.")
                    self.lbl_timer.configure(text="--:--:--")
                    self.lbl_status.configure(text="Trạng thái: Đã dọn dẹp phiên cũ", text_color=THEME_COLORS["text_muted"])
                    self.update_upcoming_list()
                    return

                if self.current_session["status"] == "scheduled":
                    self.lbl_lecture_info.configure(text=f"SẮP DIỄN RA: {name}")
                    
                    if now < start_dt:
                        remaining = int((start_dt - now).total_seconds())
                        self.lbl_timer.configure(text=f"Bắt đầu sau: {self.format_time(remaining)}")
                        self.lbl_status.configure(text="Trạng thái: Đang đếm ngược tới giờ học", text_color=THEME_COLORS["warning"])
                    else:
                        self.db.update_lecture_session_status(s_id, "ongoing")
                        self.current_session["status"] = "ongoing"
                        self.lbl_timer.configure(text="00:00:00")
                        self.lbl_status.configure(text="Trạng thái: Lớp học bắt đầu!", text_color=THEME_COLORS["primary_light"])

                elif self.current_session["status"] == "ongoing":
                    self.lbl_lecture_info.configure(text=f"ĐANG DIỄN RA: {name}")
                    if now < end_dt:
                        remaining = int((end_dt - now).total_seconds())
                        self.lbl_timer.configure(text=f"Thời gian còn lại: {self.format_time(remaining)}")
                        self.lbl_status.configure(text="Trạng thái: Lớp đang trong tiết giảng dạy", text_color=THEME_COLORS["success_text"])
                    else:
                        self.db.update_lecture_session_status(s_id, "completed")
                        self.current_session = None

            else:
                self.lbl_lecture_info.configure(text="Hiện không có lịch trình bài giảng nổi bật.")
                self.lbl_timer.configure(text="--:--:--")
                self.lbl_status.configure(text="Trạng thái: Sảnh trống", text_color=THEME_COLORS["text_muted"])

            # Đồng bộ vẽ UI danh sách
            self.update_upcoming_list()

        except Exception as e:
            print(f"[X] Lobby Loop Core Error: {e}")

        self.lobby_job = self.after(1000, self.start_lobby_loop)

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def pack_forget(self):
        if self.lobby_job:
            self.after_cancel(self.lobby_job)
            self.lobby_job = None
        super().pack_forget()