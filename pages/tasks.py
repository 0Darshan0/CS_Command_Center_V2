import customtkinter as ctk
import config
import threading

class TasksPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.draft_data = {"date": "", "location": "", "tags": "", "flagged": False}
        
    def update_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        # ==========================================
        # 🍎 APPLE REMINDERS HEADER
        # ==========================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=25, pady=(20, 5))
        
        # CHANGED: Title to Task Tracker
        ctk.CTkLabel(header_frame, text="Task Tracker", font=ctk.CTkFont(family=config.FONT, size=36, weight="bold"), text_color=config.COLORS["accent"]).pack(side="left")
        
        pending_count = len([t for t in self.controller.data.get("tasks", []) if not t.get("done", False)])
        ctk.CTkLabel(header_frame, text=str(pending_count), font=ctk.CTkFont(family=config.FONT, size=36, weight="bold"), text_color=config.COLORS["accent"]).pack(side="right")

        # --- SUB-HEADER (Completed & Clear) ---
        sub_frame = ctk.CTkFrame(self, fg_color="transparent")
        sub_frame.pack(fill="x", padx=25, pady=(0, 15))
        
        completed_count = len([t for t in self.controller.data.get("tasks", []) if t.get("done", False)])
        ctk.CTkLabel(sub_frame, text=f"{completed_count} Completed  • ", font=ctk.CTkFont(family=config.FONT, size=13, weight="bold"), text_color=config.COLORS["text_dim"]).pack(side="left")
        
        ctk.CTkButton(sub_frame, text="Clear Completed", font=ctk.CTkFont(family=config.FONT, size=13), fg_color="transparent", text_color=config.COLORS["accent"], hover_color=config.COLORS["card"], width=40, command=self.clear_completed).pack(side="left")

        # --- MAIN LIST CONTAINER (Borderless) ---
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10)

        # ==========================================
        # 1. INLINE INPUT ROW (The Apple Way)
        # ==========================================
        self.render_input_row(scroll)
        
        # Thick Divider separating input from existing tasks
        ctk.CTkFrame(scroll, height=1, fg_color=config.COLORS["border"]).pack(fill="x", padx=15, pady=15)

        # ==========================================
        # 2. EXISTING TASK LIST
        # ==========================================
        tasks = self.controller.data.get("tasks",[])
        for i, task in enumerate(tasks):
            self.create_task_row(scroll, task, i)

    def render_input_row(self, parent):
        input_frame = ctk.CTkFrame(parent, fg_color="transparent")
        input_frame.pack(fill="x", pady=5)

        # Left: Unclickable Circle
        circle = ctk.CTkCheckBox(input_frame, text="", width=24, height=24, corner_radius=12, border_width=2, state="disabled", border_color=config.COLORS["border"])
        circle.pack(side="left", anchor="n", padx=(15, 10), pady=5)

        # Middle: Vertical box holding Text and Chips
        vbox = ctk.CTkFrame(input_frame, fg_color="transparent")
        vbox.pack(side="left", fill="x", expand=True)

        # Title Input (Clear placeholder!)
        self.task_entry = ctk.CTkEntry(vbox, placeholder_text="New Task Title...", font=ctk.CTkFont(family=config.FONT, size=16), fg_color="transparent", border_width=0, text_color="#FFFFFF")
        self.task_entry.pack(fill="x")
        self.task_entry.bind("<Return>", lambda e: self.add_task())

        # Notes Input
        self.notes_entry = ctk.CTkEntry(vbox, placeholder_text="Notes...", font=ctk.CTkFont(family=config.FONT, size=14), fg_color="transparent", border_width=0, text_color=config.COLORS["text_dim"])
        self.notes_entry.pack(fill="x", pady=(0, 5))
        self.notes_entry.bind("<Return>", lambda e: self.add_task())

        # Chips Row
        self.chip_row = ctk.CTkFrame(vbox, fg_color="transparent")
        self.chip_row.pack(fill="x")

        self.date_btn = self.create_chip(self.chip_row, "🗓 Add Date", self.prompt_date)
        self.loc_btn = self.create_chip(self.chip_row, "📍 Add Location", self.prompt_loc)
        self.tag_btn = self.create_chip(self.chip_row, "# Add Tags", self.prompt_tag)
        self.flag_btn = self.create_chip(self.chip_row, "🚩", self.toggle_flag)
        
        # Right: The Add Button (Solves the "not saving" issue!)
        add_btn = ctk.CTkButton(input_frame, text="Add", font=ctk.CTkFont(family=config.FONT, size=13, weight="bold"), fg_color=config.COLORS["accent"], hover_color="#0070DF", width=60, height=30, corner_radius=8, command=self.add_task)
        add_btn.pack(side="right", anchor="n", padx=10, pady=5)

    def create_chip(self, parent, text, command):
        btn = ctk.CTkButton(parent, text=text, font=ctk.CTkFont(family=config.FONT, size=12), fg_color=config.COLORS["card"], hover_color="#2d3748", text_color=config.COLORS["text_dim"], corner_radius=6, height=24, command=command)
        btn.pack(side="left", padx=(0, 8))
        return btn

    # --- CHIP POPUP LOGIC ---
    def prompt_date(self):
        dialog = ctk.CTkInputDialog(text="Enter Due Date (e.g., Apr 30):", title="Add Date")
        val = dialog.get_input()
        if val:
            self.draft_data["date"] = val
            self.date_btn.configure(text=f"🗓 {val}", fg_color="#1A3B22", text_color=config.COLORS["success"])

    def prompt_loc(self):
        dialog = ctk.CTkInputDialog(text="Enter Location:", title="Add Location")
        val = dialog.get_input()
        if val:
            self.draft_data["location"] = val
            self.loc_btn.configure(text=f"📍 {val}", fg_color="#1A3B22", text_color=config.COLORS["success"])

    def prompt_tag(self):
        dialog = ctk.CTkInputDialog(text="Enter Tag (e.g. urgent):", title="Add Tag")
        val = dialog.get_input()
        if val:
            tag = f"#{val.replace('#', '')}"
            self.draft_data["tags"] = tag
            self.tag_btn.configure(text=tag, fg_color="#1A3B22", text_color=config.COLORS["success"])

    def toggle_flag(self):
        self.draft_data["flagged"] = not self.draft_data["flagged"]
        if self.draft_data["flagged"]:
            self.flag_btn.configure(fg_color="#4A1A1A", text_color=config.COLORS["urgent"])
        else:
            self.flag_btn.configure(fg_color=config.COLORS["card"], text_color=config.COLORS["text_dim"])

    # --- DISPLAY SAVED TASKS ---
    def create_task_row(self, parent, task, index):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        
        # Checkbox
        cb = ctk.CTkCheckBox(row, text="", width=24, height=24, corner_radius=12, border_width=2, 
                             border_color=config.COLORS["border"] if not task.get("done") else config.COLORS["success"], 
                             fg_color=config.COLORS["success"], hover_color=config.COLORS["success"],
                             command=lambda i=index: self.toggle_task(i))
        if task.get("done"): cb.select()
        cb.pack(side="left", anchor="n", padx=(15, 10), pady=2)
        
        # Main Info Vertical Box
        vbox = ctk.CTkFrame(row, fg_color="transparent")
        vbox.pack(side="left", fill="x", expand=True)

        text_color = config.COLORS["text_dim"] if task.get("done") else "#FFFFFF"
        is_overstrike = True if task.get("done") else False
        
        # Title
        ctk.CTkLabel(vbox, text=task.get("desc", ""), font=ctk.CTkFont(family=config.FONT, size=16, overstrike=is_overstrike), text_color=text_color, anchor="w").pack(fill="x")
        
        # Notes
        if task.get("notes"):
            ctk.CTkLabel(vbox, text=task["notes"], font=ctk.CTkFont(family=config.FONT, size=14), text_color=config.COLORS["text_dim"], anchor="w").pack(fill="x", pady=(2, 0))

        # Chips
        has_chips = task.get("date") or task.get("location") or task.get("tags") or task.get("flagged")
        if has_chips and not task.get("done"):
            chip_row = ctk.CTkFrame(vbox, fg_color="transparent")
            chip_row.pack(fill="x", pady=(5, 0))
            
            if task.get("date"):
                ctk.CTkLabel(chip_row, text=f"🗓 {task['date']}", font=ctk.CTkFont(family=config.FONT, size=12), text_color=config.COLORS["success"]).pack(side="left", padx=(0, 10))
            if task.get("location"):
                ctk.CTkLabel(chip_row, text=f"📍 {task['location']}", font=ctk.CTkFont(family=config.FONT, size=12), text_color=config.COLORS["text_dim"]).pack(side="left", padx=(0, 10))
            if task.get("tags"):
                ctk.CTkLabel(chip_row, text=task['tags'], font=ctk.CTkFont(family=config.FONT, size=12), text_color=config.COLORS["accent"]).pack(side="left", padx=(0, 10))
            if task.get("flagged"):
                ctk.CTkLabel(chip_row, text="🚩", font=ctk.CTkFont(family=config.FONT, size=12), text_color=config.COLORS["urgent"]).pack(side="left", padx=(0, 10))

        # --- THE DELETE BUTTON ---
        del_btn = ctk.CTkButton(row, text="✕", font=ctk.CTkFont(size=14, weight="bold"), width=30, height=30, fg_color="transparent", hover_color="#4A1A1A", text_color=config.COLORS["text_dim"], command=lambda i=index: self.delete_task(i))
        del_btn.pack(side="right", padx=10)

        # Subtle row divider
        ctk.CTkFrame(parent, height=1, fg_color=config.COLORS["border"]).pack(fill="x", padx=15)

    # --- DATA LOGIC ---
    def add_task(self):
        desc = self.task_entry.get().strip()
        notes = self.notes_entry.get().strip()
        
        if desc:
            new_task = {
                "desc": desc, 
                "notes": notes,
                "date": self.draft_data["date"], 
                "location": self.draft_data["location"],
                "tags": self.draft_data["tags"],
                "flagged": self.draft_data["flagged"],
                "done": False
            }
            self.controller.data["tasks"].insert(0, new_task)
            self.controller.save_tasks() 
            
            # Reset draft data
            self.draft_data = {"date": "", "location": "", "tags": "", "flagged": False}
            self.update_ui()
            self.sync_to_cloud() 

    def toggle_task(self, index):
        self.controller.data["tasks"][index]["done"] = not self.controller.data["tasks"][index]["done"]
        self.controller.save_tasks() 
        self.update_ui()
        self.sync_to_cloud() 

    def delete_task(self, index):
        """Deletes a specific task"""
        del self.controller.data["tasks"][index]
        self.controller.save_tasks()
        self.update_ui()
        self.sync_to_cloud()

    def clear_completed(self):
        self.controller.data["tasks"] = [t for t in self.controller.data["tasks"] if not t.get("done")]
        self.controller.save_tasks()
        self.update_ui()
        self.sync_to_cloud()

    # --- CLOUD SYNC LOGIC ---
    def sync_to_cloud(self):
        threading.Thread(target=self._push_to_sheets, daemon=True).start()

    def _push_to_sheets(self):
        try:
            service = self.controller.get_service('sheets', 'v4')
            sheet_id = config.CRM_SHEET_ID
            tab_name = "Reminders"

            sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheets = sheet_metadata.get('sheets', '')
            if not any(s.get("properties", {}).get("title") == tab_name for s in sheets):
                reqs =[{"addSheet": {"properties": {"title": tab_name}}}]
                service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": reqs}).execute()

            values = [["Task", "Notes", "Date", "Location", "Tags", "Flagged", "Status"]]
            for t in self.controller.data.get("tasks",[]):
                status = "Done" if t.get("done") else "Pending"
                values.append([
                    t.get("desc", ""), 
                    t.get("notes", ""), 
                    t.get("date", ""), 
                    t.get("location", ""), 
                    t.get("tags", ""), 
                    "Yes" if t.get("flagged") else "No", 
                    status
                ])

            service.spreadsheets().values().clear(spreadsheetId=sheet_id, range=f"'{tab_name}'!A:G").execute()
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id, range=f"'{tab_name}'!A1",
                valueInputOption="USER_ENTERED", body={"values": values}
            ).execute()
        except Exception as e:
            print(f"❌ Cloud Sync Error: {e}")