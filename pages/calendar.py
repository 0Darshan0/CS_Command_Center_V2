import customtkinter as ctk
import config
import webbrowser
import re
import datetime
import calendar

# Apple starts the week on Sunday
calendar.setfirstweekday(calendar.SUNDAY)

class CalendarPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.selected_event = None
        self.view_date = self.controller.data.get("selected_date", datetime.date.today())
        
    def update_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        # --- RESPONSIVE GRID LAYOUT ---
        self.grid_columnconfigure(0, weight=1, uniform="top_row") 
        self.grid_columnconfigure(1, weight=1, uniform="top_row") 
        self.grid_rowconfigure(0, weight=0)    # Row 0: Header
        self.grid_rowconfigure(1, weight=1)    # Row 1: Top Half (Cal & List)
        self.grid_rowconfigure(2, weight=1)    # Row 2: Bottom Half (Details)

        actual_selected_date = self.controller.data.get("selected_date", datetime.date.today())
        events = self.controller.data.get("events",[])
        today_date = datetime.date.today()

        # ==========================================
        # PAGE HEADER (Row 0)
        # ==========================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        ctk.CTkLabel(header_frame, text="Calendar", font=ctk.CTkFont(family=config.FONT, size=32, weight="bold"), text_color="#FFFFFF").pack(side="left")

        # ==========================================
        # TOP-LEFT: ELASTIC APPLE CALENDAR (Row 1, Col 0)
        # ==========================================
        cal_pane = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=15)
        cal_pane.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        
        cal_header = ctk.CTkFrame(cal_pane, fg_color="transparent")
        cal_header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkButton(cal_header, text="<", width=30, fg_color="transparent", hover_color="#2C2C2E", 
                      font=ctk.CTkFont(family=config.FONT, size=22), text_color=config.COLORS["accent"], 
                      command=self.prev_month).pack(side="left")
        
        month_str = self.view_date.strftime("%B %Y")
        ctk.CTkLabel(cal_header, text=month_str, font=ctk.CTkFont(family=config.FONT, size=20, weight="bold")).pack(side="left", expand=True)
        
        ctk.CTkButton(cal_header, text=">", width=30, fg_color="transparent", hover_color="#2C2C2E", 
                      font=ctk.CTkFont(family=config.FONT, size=22), text_color=config.COLORS["accent"], 
                      command=self.next_month).pack(side="right")

        # Responsive Grid Container
        grid_frame = ctk.CTkFrame(cal_pane, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        for i in range(7):
            grid_frame.grid_columnconfigure(i, weight=1)
        for i in range(7): 
            grid_frame.grid_rowconfigure(i, weight=1)

        days =["S", "M", "T", "W", "T", "F", "S"]
        for i, day in enumerate(days):
            ctk.CTkLabel(grid_frame, text=day, font=ctk.CTkFont(family=config.FONT, size=13, weight="bold"), 
                         text_color=config.COLORS["text_dim"]).grid(row=0, column=i)

        month_days = calendar.monthcalendar(self.view_date.year, self.view_date.month)
        for row_idx, week in enumerate(month_days):
            for col_idx, day in enumerate(week):
                if day != 0:
                    is_selected = (day == actual_selected_date.day and 
                                   self.view_date.month == actual_selected_date.month and 
                                   self.view_date.year == actual_selected_date.year)
                    is_today = (day == today_date.day and 
                                self.view_date.month == today_date.month and 
                                self.view_date.year == today_date.year)
                    
                    if is_selected:
                        bg_color = config.COLORS["urgent"]
                        txt_color = "#FFFFFF"
                    else:
                        bg_color = "transparent"
                        txt_color = config.COLORS["urgent"] if is_today else "#E5E5EA"
                        
                    weight = "bold" if is_selected or is_today else "normal"
                    
                    btn = ctk.CTkButton(grid_frame, text=str(day), width=36, height=36, corner_radius=18, 
                                        fg_color=bg_color, hover_color="#2C2C2E", 
                                        text_color=txt_color, font=ctk.CTkFont(family=config.FONT, size=16, weight=weight),
                                        command=lambda d=day: self.on_date_click(d))
                    btn.grid(row=row_idx+1, column=col_idx)

        # ==========================================
        # TOP-RIGHT: SCHEDULE LIST (Row 1, Col 1)
        # ==========================================
        list_pane = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=15)
        list_pane.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))
        
        list_header = ctk.CTkFrame(list_pane, fg_color="transparent")
        list_header.pack(fill="x", padx=25, pady=(20, 5))
        
        date_str = actual_selected_date.strftime("%A, %B %d")
        ctk.CTkLabel(list_header, text=date_str, font=ctk.CTkFont(family=config.FONT, size=20, weight="bold"), 
                     text_color="#FFFFFF").pack(side="left")
        
        if events:
            ctk.CTkLabel(list_header, text=f"{len(events)} Events", font=ctk.CTkFont(family=config.FONT, size=13), 
                         text_color=config.COLORS["accent"]).pack(side="right", pady=5)

        list_scroll = ctk.CTkScrollableFrame(list_pane, fg_color="transparent")
        list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        if not events:
            ctk.CTkLabel(list_scroll, text="No events scheduled.", font=ctk.CTkFont(family=config.FONT, size=15), text_color=config.COLORS["text_dim"]).pack(pady=40)
        else:
            if not self.selected_event: self.selected_event = events[0]
            for event in events:
                self.create_event_row(list_scroll, event)

        # ==========================================
        # BOTTOM: FULL-WIDTH READING PANE (Row 2)
        # ==========================================
        self.render_event_details()

    def prev_month(self):
        first_day = self.view_date.replace(day=1)
        self.view_date = first_day - datetime.timedelta(days=1)
        self.update_ui()

    def next_month(self):
        if self.view_date.month == 12:
            self.view_date = self.view_date.replace(year=self.view_date.year+1, month=1, day=1)
        else:
            self.view_date = self.view_date.replace(month=self.view_date.month+1, day=1)
        self.update_ui()

    def on_date_click(self, day):
        new_date = datetime.date(self.view_date.year, self.view_date.month, day)
        self.selected_event = None 
        self.controller.fetch_all_data(target_date=new_date)

    def create_event_row(self, parent, event):
        summary = event.get('summary', 'No Title')
        start = event['start'].get('dateTime', event['start'].get('date'))
        time_only = start.split('T')[1][:5] if 'T' in start else "All Day"
        
        dot_color = config.COLORS["accent"]
        low = summary.lower()
        if "onboard" in low: dot_color = config.COLORS["success"]
        elif "training" in low or "demo" in low: dot_color = config.COLORS["warning"]
        elif "issue" in low or "urgent" in low: dot_color = config.COLORS["urgent"]

        is_selected = (self.selected_event == event)
        bg_color = "#2C2C2E" if is_selected else "transparent"
        
        row = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=10, cursor="hand2")
        row.pack(fill="x", pady=2, padx=5)
        
        ctk.CTkLabel(row, text="●", text_color=dot_color, font=ctk.CTkFont(size=14)).pack(side="left", padx=(15, 8), pady=12)
        ctk.CTkLabel(row, text=time_only, font=ctk.CTkFont(family=config.FONT, size=13, weight="bold" if is_selected else "normal")).pack(side="left")
        ctk.CTkLabel(row, text=summary, font=ctk.CTkFont(family=config.FONT, size=13), anchor="w").pack(side="left", fill="x", expand=True, padx=15)

        for child in row.winfo_children():
            child.bind("<Button-1>", lambda e, ev=event: self.select_event(ev))
        row.bind("<Button-1>", lambda e, ev=event: self.select_event(ev))

    def select_event(self, event):
        self.selected_event = event
        self.update_ui()

    def render_event_details(self):
        bottom_pane = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=15)
        # Shifted to Row 2!
        bottom_pane.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        
        if not self.selected_event:
            ctk.CTkLabel(bottom_pane, text="Select an event to view details", font=ctk.CTkFont(family=config.FONT, size=16), text_color=config.COLORS["text_dim"]).pack(expand=True)
            return
            
        event = self.selected_event
        title = event.get('summary', 'No Title')
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        try:
            start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
            time_str = f"{start_dt.strftime('%A, %b %d')}  |  {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
        except:
            time_str = "All Day Event"

        meet_link = event.get('hangoutLink', event.get('htmlLink', ''))
        raw_desc = event.get('description', 'No additional details provided.')
        clean_desc = re.sub(r'<[^>]+>', '', raw_desc).replace("&nbsp;", " ").strip()

        header_frame = ctk.CTkFrame(bottom_pane, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(30, 10))
        
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)
        
        title_lbl = ctk.CTkTextbox(title_box, fg_color="transparent", font=ctk.CTkFont(family=config.FONT, size=26, weight="bold"), text_color="#FFFFFF", wrap="word", height=35)
        title_lbl.pack(fill="x")
        title_lbl.insert("0.0", title)
        title_lbl.configure(state="disabled")
        
        ctk.CTkLabel(title_box, text=time_str, font=ctk.CTkFont(family=config.FONT, size=14), text_color=config.COLORS["accent"], anchor="w").pack(fill="x", pady=(5, 0))

        if meet_link:
            ctk.CTkButton(header_frame, text="📹 Join Video Call", font=ctk.CTkFont(family=config.FONT, size=14, weight="bold"), 
                          fg_color=config.COLORS["accent"], hover_color="#0070DF", height=40, corner_radius=8,
                          command=lambda: webbrowser.open(meet_link)).pack(side="right", padx=20)

        ctk.CTkFrame(bottom_pane, height=1, fg_color=config.COLORS["border"]).pack(fill="x", padx=40, pady=10)

        desc_box = ctk.CTkTextbox(bottom_pane, fg_color="transparent", font=(config.FONT, 15), text_color="#E5E5EA", border_width=0, wrap="word")
        desc_box.pack(fill="both", expand=True, padx=35, pady=(10, 30))
        desc_box.insert("0.0", clean_desc)
        desc_box.configure(state="disabled")