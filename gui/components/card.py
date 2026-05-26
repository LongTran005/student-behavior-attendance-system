# gui/components/card.py
import customtkinter as ctk
from gui.theme import THEME_COLORS

class CustomCard(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        # Lấy giá trị mặc định, cho phép override nếu cần
        fg_color = kwargs.pop("fg_color", THEME_COLORS["bg_card"])
        border_color = kwargs.pop("border_color", THEME_COLORS["border"])
        border_width = kwargs.pop("border_width", 1)
        corner_radius = kwargs.pop("corner_radius", 12)
        
        super().__init__(
            parent,
            fg_color=fg_color,
            border_color=border_color,
            border_width=border_width,
            corner_radius=corner_radius,
            **kwargs
        )