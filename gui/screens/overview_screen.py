# gui/screens/overview_screen.py
import csv
import customtkinter as ctk
from tkinter import messagebox, filedialog
from gui.theme import THEME_COLORS, FONT_FAMILY
from gui.components.card import CustomCard
from gui.controllers.overview_controller import OverviewController

class OverviewScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.controller = OverviewController()
        self.init_ui()
        self.load_data_from_db()

    def init_ui(self):
        # Khu vực Tiêu đề 
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 15))
        ctk.CTkLabel(header, text="Bảng Điều Khiển Tổng Quan", font=(FONT_FAMILY, 28, "bold"), text_color=THEME_COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(header, text="Phân tích lớp học và thống kê giám sát theo thời gian thực", font=(FONT_FAMILY, 14), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(5,0))

        # Các thẻ thống kê (Stats Cards) 
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=30, pady=10)
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="equal")
        
        # Định nghĩa các biến Label lưu giá trị để cập nhật động
        self.lbl_total_sv = None
        self.lbl_present_sv = None
        self.lbl_focus_rate = None
        self.lbl_ai_alerts = None

        # Khởi tạo khung rỗng cho Stats
        self.setup_stats_cards_ui()

        # Khu vực Dữ liệu phía dưới 
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, padx=30, pady=(10, 20))
        bottom_frame.grid_rowconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=5, uniform="bottom_layout")
        bottom_frame.grid_columnconfigure(1, weight=5, uniform="bottom_layout")

        # --- CỘT TRÁI: DANH SÁCH SINH VIÊN TRONG CƠ SỞ DỮ LIỆU ---
        left_panel = CustomCard(bottom_frame)
        left_panel.grid(row=0, column=0, padx=10, sticky="nsew")
        ctk.CTkLabel(left_panel, text="DANH SÁCH SINH VIÊN TRONG DB", font=(FONT_FAMILY, 14, "bold"), text_color=THEME_COLORS["text_title"]).pack(anchor="w", padx=20, pady=15)
        
        # Khung cuộn chứa sinh viên
        self.sv_scroll_frame = ctk.CTkScrollableFrame(left_panel, fg_color=THEME_COLORS["bg_input"], corner_radius=8)
        self.sv_scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # --- CỘT PHẢI: LỊCH SỬ BUỔI HỌC ĐÃ DIỄN RA ---
        right_panel = CustomCard(bottom_frame)
        right_panel.grid(row=0, column=1, padx=10, sticky="nsew")
        ctk.CTkLabel(right_panel, text="LỊCH SỬ BUỔI HỌC ĐÃ DIỄN RA", font=(FONT_FAMILY, 14, "bold"), text_color=THEME_COLORS["text_title"]).pack(anchor="w", padx=20, pady=15)
        
        # Khung cuộn chứa danh sách các buổi học
        self.session_scroll_frame = ctk.CTkScrollableFrame(right_panel, fg_color=THEME_COLORS["bg_input"], corner_radius=8)
        self.session_scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _build_table_header(self, parent, columns):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(6, 8), padx=5)
        for index, (title, width, weight) in enumerate(columns):
            header.grid_columnconfigure(index, minsize=width, weight=weight)
            ctk.CTkLabel(
                header,
                text=title,
                font=(FONT_FAMILY, 12, "bold"),
                text_color=THEME_COLORS["text_muted"],
                anchor="w",
            ).grid(row=0, column=index, sticky="ew", padx=(0, 10))

    def _add_student_row(self, student_id, name, class_name):
        row = ctk.CTkFrame(self.sv_scroll_frame, fg_color="transparent")
        row.pack(fill="x", pady=4, padx=5)
        row.grid_columnconfigure(0, minsize=90, weight=0)
        row.grid_columnconfigure(1, minsize=160, weight=1)
        row.grid_columnconfigure(2, minsize=80, weight=0)
        row.grid_columnconfigure(3, minsize=120, weight=0)

        ctk.CTkLabel(row, text=str(student_id), font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_main"], anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(row, text=str(name), font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_main"], anchor="w").grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(row, text=str(class_name), font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"], anchor="w").grid(row=0, column=2, sticky="ew", padx=(0, 10))

        action_frame = ctk.CTkFrame(row, fg_color="transparent")
        action_frame.grid(row=0, column=3, sticky="ew")
        ctk.CTkButton(
            action_frame, text="Sửa", width=50, height=28, font=(FONT_FAMILY, 11),
            fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
            command=lambda sid=student_id: self.open_edit_student_dialog(sid)
        ).pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            action_frame, text="Xóa", width=50, height=28, font=(FONT_FAMILY, 11),
            fg_color=THEME_COLORS["danger"], hover_color="#B91C1C",
            command=lambda sid=student_id, sname=name: self.handle_delete_student(sid, sname)
        ).pack(side="left")

    def _add_session_row(self, session_id, title, date, time_range):
        row = ctk.CTkFrame(
            self.session_scroll_frame,
            fg_color="transparent",
            height=40,
            corner_radius=6,
        )
        row.pack(fill="x", pady=4, padx=5)
        row.pack_propagate(False)
        row.grid_columnconfigure(0, minsize=210, weight=1)
        row.grid_columnconfigure(1, minsize=95, weight=0)
        row.grid_columnconfigure(2, minsize=120, weight=0)

        widgets = [
            ctk.CTkLabel(row, text=str(title), font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_main"], anchor="w"),
            ctk.CTkLabel(row, text=str(date), font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"], anchor="w"),
            ctk.CTkLabel(row, text=str(time_range), font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"], anchor="w"),
        ]
        widgets[0].grid(row=0, column=0, sticky="ew", padx=(8, 10), pady=8)
        widgets[1].grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=8)
        widgets[2].grid(row=0, column=2, sticky="ew", pady=8)

        command = lambda _event: self.show_session_details(session_id, title, date)
        row.bind("<Button-1>", command)
        for widget in widgets:
            widget.bind("<Button-1>", command)

    def setup_stats_cards_ui(self):
        """Khởi tạo cấu trúc giao diện tĩnh cho các Thẻ Thống Kê"""
        titles = ["TỔNG SINH VIÊN", "CÓ MẶT (BUỔI CUỐI)", "TỶ LỆ CHUYÊN CẦN", "CẢNH BÁO AI"]
        colors = [THEME_COLORS["text_main"], THEME_COLORS["success_text"], THEME_COLORS["text_title"], THEME_COLORS["warning"]]
        
        cards = []
        for i in range(4):
            card = CustomCard(self.stats_frame)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            ctk.CTkLabel(card, text=titles[i], font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(15, 5))
            
            val_frame = ctk.CTkFrame(card, fg_color="transparent")
            val_frame.pack(fill="x", padx=20, pady=(0, 15))
            
            lbl_val = ctk.CTkLabel(val_frame, text="--", font=(FONT_FAMILY, 32, "bold"), text_color=colors[i])
            lbl_val.pack(side="left")
            cards.append(lbl_val)
            
        self.lbl_total_sv, self.lbl_present_sv, self.lbl_focus_rate, self.lbl_ai_alerts = cards
    
    def load_data_from_db(self):
        """Tải dữ liệu từ Controller và hiển thị lên UI"""
        for widget in self.sv_scroll_frame.winfo_children():
            widget.destroy()
        for widget in self.session_scroll_frame.winfo_children():
            widget.destroy()

        # 1. Tải dữ liệu vào các thẻ thông kê
        stats = self.controller.get_stats_data()
        self.lbl_total_sv.configure(text=stats["total"])
        self.lbl_present_sv.configure(text=stats["present"])
        self.lbl_focus_rate.configure(text=stats["rate"])
        self.lbl_ai_alerts.configure(text=stats["alerts"])

        # 2. Tải dữ liệu danh sách Sinh viên
        self._build_table_header(
            self.sv_scroll_frame,
            [("Mã SV", 90, 0), ("Họ và tên", 160, 1), ("Lớp", 80, 0), ("Hành động", 120, 0)]
        )
        students = self.controller.load_all_students()
        for mssv, name, class_name in students:
            self._add_student_row(mssv, name, class_name)

        # 3. Tải dữ liệu danh sách Buổi học
        self._build_table_header(
            self.session_scroll_frame,
            [("Bài giảng", 210, 1), ("Ngày", 95, 0), ("Thời gian", 120, 0)]
        )
        sessions = self.controller.load_all_sessions()
        for s_id, title, date, room in sessions:
            self._add_session_row(s_id, title, date, room)

    def refresh_and_load_data(self):
        self.load_data_from_db()

    # ===================== XỬ LÝ XÓA SINH VIÊN =====================
    def handle_delete_student(self, student_id, student_name):
        """Xác nhận và xóa sinh viên khỏi hệ thống"""
        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa sinh viên:\n\n"
            f"MSSV: {student_id}\nHọ tên: {student_name}\n\n"
            f"Toàn bộ dữ liệu điểm danh và trạng thái học tập\n"
            f"liên quan sẽ bị xóa vĩnh viễn!"
        )
        if not confirm:
            return

        result = self.controller.handle_delete_student(student_id)
        if result["status"] == "success":
            messagebox.showinfo("Thành công", result["message"])
            self.load_data_from_db()
        else:
            messagebox.showerror("Lỗi", result["message"])

    # ===================== XỬ LÝ SỬA SINH VIÊN =====================
    def open_edit_student_dialog(self, student_id):
        """Mở cửa sổ chỉnh sửa thông tin sinh viên"""
        student = self.controller.get_student_by_id(student_id)
        if not student:
            messagebox.showerror("Lỗi", f"Không tìm thấy sinh viên có MSSV: {student_id}")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Chỉnh sửa: {student['full_name']}")
        dialog.geometry("500x620")
        dialog.configure(fg_color=THEME_COLORS["bg_main"])
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        card = CustomCard(dialog)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card, text=f"Chỉnh Sửa Sinh Viên: {student_id}",
            font=(FONT_FAMILY, 20, "bold"), text_color=THEME_COLORS["text_title"]
        ).pack(anchor="w", padx=25, pady=(20, 15))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=25)

        entries = {}
        fields = [
            ("full_name", "Họ và Tên", student["full_name"]),
            ("class_name", "Lớp", student["class_name"] or ""),
            ("email", "Email", student["email"]),
            ("phone", "Số Điện Thoại", student["phone"] or ""),
        ]
        for key, label, value in fields:
            ctk.CTkLabel(form, text=label, font=(FONT_FAMILY, 12, "bold"),
                         text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(8, 3))
            entry = ctk.CTkEntry(
                form, fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"],
                text_color=THEME_COLORS["text_main"], height=42, font=(FONT_FAMILY, 14)
            )
            entry.pack(fill="x")
            if value:
                entry.insert(0, value)
            entries[key] = entry

        # Biến lưu đường dẫn ảnh mới
        new_image_path = {"value": None}

        img_frame = ctk.CTkFrame(form, fg_color="transparent")
        img_frame.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(img_frame, text="Ảnh chân dung (tùy chọn)", font=(FONT_FAMILY, 12, "bold"),
                     text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(0, 3))

        lbl_img_status = ctk.CTkLabel(img_frame, text="Giữ nguyên ảnh cũ",
                                       font=(FONT_FAMILY, 12), text_color=THEME_COLORS["text_muted"])
        lbl_img_status.pack(side="left", padx=(0, 10))

        def browse_new_image():
            path = filedialog.askopenfilename(
                title="Chọn ảnh mới",
                filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
            )
            if path:
                import os
                new_image_path["value"] = path
                lbl_img_status.configure(text=os.path.basename(path), text_color=THEME_COLORS["success_text"])

        ctk.CTkButton(
            img_frame, text="Đổi ảnh", width=90, height=32, font=(FONT_FAMILY, 12),
            fg_color=THEME_COLORS["bg_dark"], text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_card_hover"], command=browse_new_image
        ).pack(side="right")

        # Nút hành động
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(15, 20))

        def submit_edit():
            result = self.controller.handle_update_student(
                student_id=student_id,
                full_name=entries["full_name"].get(),
                class_name=entries["class_name"].get(),
                email=entries["email"].get(),
                phone=entries["phone"].get(),
                new_image_path=new_image_path["value"],
            )
            if result["status"] == "success":
                messagebox.showinfo("Thành công", result["message"], parent=dialog)
                dialog.grab_release()
                dialog.destroy()
                self.load_data_from_db()
            else:
                messagebox.showerror("Lỗi", result["message"], parent=dialog)

        ctk.CTkButton(
            btn_frame, text="Hủy", width=100, height=42,
            fg_color=THEME_COLORS["bg_dark"], text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_card_hover"],
            command=lambda: (dialog.grab_release(), dialog.destroy())
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Lưu thay đổi", width=140, height=42,
            font=(FONT_FAMILY, 14, "bold"),
            fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
            command=submit_edit
        ).pack(side="right")

    def show_session_details(self, session_id, session_title, session_date):
        """Mở cửa sổ hiển thị chi tiết điểm danh từ database dựa vào session_id"""
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Chi tiết: {session_title}")
        detail_window.geometry("750x500")
        detail_window.configure(fg_color=THEME_COLORS["bg_main"])
        detail_window.transient(self.winfo_toplevel())  # Chỉ đè lên cửa sổ chính của app
        detail_window.grab_set()  # Ngăn chặn click ra ngoài, tránh mở đè nhiều cửa sổ
        detail_window.focus_set()

        # Khung thông tin buổi học
        info_frame = CustomCard(detail_window)
        info_frame.pack(fill="x", padx=20, pady=15)
        
        info_header = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_header.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(info_header, text=f"Bài học: {session_title}", font=(FONT_FAMILY, 16, "bold"), text_color=THEME_COLORS["text_title"]).pack(side="left")
        
        # Nút xuất CSV
        def export_csv():
            file_path = filedialog.asksaveasfilename(
                title="Lưu báo cáo điểm danh",
                defaultextension=".csv",
                initialfile=f"DiemDanh_{session_id}_{session_date}.csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if not file_path:
                return
            
            try:
                # Lấy dữ liệu mới nhất
                data = self.controller.get_session_attendance_details(session_id)
                with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    # Ghi Header
                    writer.writerow(["MSSV", "Họ và tên", "Điểm danh", "Trạng thái AI"])
                    # Ghi dữ liệu
                    for mssv, name, status, ai_state in data:
                        status_text = status if status else "Vắng mặt"
                        ai_state_text = ai_state if ai_state else "Không có dữ liệu"
                        writer.writerow([mssv, name, status_text, ai_state_text])
                
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo thành công tại:\n{file_path}", parent=detail_window)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất báo cáo:\n{e}", parent=detail_window)

        ctk.CTkButton(
            info_header, text="Xuất CSV", width=90, height=30, font=(FONT_FAMILY, 12, "bold"),
            fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
            command=export_csv
        ).pack(side="right")

        ctk.CTkLabel(info_frame, text=f"Thời gian: {session_date} | ID phiên học: {session_id}", font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(0, 15))

        # Khung danh sách điểm danh
        list_card = CustomCard(detail_window)
        list_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        attendance_scroll = ctk.CTkScrollableFrame(list_card, fg_color=THEME_COLORS["bg_input"], corner_radius=8)
        attendance_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._build_table_header(
            attendance_scroll,
            [("MSSV", 95, 0), ("Họ và tên", 220, 1), ("Điểm danh", 100, 0), ("Trạng thái AI", 130, 0)]
        )

        # Gọi Controller lấy dữ liệu điểm danh thật của buổi học này từ DB
        attendance_data = self.controller.get_session_attendance_details(session_id)

        for mssv, name, status, ai_state in attendance_data:
            # Xử lý dữ liệu Null nếu học sinh vắng hoặc chưa có dữ liệu điểm danh
            status = status if status else "Vắng mặt"
            ai_state = ai_state if ai_state else "Không có dữ liệu"

            # Thiết lập màu sắc tương ứng với trạng thái
            status_color = THEME_COLORS["success_text"] if status == "Có mặt" else THEME_COLORS["danger"]
            
            if ai_state == "Tập trung":
                ai_color = THEME_COLORS["success_text"]
            elif "ngủ" in ai_state.lower() or "gục" in ai_state.lower():
                ai_color = THEME_COLORS["danger"]
            elif "mất tập trung" in ai_state.lower():
                ai_color = THEME_COLORS["warning"]
            else:
                ai_color = THEME_COLORS["text_muted"]

            row = ctk.CTkFrame(attendance_scroll, fg_color="transparent")
            row.pack(fill="x", pady=6, padx=5)
            row.grid_columnconfigure(0, minsize=95, weight=0)
            row.grid_columnconfigure(1, minsize=220, weight=1)
            row.grid_columnconfigure(2, minsize=100, weight=0)
            row.grid_columnconfigure(3, minsize=130, weight=0)

            ctk.CTkLabel(row, text=mssv, font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_main"], anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(row, text=name, font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_main"], anchor="w").grid(row=0, column=1, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(row, text=status, font=(FONT_FAMILY, 13, "bold"), text_color=status_color, anchor="w").grid(row=0, column=2, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(row, text=ai_state, font=(FONT_FAMILY, 13, "bold"), text_color=ai_color, anchor="w").grid(row=0, column=3, sticky="ew")
