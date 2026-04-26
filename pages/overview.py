import customtkinter as ctk
from tkcalendar import Calendar
import config
from datetime import datetime

class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
    def update_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        
        # 1. HEADER & KPI ROW
        ctk.CTkLabel(self, text="Dashboard", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 20))

        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 10))
        
        def clean_currency(val):
            val = str(val)
            return val if "₹" in val else f"₹{val}"

        # KPI CARDS
        self.create_card(kpi_row, "SUBSCRIPTION", clean_currency(self.controller.data.get("sub_achieved", "0")), config.COLORS["accent"])
        self.create_card(kpi_row, "TOP-UP/RECH", clean_currency(self.controller.data.get("topup_achieved", "0")), config.COLORS["warning"])
        
        # Calculate % and Gap
        achieved_val = float(str(self.controller.data.get("achieved", "0")).replace('₹', '').replace(',', '').strip() or 0)
        target_val = float(str(self.controller.data.get("target", "300000")).replace('₹', '').replace(',', '').strip() or 300000)
        percent = (achieved_val / target_val) * 100 if target_val > 0 else 0
        gap = target_val - achieved_val
        
        self.create_card(kpi_row, "TOTAL ACHIEVED", clean_currency(self.controller.data.get("achieved", "0")), config.COLORS["success"], f"{percent:.1f}% of goal")
        self.create_card(kpi_row, "MONTHLY TARGET", clean_currency(self.controller.data.get("target", "300,000")), "#ffffff", f"₹{gap:,.0f} to go")

        # 2. MAIN CONTENT SPLIT
        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.pack(fill="both", expand=True, pady=10)
        split_frame.grid_columnconfigure(0, weight=1) 
        split_frame.grid_columnconfigure(1, weight=1) 

        # --- LEFT: RENEWALS ---
        ren_card = ctk.CTkFrame(split_frame, fg_color=config.COLORS["card"], corner_radius=15)
        ren_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(ren_card, text="Pending Renewals", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        rows = self.controller.data.get("renewal_list", [])
        if not rows:
            ctk.CTkLabel(ren_card, text="No renewals found.", text_color=config.COLORS["text_dim"]).pack(pady=20)
        else:
            for r in rows[:6]:
                if len(r) > 4:
                    item = ctk.CTkFrame(ren_card, fg_color="transparent")
                    item.pack(fill="x", padx=20, pady=5)
                    ctk.CTkLabel(item, text=r[1], font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
                    ctk.CTkLabel(item, text=clean_currency(r[4]), text_color=config.COLORS["text_dim"]).pack(side="right")
                    ctk.CTkFrame(ren_card, height=1, fg_color="#2d3748").pack(fill="x", padx=20)

        # --- RIGHT: INTERACTIVE CALENDAR & AGENDA ---
        self.render_calendar_panel(split_frame)

    def render_calendar_panel(self, parent):
        cal_card = ctk.CTkFrame(parent, fg_color=config.COLORS["card"], corner_radius=15)
        cal_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        selected_d = self.controller.data.get("selected_date")
        ctk.CTkLabel(cal_card, text=selected_d.strftime("%B %Y"), font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 5))

        # Fixed height for calendar to prevent it from pushing meetings out
        self.cal_widget = Calendar(cal_card, background=config.COLORS["card"], foreground='white', 
                                   selectbackground=config.COLORS["accent"], borderwidth=0)
        self.cal_widget.pack(fill="x", padx=20, pady=5) 
        self.cal_widget.selection_set(selected_d)
        self.cal_widget.bind("<<CalendarSelected>>", self.on_date_click)

        # AGENDA HEADER
        ctk.CTkLabel(cal_card, text="Today's Agenda", font=ctk.CTkFont(size=14, weight="bold"), 
                     text_color=config.COLORS["accent"]).pack(anchor="w", padx=25, pady=(10, 0))

        # AGENDA LIST (Scrollable sub-area)
        events = self.controller.data.get("events", [])
        preview_frame = ctk.CTkScrollableFrame(cal_card, fg_color="transparent", height=150)
        preview_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        if not events:
            ctk.CTkLabel(preview_frame, text="No meetings scheduled", font=ctk.CTkFont(size=12), text_color=config.COLORS["text_dim"]).pack(pady=20)
        else:
            for e in events:
                summary = e.get('summary', 'Meeting')
                start = e['start'].get('dateTime', e['start'].get('date'))
                time_only = start.split('T')[1][:5] if 'T' in start else "--:--"
                
                row = ctk.CTkFrame(preview_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=time_only, font=ctk.CTkFont(size=11, weight="bold"), width=50).pack(side="left")
                ctk.CTkLabel(row, text=summary, font=ctk.CTkFont(size=12), anchor="w", wraplength=200).pack(side="left", padx=10)

    def on_date_click(self, event):
        selected_date = self.cal_widget.selection_get()
        self.controller.fetch_all_data(target_date=selected_date)

    def create_card(self, parent, label, val, color, subtext="view details →"):
        card = ctk.CTkFrame(parent, fg_color=config.COLORS["card"], height=100)
        card.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(pady=(15,0), padx=15, anchor="w")
        ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=24, weight="bold"), text_color=color).pack(padx=15, anchor="w")
        ctk.CTkLabel(card, text=subtext, font=ctk.CTkFont(size=10), text_color="#94a3b8").pack(pady=(0, 15), padx=15, anchor="w")