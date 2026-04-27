import customtkinter as ctk
import config
import datetime
import calendar

calendar.setfirstweekday(calendar.SUNDAY)

class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.view_date = self.controller.data.get("selected_date", datetime.date.today())
        
        # --- 1. BUILD THE SKELETON (Only happens once!) ---
        self.setup_ui()
        
    def setup_ui(self):
        """Builds all the containers and labels so they never have to be destroyed"""
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(self.main_scroll, text="Overview", font=ctk.CTkFont(family=config.FONT, size=32, weight="bold"), text_color="#FFFFFF").pack(anchor="w", pady=(0, 20), padx=5)

        # TIER 1: KPIs
        kpi_row = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 15))
        
        self.lbl_sub = self.create_kpi_card(kpi_row, "SUBSCRIPTION", config.COLORS["accent"], "Recurring")
        self.lbl_topup = self.create_kpi_card(kpi_row, "TOP-UP/RECH", config.COLORS["warning"], "One-time")
        self.lbl_total, self.lbl_total_sub = self.create_kpi_card(kpi_row, "TOTAL ACHIEVED", config.COLORS["success"], "0% of goal", return_sub=True)
        self.lbl_target, self.lbl_target_sub = self.create_kpi_card(kpi_row, "MONTHLY TARGET", "#FFFFFF", "₹0 to go", return_sub=True)

        # TIER 2: ACTION CENTER
        action_row = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        action_row.pack(fill="x", pady=15)
        action_row.grid_columnconfigure((0,1,2), weight=1, uniform="action")

        self.task_card = self.create_widget_card(action_row, "Priority Tasks", 0)
        self.ren_card = self.create_widget_card(action_row, "Upcoming Renewals", 1)
        self.health_card = self.create_widget_card(action_row, "System Status", 2)

        # TIER 3: FLOW
        flow_row = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        flow_row.pack(fill="x", pady=15)
        flow_row.grid_columnconfigure((0,1), weight=1, uniform="flow")

        cal_card = ctk.CTkFrame(flow_row, fg_color=config.COLORS["card"], corner_radius=15)
        cal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.setup_calendar_widget(cal_card)

        ai_card = ctk.CTkFrame(flow_row, fg_color=config.COLORS["card"], corner_radius=15)
        ai_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(ai_card, text="Quick AI Dropzone", font=ctk.CTkFont(family=config.FONT, size=16, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(ai_card, text="Paste notes here to jump straight to the Churn Predictor.", font=ctk.CTkFont(family=config.FONT, size=12), text_color=config.COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(0, 15))
        self.quick_ai_input = ctk.CTkTextbox(ai_card, height=200, fg_color=config.COLORS["bg"], border_width=0, corner_radius=10, font=ctk.CTkFont(family=config.FONT, size=14))
        self.quick_ai_input.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        ctk.CTkButton(ai_card, text="Analyze in Churn Predictor →", font=ctk.CTkFont(family=config.FONT, size=14, weight="bold"), height=40, corner_radius=8, fg_color=config.COLORS["accent"], hover_color="#0070DF", command=self.jump_to_ai).pack(fill="x", padx=20, pady=(0, 20))

    # --- 2. UPDATE THE FLESH (Happens smoothly on click!) ---
    def update_ui(self):
        self.view_date = self.controller.data.get("selected_date", datetime.date.today())
        
        # Update KPIs
        achieved_val = float(str(self.controller.data.get("achieved", "0")).replace('₹', '').replace(',', '').strip() or 0)
        target_val = float(str(self.controller.data.get("target", "300000")).replace('₹', '').replace(',', '').strip() or 300000)
        
        self.lbl_sub.configure(text=self.clean_currency(self.controller.data.get("sub_achieved", "0")))
        self.lbl_topup.configure(text=self.clean_currency(self.controller.data.get("topup_achieved", "0")))
        self.lbl_total.configure(text=self.clean_currency(self.controller.data.get("achieved", "0")))
        self.lbl_target.configure(text=self.clean_currency(self.controller.data.get("target", "300000")))

        percent = (achieved_val / target_val) * 100 if target_val > 0 else 0
        gap = target_val - achieved_val
        self.lbl_total_sub.configure(text=f"{percent:.1f}% of goal")
        self.lbl_target_sub.configure(text=f"₹{gap:,.0f} to go" if gap > 0 else "Target Smashed! 🏆")

        # Update Tasks (Only destroy inner list, not the whole card)
        for w in self.task_card.winfo_children(): w.destroy()
        pending_tasks =[t for t in self.controller.data.get("tasks", []) if not t.get("done")]
        if not pending_tasks:
            ctk.CTkLabel(self.task_card, text="All caught up! 🎉", text_color=config.COLORS["text_dim"]).pack(pady=20)
        else:
            for t in pending_tasks[:3]:
                row = ctk.CTkFrame(self.task_card, fg_color="transparent")
                row.pack(fill="x", pady=5)
                ctk.CTkLabel(row, text="○", font=ctk.CTkFont(size=16), text_color=config.COLORS["text_dim"]).pack(side="left", padx=(0, 10))
                ctk.CTkLabel(row, text=t["desc"], font=ctk.CTkFont(family=config.FONT, size=13), anchor="w").pack(side="left", fill="x", expand=True)

        # Update Renewals
        for w in self.ren_card.winfo_children(): w.destroy()
        valid_rows = [r for r in self.controller.data.get("renewal_list",[]) if len(r) > 4]
        if not valid_rows:
            ctk.CTkLabel(self.ren_card, text="No renewals found.", text_color=config.COLORS["text_dim"]).pack(pady=20)
        else:
            for r in valid_rows[:3]:
                row = ctk.CTkFrame(self.ren_card, fg_color="transparent")
                row.pack(fill="x", pady=5)
                ctk.CTkLabel(row, text=r[1], font=ctk.CTkFont(family=config.FONT, size=13, weight="bold")).pack(side="left")
                ctk.CTkLabel(row, text=self.clean_currency(r[4]), text_color=config.COLORS["text_dim"], font=ctk.CTkFont(family=config.FONT, size=12)).pack(side="right")

        # Update System Status
        for w in self.health_card.winfo_children(): w.destroy()
        ctk.CTkLabel(self.health_card, text="Everything is running smoothly.", text_color=config.COLORS["text_dim"], font=ctk.CTkFont(family=config.FONT, size=12)).pack(anchor="w", pady=(0, 15))
        self.create_status_row(self.health_card, "Google Sheets")
        self.create_status_row(self.health_card, "Google Calendar")

        # Update Calendar Grid
        self.cal_month_lbl.configure(text=self.view_date.strftime("%B %Y"))
        for w in self.cal_grid_frame.winfo_children():
            if int(w.grid_info()["row"]) > 0: w.destroy() # Keep Headers, delete numbers

        actual_selected_date = self.controller.data.get("selected_date", datetime.date.today())
        today_date = datetime.date.today()
        month_days = calendar.monthcalendar(self.view_date.year, self.view_date.month)
        
        for row_idx, week in enumerate(month_days):
            for col_idx, day in enumerate(week):
                if day != 0:
                    is_sel = (day == actual_selected_date.day and self.view_date.month == actual_selected_date.month and self.view_date.year == actual_selected_date.year)
                    is_today = (day == today_date.day and self.view_date.month == today_date.month and self.view_date.year == today_date.year)
                    
                    bg_color = config.COLORS["urgent"] if is_sel else "transparent"
                    txt_color = "#FFFFFF" if is_sel else config.COLORS["urgent"] if is_today else "#E5E5EA"
                    weight = "bold" if is_sel or is_today else "normal"
                    
                    btn = ctk.CTkButton(self.cal_grid_frame, text=str(day), width=30, height=30, corner_radius=15, fg_color=bg_color, hover_color="#2C2C2E", text_color=txt_color, font=ctk.CTkFont(family=config.FONT, size=13, weight=weight), command=lambda d=day: self.on_date_click(d))
                    btn.grid(row=row_idx+1, column=col_idx, padx=1, pady=1)

        # Update Agenda
        for w in self.agenda_frame.winfo_children(): w.destroy()
        events = self.controller.data.get("events", [])[:3]
        if not events:
            ctk.CTkLabel(self.agenda_frame, text="No events today.", text_color=config.COLORS["text_dim"], font=ctk.CTkFont(family=config.FONT, size=12)).pack(pady=10)
        else:
            for e in events:
                ctk.CTkLabel(self.agenda_frame, text=f"● {e.get('summary', 'Event')}", text_color="#cbd5e1", font=ctk.CTkFont(family=config.FONT, size=12), anchor="w").pack(fill="x", pady=2)

    # --- UI HELPERS ---
    def setup_calendar_widget(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(20, 10))
        
        self.cal_month_lbl = ctk.CTkLabel(top_bar, text="", font=ctk.CTkFont(family=config.FONT, size=18, weight="bold"))
        self.cal_month_lbl.pack(side="left")
        
        controls = ctk.CTkFrame(top_bar, fg_color="transparent")
        controls.pack(side="right")
        ctk.CTkButton(controls, text="<", width=25, fg_color="transparent", text_color=config.COLORS["accent"], command=self.prev_month).pack(side="left")
        ctk.CTkButton(controls, text=">", width=25, fg_color="transparent", text_color=config.COLORS["accent"], command=self.next_month).pack(side="left")

        self.cal_grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.cal_grid_frame.pack(fill="x", padx=15, pady=(0, 15))
        for i in range(7): self.cal_grid_frame.grid_columnconfigure(i, weight=1)
        for i, day in enumerate(["S", "M", "T", "W", "T", "F", "S"]):
            ctk.CTkLabel(self.cal_grid_frame, text=day, font=ctk.CTkFont(family=config.FONT, size=11, weight="bold"), text_color=config.COLORS["text_dim"]).grid(row=0, column=i, pady=(0, 5))

        ctk.CTkFrame(parent, height=1, fg_color=config.COLORS["border"]).pack(fill="x", padx=20, pady=5)
        self.agenda_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.agenda_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def create_kpi_card(self, parent, label, color, subtext, return_sub=False):
        card = ctk.CTkFrame(parent, fg_color=config.COLORS["card"], height=110, corner_radius=12)
        card.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(family=config.FONT, size=11, weight="bold"), text_color=config.COLORS["text_dim"]).pack(pady=(15,0), padx=15, anchor="w")
        val_lbl = ctk.CTkLabel(card, text="₹0", font=ctk.CTkFont(family=config.FONT, size=26, weight="bold"), text_color=color)
        val_lbl.pack(padx=15, pady=(2, 2), anchor="w")
        sub_lbl = ctk.CTkLabel(card, text=subtext, font=ctk.CTkFont(family=config.FONT, size=11), text_color=config.COLORS["text_dim"])
        sub_lbl.pack(padx=15, anchor="w")
        if return_sub: return val_lbl, sub_lbl
        return val_lbl

    def create_widget_card(self, parent, title, col):
        card = ctk.CTkFrame(parent, fg_color=config.COLORS["card"], corner_radius=15)
        card.grid(row=0, column=col, sticky="nsew", padx=5)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family=config.FONT, size=16, weight="bold")).pack(anchor="w", padx=20, pady=(20, 15))
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        return content
        
    def create_status_row(self, parent, text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(family=config.FONT, size=13)).pack(side="left")
        ctk.CTkLabel(row, text="● SYNCED", text_color=config.COLORS["success"], font=ctk.CTkFont(size=10, weight="bold")).pack(side="right")

    def clean_currency(self, val):
        val = str(val).strip()
        if not val or val == "N/A": return "₹0"
        return val if "₹" in val else f"₹{val}"

    def prev_month(self):
        self.view_date = (self.view_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        self.update_ui()

    def next_month(self):
        m, y = self.view_date.month, self.view_date.year
        self.view_date = self.view_date.replace(year=y+1, month=1, day=1) if m == 12 else self.view_date.replace(month=m+1, day=1)
        self.update_ui()

    def on_date_click(self, day):
        new_date = datetime.date(self.view_date.year, self.view_date.month, day)
        self.controller.fetch_all_data(target_date=new_date)

    def jump_to_ai(self):
        notes = self.quick_ai_input.get("0.0", "end").strip()
        if notes:
            self.controller.pages["ChurnAnalyzerPage"].ai_input.delete("0.0", "end")
            self.controller.pages["ChurnAnalyzerPage"].ai_input.insert("0.0", notes)
        self.controller.show_page("ChurnAnalyzerPage")