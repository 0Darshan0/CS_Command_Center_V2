import customtkinter as ctk
from tkcalendar import DateEntry
import config
import datetime

class CalendarPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
    def update_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        # Header Row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="Smart Schedule", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        # Date Selection Controls
        self.date_picker = DateEntry(header, width=12, background=config.COLORS["accent"], foreground='white', borderwidth=2)
        self.date_picker.set_date(self.controller.data["selected_date"])
        self.date_picker.pack(side="right", padx=10)
        
        ctk.CTkButton(header, text="Go to Date", width=100, fg_color=config.COLORS["accent"], 
                      command=self.change_date).pack(side="right")

        # Meeting Count Label
        events = self.controller.data.get("events", [])
        ctk.CTkLabel(self, text=f"Showing {len(events)} events for {self.controller.data['selected_date']}", 
                     text_color=config.COLORS["text_dim"]).pack(anchor="w", pady=(0, 10))

        # Events Scroll Area
        scroll = ctk.CTkScrollableFrame(self, fg_color=config.COLORS["card"], corner_radius=12)
        scroll.pack(fill="both", expand=True)

        if not events:
            ctk.CTkLabel(scroll, text="No meetings found for this date.", pady=60).pack()
        else:
            for event in events:
                summary = event.get('summary', 'No Title')
                start = event['start'].get('dateTime', event['start'].get('date'))
                time_only = start.split('T')[1][:5] if 'T' in start else "ALL DAY"
                
                tag, t_color = "ACTIVE", config.COLORS["accent"]
                low = summary.lower()
                if "onboard" in low: tag, t_color = "ONBOARDING", config.COLORS["success"]
                elif "training" in low or "demo" in low: tag, t_color = "TRAINING", config.COLORS["warning"]
                elif "issue" in low or "urgent" in low: tag, t_color = "URGENT", config.COLORS["urgent"]

                self.create_event_tile(scroll, time_only, summary, tag, t_color)

    def change_date(self):
        new_date = self.date_picker.get_date()
        self.controller.fetch_all_data(target_date=new_date)

    def create_event_tile(self, parent, time, title, tag, t_color):
        item = ctk.CTkFrame(parent, fg_color="#1e293b", height=70)
        item.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(item, text=time, font=ctk.CTkFont(size=14, weight="bold"), width=80).pack(side="left", padx=15)
        badge = ctk.CTkFrame(item, fg_color="transparent", border_width=1, border_color=t_color, corner_radius=6)
        badge.pack(side="left", padx=10)
        ctk.CTkLabel(badge, text=tag, text_color=t_color, font=ctk.CTkFont(size=10, weight="bold"), padx=10).pack(pady=2)
        ctk.CTkLabel(item, text=title, font=ctk.CTkFont(size=14)).pack(side="left", padx=20)