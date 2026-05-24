import customtkinter as ctk
import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.setup_ui()

    def setup_ui(self):
        # ==========================================
        # 1. HEADER 
        # ==========================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="Overview", font=(config.FONT, 34, "bold"), text_color=config.COLORS["text_main"]).pack(side="left")
        
        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        status_frame.pack(side="right", pady=10)
        
        self.lbl_sheet_status = ctk.CTkLabel(status_frame, text="● Sheets", font=(config.FONT, 12, "bold"), text_color=config.COLORS["success"])
        self.lbl_sheet_status.pack(side="left", padx=10)
        self.lbl_cal_status = ctk.CTkLabel(status_frame, text="● Calendar", font=(config.FONT, 12, "bold"), text_color=config.COLORS["success"])
        self.lbl_cal_status.pack(side="left", padx=10)

        # ==========================================
        # 2. KPI ROW 
        # ==========================================
        self.lbl_sub = self.create_kpi_card(1, 0, "SUBSCRIPTION", "Recurring", config.COLORS["text_main"])
        self.lbl_topup = self.create_kpi_card(1, 1, "TOP-UP / RECH", "One-time", config.COLORS["text_main"])
        self.lbl_total = self.create_kpi_card(1, 2, "TOTAL ACHIEVED", "Revenue", config.COLORS["accent"]) 
        self.lbl_target = self.create_kpi_card(1, 3, "MONTHLY TARGET", "Goal", config.COLORS["accent_light"]) 

        # ==========================================
        # 3. MIDDLE ROW (Stealth Scrollbars)
        # ==========================================
        self.tasks_frame = self.create_panel(2, 0, 2, "Priority Tasks")
        self.tasks_container = ctk.CTkScrollableFrame(
            self.tasks_frame, fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=config.COLORS["card"], 
            scrollbar_button_hover_color=config.COLORS["border"] 
        )
        self.tasks_container.pack(fill="both", expand=True, padx=15, pady=10)

        self.renewals_frame = self.create_panel(2, 2, 2, "Upcoming Renewals")
        self.renewals_container = ctk.CTkScrollableFrame(
            self.renewals_frame, fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=config.COLORS["card"],
            scrollbar_button_hover_color=config.COLORS["border"]
        )
        self.renewals_container.pack(fill="both", expand=True, padx=15, pady=10)

        # ==========================================
        # 4. BOTTOM ROW (Stealth Scrollbars)
        # ==========================================
        self.cal_frame = self.create_panel(3, 0, 2, "Today's Schedule")
        self.cal_container = ctk.CTkScrollableFrame(
            self.cal_frame, fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=config.COLORS["card"],
            scrollbar_button_hover_color=config.COLORS["border"]
        )
        self.cal_container.pack(fill="both", expand=True, padx=15, pady=10)

        self.launchpad_frame = self.create_panel(3, 2, 2, "Quick Launchpad")
        self.build_launchpad()

    # --- UI HELPERS ---
    def create_kpi_card(self, row, col, title, subtitle, value_color):
        card = ctk.CTkFrame(self, fg_color=config.COLORS["card"], height=110, corner_radius=12, border_width=1, border_color=config.COLORS["border"])
        card.grid(row=row, column=col, sticky="nsew", padx=10, pady=(0, 20))
        card.grid_propagate(False)
        
        ctk.CTkLabel(card, text=title, font=(config.FONT, 11, "bold"), text_color=config.COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(15, 0))
        lbl_val = ctk.CTkLabel(card, text="₹0", font=(config.FONT, 34, "bold"), text_color=value_color)
        lbl_val.pack(anchor="w", padx=20, pady=0)
        ctk.CTkLabel(card, text=subtitle, font=(config.FONT, 12), text_color=config.COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(0, 15))
        
        return lbl_val

    def create_panel(self, row, col, colspan, title):
        card = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=12, border_width=1, border_color=config.COLORS["border"])
        card.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=10, pady=10)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(header, text=title, font=(config.FONT, 18, "bold"), text_color=config.COLORS["text_main"]).pack(side="left")
        
        return card

    def build_launchpad(self):
        grid_frame = ctk.CTkFrame(self.launchpad_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        grid_frame.grid_columnconfigure((0, 1), weight=1)
        grid_frame.grid_rowconfigure((0, 1), weight=1)

        def create_shortcut(row, col, title, target_page):
            btn = ctk.CTkButton(
                grid_frame, text=title, font=(config.FONT, 14, "bold"),
                fg_color="transparent", text_color=config.COLORS["text_main"],
                border_width=1, border_color=config.COLORS["border"],
                hover_color=config.COLORS["surface_hover"], corner_radius=8, height=60,
                command=lambda p=target_page: self.controller.show_page(p)
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

        create_shortcut(0, 0, "WhatsApp Hub", "WhatsAppHub")
        create_shortcut(0, 1, "Churn Predictor", "ChurnAnalyzerPage")
        create_shortcut(1, 0, "AI Briefing", "AIPage")
        create_shortcut(1, 1, "Task Manager", "TasksPage")

    # ==========================================
    # DATA POPULATION LOGIC
    # ==========================================
    def update_ui(self):
        data = self.controller.data

        self.lbl_sub.configure(text=data.get("sub_achieved", "₹0"))
        self.lbl_topup.configure(text=data.get("topup_achieved", "₹0"))
        self.lbl_total.configure(text=data.get("achieved", "₹0"))
        
        target_val = data.get("target", "₹0")
        achieved_val = data.get("achieved", "₹0")
        
        try:
            ach_clean = float(achieved_val.replace("₹", "").replace(",", ""))
            tgt_clean = float(target_val.replace("₹", "").replace(",", ""))
            if ach_clean >= tgt_clean and tgt_clean > 0:
                self.lbl_target.configure(text=target_val, text_color=config.COLORS["success"])
            else:
                self.lbl_target.configure(text=target_val)
        except:
            self.lbl_target.configure(text=target_val)

        for widget in self.tasks_container.winfo_children(): widget.destroy()
        tasks = data.get("tasks", [])
        has_tasks = False
        for task in tasks:
            title = task.get('title', '').strip()
            if title:
                has_tasks = True
                ctk.CTkLabel(self.tasks_container, text=f"•  {title}", font=(config.FONT, 14), text_color=config.COLORS["text_main"]).pack(anchor="w", pady=6)
        if not has_tasks:
            ctk.CTkLabel(self.tasks_container, text="No pending tasks.", font=(config.FONT, 13), text_color=config.COLORS["text_dim"]).pack(pady=20)

        for widget in self.renewals_container.winfo_children(): widget.destroy()
        renewals = data.get("renewal_list", [])
        if renewals:
            for row in renewals[:6]: 
                if len(row) >= 6:
                    client_name = row[1]  
                    amount = row[5]       
                    
                    item_frame = ctk.CTkFrame(self.renewals_container, fg_color="transparent")
                    item_frame.pack(fill="x", pady=6)
                    ctk.CTkLabel(item_frame, text=client_name, font=(config.FONT, 14, "bold"), text_color=config.COLORS["text_main"]).pack(side="left")
                    ctk.CTkLabel(item_frame, text=amount, font=(config.FONT, 13), text_color=config.COLORS["text_dim"]).pack(side="right")
        else:
            ctk.CTkLabel(self.renewals_container, text="No upcoming renewals.", font=(config.FONT, 13), text_color=config.COLORS["text_dim"]).pack(pady=20)

        for widget in self.cal_container.winfo_children(): widget.destroy()
        events = data.get("events", [])
        if events:
            for event in events:
                summary = event.get('summary', 'Busy')
                start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
                time_str = "All Day"
                if 'T' in start:
                    try:
                        time_obj = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                        time_str = time_obj.strftime("%I:%M %p")
                    except: pass

                item_frame = ctk.CTkFrame(self.cal_container, fg_color="transparent")
                item_frame.pack(fill="x", pady=8)
                ctk.CTkLabel(item_frame, text=time_str, font=(config.FONT, 13, "bold"), text_color=config.COLORS["accent"], width=80, anchor="w").pack(side="left")
                ctk.CTkLabel(item_frame, text=summary, font=(config.FONT, 14), text_color=config.COLORS["text_main"]).pack(side="left", padx=10)
        else:
            ctk.CTkLabel(self.cal_container, text="No events scheduled for today.", font=(config.FONT, 13), text_color=config.COLORS["text_dim"]).pack(pady=20)