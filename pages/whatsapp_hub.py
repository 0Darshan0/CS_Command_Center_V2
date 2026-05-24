import customtkinter as ctk
import threading
import sys
import os
import subprocess
import queue
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLORS, FONT

class WhatsAppHub(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.controller = controller
        self.message_queue = queue.Queue()
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ==========================================
        # TOP TOOLBAR & NAVIGATION
        # ==========================================
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=40, pady=(40, 20))
        
        # Titles
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="WhatsApp Hub", font=(FONT, 28, "bold"), text_color=COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(title_box, text="AI communications engine", font=(FONT, 13), text_color=COLORS["text_dim"]).pack(anchor="w")

        # macOS Style Segmented Control
        self.nav_var = ctk.StringVar(value="Morning Digest")
        self.nav_menu = ctk.CTkSegmentedButton(
            self.header_frame, 
            values=["Morning Digest", "AI Co-Pilot", "Broadcaster"],
            variable=self.nav_var,
            command=self.switch_view,
            font=(FONT, 13, "bold"),
            fg_color=COLORS["card"],
            selected_color=COLORS["accent"],
            selected_hover_color="#005ecb",
            unselected_color=COLORS["card"],
            unselected_hover_color="#2c2c2e",
            height=35
        )
        self.nav_menu.pack(side="right", pady=10)

        # ==========================================
        # MAIN WORKSPACE CONTAINERS
        # ==========================================
        # We create 3 separate frames, but only show the active one.
        self.frame_digest = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_copilot = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_broadcast = ctk.CTkFrame(self, fg_color="transparent")

        self.build_digest_view()
        self.build_copilot_view()
        self.build_broadcast_view()

        # Show initial view
        self.switch_view("Morning Digest")
        self.check_queue()

    def switch_view(self, view_name):
        """Hides all frames and maps the selected one gracefully."""
        self.frame_digest.grid_forget()
        self.frame_copilot.grid_forget()
        self.frame_broadcast.grid_forget()

        if view_name == "Morning Digest":
            self.frame_digest.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 40))
        elif view_name == "AI Co-Pilot":
            self.frame_copilot.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 40))
        elif view_name == "Broadcaster":
            self.frame_broadcast.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 40))

    # ==========================================
    # VIEW 1: MORNING DIGEST (Clean Text Focus)
    # ==========================================
    def build_digest_view(self):
        self.frame_digest.grid_columnconfigure(0, weight=1)
        self.frame_digest.grid_rowconfigure(1, weight=1)

        # Action Bar
        action_bar = ctk.CTkFrame(self.frame_digest, fg_color="transparent", height=50)
        action_bar.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        self.btn_digest = ctk.CTkButton(
            action_bar, text="Run Morning Digest", font=(FONT, 13, "bold"),
            fg_color=COLORS["accent"], hover_color="#005ecb", height=36, corner_radius=6,
            command=self.start_digest
        )
        self.btn_digest.pack(side="left")
        
        self.status_digest = ctk.CTkLabel(action_bar, text="Idle", font=(FONT, 13), text_color=COLORS["text_dim"])
        self.status_digest.pack(side="left", padx=15)

        # Premium Textbox Area
        self.out_digest = ctk.CTkTextbox(
            self.frame_digest, font=(FONT, 14), fg_color=COLORS["card"], 
            text_color=COLORS["text_main"], wrap="word", corner_radius=12
        )
        self.out_digest.grid(row=1, column=0, sticky="nsew")
        self.out_digest.insert("0.0", "Your AI summary will appear here.")
        self.out_digest.configure(state="disabled")

    # ==========================================
    # VIEW 2: AI CO-PILOT (Master-Detail Inbox)
    # ==========================================
    def build_copilot_view(self):
        self.frame_copilot.grid_columnconfigure(0, weight=1)
        self.frame_copilot.grid_rowconfigure(1, weight=1)

        # Action Bar
        action_bar = ctk.CTkFrame(self.frame_copilot, fg_color="transparent", height=50)
        action_bar.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        self.btn_scan = ctk.CTkButton(
            action_bar, text="Scan Inbox for Mentions", font=(FONT, 13, "bold"),
            fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"], 
            hover_color="#2c2c2e", height=36, corner_radius=6, text_color=COLORS["text_main"],
            command=self.start_scan
        )
        self.btn_scan.pack(side="left")
        
        self.status_copilot = ctk.CTkLabel(action_bar, text="Idle", font=(FONT, 13), text_color=COLORS["text_dim"])
        self.status_copilot.pack(side="left", padx=15)

        # Split View for Copilot (Logs on left, Drafts on right)
        split_frame = ctk.CTkFrame(self.frame_copilot, fg_color="transparent")
        split_frame.grid(row=1, column=0, sticky="nsew")
        split_frame.grid_columnconfigure(0, weight=1)
        
        # Clean Drafts Inbox
        self.copilot_scroll = ctk.CTkScrollableFrame(split_frame, fg_color="transparent")
        self.copilot_scroll.grid(row=0, column=0, sticky="nsew")
        
        self.load_copilot_drafts_to_ui()

    # ==========================================
    # VIEW 3: BROADCASTER (Centered Form)
    # ==========================================
    def build_broadcast_view(self):
        self.frame_broadcast.grid_columnconfigure(0, weight=1)
        self.frame_broadcast.grid_rowconfigure(0, weight=1)

        # Centered Container to prevent inputs from stretching too wide
        form_container = ctk.CTkFrame(self.frame_broadcast, fg_color="transparent", width=600)
        form_container.grid(row=0, column=0, sticky="n", pady=40)
        form_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form_container, text="Target Groups", font=(FONT, 13, "bold"), text_color=COLORS["text_dim"]).pack(anchor="w", pady=(0, 5))
        self.entry_groups = ctk.CTkEntry(
            form_container, placeholder_text="CS Test Group 1, CS Test Group 2", 
            height=40, fg_color=COLORS["card"], border_width=0, corner_radius=8, width=600
        )
        self.entry_groups.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(form_container, text="Broadcast Message", font=(FONT, 13, "bold"), text_color=COLORS["text_dim"]).pack(anchor="w", pady=(0, 5))
        self.text_message = ctk.CTkTextbox(
            form_container, font=(FONT, 14), fg_color=COLORS["card"], border_width=0, corner_radius=8, height=150, width=600
        )
        self.text_message.pack(fill="x", pady=(0, 25))

        self.btn_broadcast = ctk.CTkButton(
            form_container, text="Launch Broadcast", font=(FONT, 14, "bold"), 
            fg_color=COLORS["accent"], hover_color="#005ecb", height=45, corner_radius=8, 
            command=self.start_broadcast, width=600
        )
        self.btn_broadcast.pack(fill="x")
        
        self.status_broadcast = ctk.CTkLabel(form_container, text="", font=(FONT, 13), text_color=COLORS["text_dim"])
        self.status_broadcast.pack(pady=10)

    # ==========================================
    # DRAFTS UI BUILDER (Sleek Chat Bubbles)
    # ==========================================
    def load_copilot_drafts_to_ui(self):
        for widget in self.copilot_scroll.winfo_children():
            widget.destroy()
            
        drafts_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "whatsapp_engine", "copilot_drafts.json")
        
        if os.path.exists(drafts_file):
            try:
                with open(drafts_file, "r") as f:
                    drafts = json.load(f)
            except:
                drafts = []
                
            if drafts:
                for d in drafts:
                    # Premium Card Style
                    card = ctk.CTkFrame(self.copilot_scroll, fg_color=COLORS["card"], corner_radius=12)
                    card.pack(fill="x", pady=(0, 15), padx=5)
                    
                    header = ctk.CTkFrame(card, fg_color="transparent")
                    header.pack(fill="x", padx=20, pady=(15, 5))
                    ctk.CTkLabel(header, text=d['group'], font=(FONT, 14, "bold"), text_color=COLORS["text_main"]).pack(side="left")
                    
                    txt = ctk.CTkTextbox(card, height=60, font=(FONT, 14), fg_color=COLORS["card"], text_color=COLORS["text_dim"], border_width=0)
                    txt.pack(fill="x", padx=15, pady=5)
                    txt.insert("0.0", d['draft'])
                    
                    btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                    btn_frame.pack(fill="x", padx=20, pady=(5, 15))
                    
                    # Professional Action Buttons
                    btn_send = ctk.CTkButton(
                        btn_frame, text="Approve & Send", font=(FONT, 12, "bold"), width=120, height=32, corner_radius=6,
                        fg_color=COLORS["success"], hover_color="#28a745",
                        command=lambda g=d['group'], t=txt: self.send_single_draft(g, t.get("1.0", "end-1c"))
                    )
                    btn_send.pack(side="left", padx=(0, 10))
                    
                    # Ghost Button for Discard (Looks much cleaner)
                    btn_discard = ctk.CTkButton(
                        btn_frame, text="Discard", font=(FONT, 12), width=80, height=32, corner_radius=6,
                        fg_color="transparent", border_width=1, border_color=COLORS["urgent"], text_color=COLORS["urgent"], hover_color="#2c1a1d",
                        command=lambda g=d['group']: self.discard_draft(g)
                    )
                    btn_discard.pack(side="left")
                return

        # Empty State
        empty_lbl = ctk.CTkLabel(self.copilot_scroll, text="No pending drafts.", font=(FONT, 14), text_color=COLORS["text_dim"])
        empty_lbl.pack(pady=40)

    # ==========================================
    # LOGIC EXECUTORS (Same as before)
    # ==========================================
    def send_single_draft(self, group_name, message):
        if not message.strip(): return
        payload_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "whatsapp_engine", "broadcast_payload.json")
        with open(payload_path, "w") as f:
            json.dump({"groups": [group_name], "message": message}, f)

        self.message_queue.put(("UI_TOGGLE", "disabled"))
        self.message_queue.put(("COPILOT_STATUS", (f"Sending to {group_name}...", COLORS["warning"])))
        threading.Thread(target=self.run_subprocess, args=("broadcaster.py", "COPILOT_LOG", "COPILOT_STATUS"), daemon=True).start()
        self.discard_draft(group_name)

    def discard_draft(self, group_name):
        drafts_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "whatsapp_engine", "copilot_drafts.json")
        if os.path.exists(drafts_file):
            with open(drafts_file, "r") as f:
                drafts = json.load(f)
            drafts = [d for d in drafts if d["group"] != group_name]
            with open(drafts_file, "w") as f:
                json.dump(drafts, f)
            self.load_copilot_drafts_to_ui()

    def check_queue(self):
        while not self.message_queue.empty():
            msg_type, content = self.message_queue.get()
            
            if msg_type == "DIGEST_LOG": self.update_textbox(self.out_digest, content)
            elif msg_type == "DIGEST_STATUS": self.status_digest.configure(text=content[0], text_color=content[1])
            elif msg_type == "CLEAR_DIGEST": self.clear_textbox(self.out_digest)
            
            elif msg_type == "COPILOT_STATUS": self.status_copilot.configure(text=content[0], text_color=content[1])
            elif msg_type == "LOAD_DRAFTS": self.load_copilot_drafts_to_ui()
            
            elif msg_type == "BROADCAST_STATUS": self.status_broadcast.configure(text=content[0], text_color=content[1])
            
            elif msg_type == "UI_TOGGLE":
                state = content
                self.btn_digest.configure(state=state)
                self.btn_scan.configure(state=state)
                self.btn_broadcast.configure(state=state)

        self.after(100, self.check_queue)

    def update_textbox(self, textbox, text):
        textbox.configure(state="normal")
        textbox.insert("end", f"\n{text}")
        textbox.see("end")
        textbox.configure(state="disabled")

    def clear_textbox(self, textbox):
        textbox.configure(state="normal")
        textbox.delete("0.0", "end")
        textbox.configure(state="disabled")

    def run_subprocess(self, script_name, log_key, status_key, callback=None):
        try:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_path = os.path.join(root_dir, "whatsapp_engine", script_name)
            process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=root_dir)
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    clean_line = line.strip('\n')
                    if "Sending context" in clean_line or "Analyzing" in clean_line:
                        self.message_queue.put((status_key, (f"AI Processing...", COLORS["accent"])))
                    self.message_queue.put((log_key, clean_line))
            
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                self.message_queue.put((status_key, ("Complete", COLORS["success"])))
                if callback: self.message_queue.put((callback, None)) 
            else:
                self.message_queue.put((status_key, ("Failed", COLORS["urgent"])))
        except Exception as e:
            self.message_queue.put((log_key, f"\nError: {e}"))
            self.message_queue.put((status_key, ("Failed", COLORS["urgent"])))
        finally:
            self.message_queue.put(("UI_TOGGLE", "normal"))

    # ==========================================
    # TRIGGERS
    # ==========================================
    def start_digest(self):
        self.message_queue.put(("UI_TOGGLE", "disabled"))
        self.message_queue.put(("DIGEST_STATUS", ("Scraping...", COLORS["warning"])))
        self.message_queue.put(("CLEAR_DIGEST", None))
        threading.Thread(target=self.run_subprocess, args=("morning_digest.py", "DIGEST_LOG", "DIGEST_STATUS"), daemon=True).start()

    def start_scan(self):
        self.message_queue.put(("UI_TOGGLE", "disabled"))
        self.message_queue.put(("COPILOT_STATUS", ("Scanning...", COLORS["warning"])))
        threading.Thread(target=self.run_subprocess, args=("copilot_watcher.py", "COPILOT_LOG", "COPILOT_STATUS", "LOAD_DRAFTS"), daemon=True).start()

    def start_broadcast(self):
        groups_raw = self.entry_groups.get()
        message = self.text_message.get("1.0", "end-1c")
        if not groups_raw or not message.strip():
            self.message_queue.put(("BROADCAST_STATUS", ("Please fill all fields.", COLORS["warning"])))
            return

        group_list = [g.strip() for g in groups_raw.split(",") if g.strip()]
        payload_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "whatsapp_engine", "broadcast_payload.json")
        with open(payload_path, "w") as f:
            json.dump({"groups": group_list, "message": message}, f)

        self.message_queue.put(("UI_TOGGLE", "disabled"))
        self.message_queue.put(("BROADCAST_STATUS", ("Broadcasting...", COLORS["warning"])))
        threading.Thread(target=self.run_subprocess, args=("broadcaster.py", "BROADCAST_LOG", "BROADCAST_STATUS"), daemon=True).start()