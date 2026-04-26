import customtkinter as ctk
import config

class TasksPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
    def update_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Task Management", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        # ADD TASK UI
        add_frame = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=15)
        add_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(add_frame, text="New task", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.task_entry = ctk.CTkEntry(add_frame, placeholder_text="Task description...", height=40, fg_color="#0f172a")
        self.task_entry.pack(fill="x", padx=20, pady=5)
        
        controls = ctk.CTkFrame(add_frame, fg_color="transparent")
        controls.pack(fill="x", padx=20, pady=(5, 15))
        
        self.date_entry = ctk.CTkEntry(controls, placeholder_text="Due date (e.g. Apr 30)", width=200, fg_color="#0f172a")
        self.date_entry.pack(side="left")
        
        self.priority_menu = ctk.CTkOptionMenu(controls, values=["low", "medium", "high"], fg_color="#0f172a", button_color="#334155")
        self.priority_menu.pack(side="left", padx=10)
        
        ctk.CTkButton(controls, text="Add task", width=120, fg_color=config.COLORS["accent"], command=self.add_task).pack(side="right")

        # LIST TASKS
        list_card = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=15)
        list_card.pack(fill="both", expand=True)
        
        pending_count = len([t for t in self.controller.data["tasks"] if not t["done"]])
        ctk.CTkLabel(list_card, text=f"All tasks ({pending_count} pending)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=15)

        scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        for i, task in enumerate(self.controller.data["tasks"]):
            self.create_task_row(scroll, task, i)

    def create_task_row(self, parent, task, index):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)
        
        # Fix: ensure the toggle command passes the correct index
        cb = ctk.CTkCheckBox(row, text="", width=20, command=lambda i=index: self.toggle_task(i))
        if task["done"]: cb.select()
        cb.pack(side="left", padx=(10, 15))
        
        text_color = config.COLORS["text_dim"] if task["done"] else "white"
        lbl = ctk.CTkLabel(row, text=task["desc"], font=ctk.CTkFont(size=14), text_color=text_color, anchor="w")
        lbl.pack(side="left", fill="x", expand=True)

        p_colors = {"high": config.COLORS["urgent"], "medium": config.COLORS["warning"], "low": config.COLORS["success"]}
        badge = ctk.CTkFrame(row, fg_color="#1e293b", border_width=1, border_color=p_colors[task["priority"]], corner_radius=6)
        badge.pack(side="right", padx=15)
        ctk.CTkLabel(badge, text=task["priority"].upper(), text_color=p_colors[task["priority"]], font=ctk.CTkFont(size=9, weight="bold"), padx=10).pack(pady=2)

        ctk.CTkLabel(row, text=task["date"], font=ctk.CTkFont(size=12), text_color=config.COLORS["text_dim"], width=60).pack(side="right")
        ctk.CTkFrame(parent, height=1, fg_color="#2d3748").pack(fill="x", padx=10)

    def add_task(self):
        desc = self.task_entry.get()
        date = self.date_entry.get()
        priority = self.priority_menu.get()
        if desc:
            new_task = {"desc": desc, "date": date if date else "Today", "priority": priority, "done": False}
            self.controller.data["tasks"].insert(0, new_task)
            self.controller.save_tasks() # Save to file
            self.update_ui()
            self.task_entry.delete(0, 'end')
            self.date_entry.delete(0, 'end')

    def toggle_task(self, index):
        self.controller.data["tasks"][index]["done"] = not self.controller.data["tasks"][index]["done"]
        self.controller.save_tasks() # Save change to file
        self.update_ui()