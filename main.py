import sys
import os
import datetime
import json

# --- APP PATH LOGIC ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = sys._MEIPASS 
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

sys.path.append(BUNDLE_DIR)
def get_path(filename): return os.path.join(BASE_DIR, filename)

import customtkinter as ctk
import config 
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# --- IMPORT ALL PAGES ---
from pages.overview import OverviewPage
from pages.renewals import RenewalsPage
from pages.calendar import CalendarPage
from pages.ai_briefing import AIPage
from pages.tasks import TasksPage
from pages.whatsapp_hub import WhatsAppHub
from pages.churn_analyzer import ChurnAnalyzerPage

class CSCommandOS(ctk.CTk):
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',       
        'https://www.googleapis.com/auth/calendar.readonly', 
        'https://www.googleapis.com/auth/drive.readonly'
    ]

    def __init__(self):
        super().__init__()
        
        self.title("CS COMMAND OS") 
        self.geometry("1400x900")
        self.configure(fg_color=config.COLORS["bg"])
        
        self.data = {
            "achieved": "₹0", "target": "₹0", "sub_achieved": "₹0", "topup_achieved": "₹0",
            "events": [], "renewal_list":[], "selected_date": datetime.date.today(), "tasks":[]
        }
        
        self.current_page = "OverviewPage" 
        self.nav_buttons = {}
        
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # 1. THE SIDEBAR
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=config.COLORS["sidebar"], corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", pady=(35, 20), padx=25)
        ctk.CTkLabel(brand_frame, text="CS COMMAND", font=(config.FONT, 18, "bold"), text_color=config.COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(brand_frame, text="Operating System V3", font=(config.FONT, 11), text_color=config.COLORS["text_dim"]).pack(anchor="w")

        self.search_btn = ctk.CTkButton(
            self.sidebar, text="🔍 Search...             ⌘K", font=(config.FONT, 12),
            fg_color=config.COLORS["card"], hover_color=config.COLORS["surface_hover"],
            text_color=config.COLORS["text_dim"], border_width=1, border_color=config.COLORS["border"],
            height=35, corner_radius=8, command=self.toggle_cmd_k
        )
        self.search_btn.pack(fill="x", padx=20, pady=(0, 20))

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(nav_frame, text="MAIN MENU", font=(config.FONT, 10, "bold"), text_color=config.COLORS["text_dim"]).pack(anchor="w", padx=25, pady=(0, 10))
        self.create_nav_btn("📊  Overview", "OverviewPage", nav_frame)
        self.create_nav_btn("📋  Tasks", "TasksPage", nav_frame)
        self.create_nav_btn("💰  Renewals", "RenewalsPage", nav_frame)
        self.create_nav_btn("🗓️  Calendar", "CalendarPage", nav_frame)
        
        ctk.CTkLabel(nav_frame, text="INTELLIGENCE", font=(config.FONT, 10, "bold"), text_color=config.COLORS["text_dim"]).pack(anchor="w", padx=25, pady=(25, 10))
        self.create_nav_btn("🚀  AI Briefing", "AIPage", nav_frame)
        self.create_nav_btn("🚨  Churn Predictor", "ChurnAnalyzerPage", nav_frame)
        self.create_nav_btn("💬  WhatsApp Hub", "WhatsAppHub", nav_frame)

        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=25, padx=20)
        
        self.sync_btn = ctk.CTkButton(
            bottom_frame, text="🔄 Sync System", font=(config.FONT, 13, "bold"), 
            fg_color="transparent", border_width=1, border_color=config.COLORS["border"], 
            text_color=config.COLORS["text_main"], hover_color=config.COLORS["surface_hover"],
            command=self.fetch_all_data, height=40, corner_radius=8
        )
        self.sync_btn.pack(fill="x")

        # ==========================================
        # 2. DIVIDER & MAIN CONTAINER
        # ==========================================
        divider = ctk.CTkFrame(self, width=1, fg_color=config.COLORS["border"], corner_radius=0)
        divider.grid(row=0, column=1, sticky="ns")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=2, sticky="nsew", padx=40, pady=40)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.pages = {}
        for PageClass in [OverviewPage, TasksPage, RenewalsPage, CalendarPage, AIPage, ChurnAnalyzerPage, WhatsAppHub]:
            page_name = PageClass.__name__
            frame = PageClass(parent=self.container, controller=self)
            self.pages[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # ==========================================
        # 3. CMD+K OVERLAY SETUP (FOCUS MODE)
        # ==========================================
        self.build_cmd_k_menu()
        
        self.bind_all("<Command-k>", self.toggle_cmd_k)
        self.bind_all("<Control-k>", self.toggle_cmd_k)
        self.bind_all("<Escape>", lambda e: self.close_cmd_k())
        self.bind_all("<Button-1>", self.check_click_outside)

        self.load_tasks()
        self.fetch_all_data()
        self.show_page(self.current_page)

    # ==========================================
    # CMD+K LOGIC (The Spotlight Search)
    # ==========================================
    def build_cmd_k_menu(self):
        self.cmd_k_is_open = False
        
        # Built directly into the main window
        self.cmd_k_frame = ctk.CTkFrame(
            self, width=650, height=450, fg_color=config.COLORS["sidebar"], 
            corner_radius=15, border_width=1, border_color=config.COLORS["accent"]
        )
        
        self.cmd_k_frame.grid_propagate(False)
        self.cmd_k_frame.pack_propagate(False)

        self.cmd_k_entry = ctk.CTkEntry(
            self.cmd_k_frame, font=(config.FONT, 20), placeholder_text="Search clients, tasks, or jump to page...", 
            fg_color=config.COLORS["card"], border_width=0, height=50, text_color=config.COLORS["text_main"]
        )
        self.cmd_k_entry.pack(fill="x", padx=20, pady=(20, 10))
        self.cmd_k_entry.bind("<KeyRelease>", self.on_cmd_k_type)

        self.cmd_k_results = ctk.CTkScrollableFrame(
            self.cmd_k_frame, fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=config.COLORS["sidebar"],
            scrollbar_button_hover_color=config.COLORS["accent"]
        )
        self.cmd_k_results.pack(fill="both", expand=True, padx=10, pady=(0, 20))

    def toggle_cmd_k(self, event=None):
        if self.cmd_k_is_open:
            self.close_cmd_k()
        else:
            # FOCUS MODE: Temporarily hide the main container to prevent UI bleeding
            self.container.grid_forget()
            
            # Show the Search Menu in the center of the right panel
            self.cmd_k_frame.place(relx=0.6, rely=0.4, anchor="center")
            self.cmd_k_frame.tkraise()
            
            self.cmd_k_entry.focus_set()
            self.cmd_k_entry.delete(0, "end")
            self.on_cmd_k_type() 
            self.cmd_k_is_open = True
            
    def close_cmd_k(self):
        if self.cmd_k_is_open:
            # Hide the Search Menu
            self.cmd_k_frame.place_forget()
            
            # Restore the main container!
            self.container.grid(row=0, column=2, sticky="nsew", padx=40, pady=40)
            
            self.cmd_k_is_open = False
            self.focus_set()

    def check_click_outside(self, event):
        if not self.cmd_k_is_open:
            return

        click_x = event.x_root
        click_y = event.y_root

        frame_x = self.cmd_k_frame.winfo_rootx()
        frame_y = self.cmd_k_frame.winfo_rooty()
        frame_w = self.cmd_k_frame.winfo_width()
        frame_h = self.cmd_k_frame.winfo_height()

        btn_x = self.search_btn.winfo_rootx()
        btn_y = self.search_btn.winfo_rooty()
        btn_w = self.search_btn.winfo_width()
        btn_h = self.search_btn.winfo_height()

        is_inside_frame = (frame_x <= click_x <= frame_x + frame_w) and (frame_y <= click_y <= frame_y + frame_h)
        is_inside_btn = (btn_x <= click_x <= btn_x + btn_w) and (btn_y <= click_y <= btn_y + btn_h)

        if not is_inside_frame and not is_inside_btn:
            self.close_cmd_k()

    def on_cmd_k_type(self, event=None):
        query = self.cmd_k_entry.get().lower().strip()
        
        for widget in self.cmd_k_results.winfo_children():
            widget.destroy()

        results_found = False

        pages_map = {
            "Overview Dashboard": "OverviewPage",
            "Task Manager": "TasksPage",
            "Upcoming Renewals": "RenewalsPage",
            "Calendar Schedule": "CalendarPage",
            "AI Briefing": "AIPage",
            "Churn Predictor": "ChurnAnalyzerPage",
            "WhatsApp Command Hub": "WhatsAppHub"
        }
        
        for ui_name, class_name in pages_map.items():
            if query in ui_name.lower():
                self.create_cmd_k_item(f"Go to: {ui_name}", "📁 Navigation", lambda p=class_name: self.jump_to_page(p))
                results_found = True

        renewals = self.data.get("renewal_list", [])
        for row in renewals:
            if len(row) >= 2:
                client_name = str(row[1])
                if query in client_name.lower() and client_name.strip() != "":
                    self.create_cmd_k_item(
                        f"Message {client_name}", "💬 WhatsApp Action", 
                        lambda c=client_name: self.jump_to_whatsapp(c)
                    )
                    results_found = True
                    
        if not results_found:
            ctk.CTkLabel(self.cmd_k_results, text="No results found.", text_color=config.COLORS["text_dim"]).pack(pady=20)

    def create_cmd_k_item(self, title, subtitle, command):
        btn = ctk.CTkButton(
            self.cmd_k_results, text=title, font=(config.FONT, 14, "bold"),
            fg_color="transparent", text_color=config.COLORS["text_main"],
            hover_color=config.COLORS["surface_hover"], anchor="w", height=45,
            command=command
        )
        btn.pack(fill="x", pady=2)
        btn.configure(text=f"{subtitle}   |   {title}")

    def jump_to_page(self, page_name):
        self.close_cmd_k()
        self.show_page(page_name)

    def jump_to_whatsapp(self, client_name):
        self.close_cmd_k()
        self.show_page("WhatsAppHub")
        hub = self.pages["WhatsAppHub"]
        hub.switch_view("Broadcaster")
        hub.entry_groups.delete(0, "end")
        hub.entry_groups.insert(0, f"{client_name} <> Cheerio")

    # ==========================================
    # DATA LOGIC
    # ==========================================
    def get_service(self, name, version):
        creds = None
        token_path = get_path('token.json')
        creds_path = get_path('credentials.json')
        if os.path.exists(token_path): creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token: token.write(creds.to_json())
        return build(name, version, credentials=creds)

    def load_tasks(self):
        task_path = get_path('tasks.json')
        if os.path.exists(task_path):
            try:
                with open(task_path, 'r') as f: self.data["tasks"] = json.load(f)
            except: self.data["tasks"] = []

    def save_tasks(self):
        with open(get_path('tasks.json'), 'w') as f: json.dump(self.data["tasks"], f)

    def fetch_all_data(self, target_date=None):
        if target_date: self.data["selected_date"] = target_date
        d = self.data["selected_date"]
        
        self.sync_btn.configure(text="⏳ Syncing...")
        
        try:
            service = self.get_service('sheets', 'v4')
            rev_result = service.spreadsheets().values().get(spreadsheetId=config.FINANCIAL_SHEET_ID, range=f"'{config.TAB_REVENUE}'!B3:C5").execute()
            rows = rev_result.get('values', [])
            if len(rows) >= 3:
                self.data["sub_achieved"] = rows[0][0]
                self.data["topup_achieved"] = rows[1][0]
                self.data["achieved"] = rows[2][0]
                self.data["target"] = rows[2][1]

            ren_result = service.spreadsheets().values().get(spreadsheetId=config.FINANCIAL_SHEET_ID, range=f"'{config.TAB_RENEWAL}'!A2:J100").execute()
            self.data["renewal_list"] = ren_result.get('values', [])

            cal_service = self.get_service('calendar', 'v3')
            time_min = datetime.datetime.combine(d, datetime.time.min).isoformat() + 'Z'
            time_max = datetime.datetime.combine(d, datetime.time.max).isoformat() + 'Z'
            self.data["events"] = cal_service.events().list(calendarId=config.OFFICE_CALENDAR_ID, timeMin=time_min, timeMax=time_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
            
            self.show_page(self.current_page)
        except Exception as e: 
            print(f"❌ Sync Error: {e}")
        finally:
            self.sync_btn.configure(text="🔄 Sync System")

    # ==========================================
    # NAVIGATION LOGIC
    # ==========================================
    def create_nav_btn(self, text, page_name, parent):
        btn = ctk.CTkButton(
            parent, text=text, height=38, corner_radius=6, 
            fg_color="transparent", text_color=config.COLORS["text_dim"], 
            hover_color=config.COLORS["surface_hover"], font=(config.FONT, 14), 
            anchor="w", command=lambda: self.show_page(page_name)
        )
        btn.pack(fill="x", padx=15, pady=2)
        self.nav_buttons[page_name] = btn

    def show_page(self, page_name):
        self.current_page = page_name
        
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(fg_color=config.COLORS["surface_hover"], text_color=config.COLORS["text_main"])
            else:
                btn.configure(fg_color="transparent", text_color=config.COLORS["text_dim"])
                
        frame = self.pages[page_name]
        frame.tkraise()
        
        if hasattr(frame, 'update_ui'):
            frame.update_ui()

if __name__ == "__main__":
    app = CSCommandOS()
    app.mainloop()