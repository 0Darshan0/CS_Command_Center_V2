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

def get_path(filename):
    return os.path.join(BASE_DIR, filename)

import customtkinter as ctk
import config 
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# --- IMPORT ALL 6 PAGES ---
from pages.overview import OverviewPage
from pages.renewals import RenewalsPage
from pages.calendar import CalendarPage
from pages.ai_briefing import AIPage
from pages.tasks import TasksPage
from pages.churn_analyzer import ChurnAnalyzerPage

class CSCommandOS(ctk.CTk):
    SCOPES =['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/drive.readonly']

    def __init__(self):
        super().__init__()
        
        self.title("CS COMMAND OS V2.0") 
        self.geometry("1300x850")
        self.configure(fg_color=config.COLORS["bg"])
        
        self.data = {
            "achieved": "₹0", "target": "₹0", "sub_achieved": "₹0", "topup_achieved": "₹0",
            "events": [], "renewal_list":[], "selected_date": datetime.date.today(),
            "tasks":[]
        }
        
        # FIX FOR TKINTER ERROR: Define the current page upfront!
        self.current_page = "OverviewPage" 
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=config.COLORS["sidebar"], corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="CS COMMAND", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=40)
        
        self.create_nav_btn("📊 Overview", "OverviewPage")
        self.create_nav_btn("📋 Tasks", "TasksPage")
        self.create_nav_btn("💰 Renewals", "RenewalsPage")
        self.create_nav_btn("🗓️ Calendar", "CalendarPage")
        self.create_nav_btn("🚀 AI Briefing", "AIPage")
        self.create_nav_btn("🚨 Churn Predictor", "ChurnAnalyzerPage") # NEW PAGE BUTTON

        ctk.CTkButton(self.sidebar, text="🔄 Sync System", fg_color="transparent", border_width=1, 
                      command=self.fetch_all_data).pack(side="bottom", pady=30, padx=20)

        # --- CONTAINER ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # --- REGISTER PAGES ---
        self.pages = {}
        # ADDED CHURN ANALYZER HERE
        for PageClass in[OverviewPage, TasksPage, RenewalsPage, CalendarPage, AIPage, ChurnAnalyzerPage]:
            page_name = PageClass.__name__
            frame = PageClass(parent=self.container, controller=self)
            self.pages[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.load_tasks()
        self.fetch_all_data()
        self.show_page(self.current_page)

    def get_service(self, name, version):
        creds = None
        token_path = get_path('token.json')
        creds_path = get_path('credentials.json')

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        return build(name, version, credentials=creds)

    def load_tasks(self):
        task_path = get_path('tasks.json')
        if os.path.exists(task_path):
            try:
                with open(task_path, 'r') as f:
                    self.data["tasks"] = json.load(f)
            except: self.data["tasks"] =[]

    def save_tasks(self):
        with open(get_path('tasks.json'), 'w') as f:
            json.dump(self.data["tasks"], f)

    def fetch_all_data(self, target_date=None):
        if target_date: self.data["selected_date"] = target_date
        d = self.data["selected_date"]
        try:
            service = self.get_service('sheets', 'v4')
            rev_result = service.spreadsheets().values().get(
                spreadsheetId=config.FINANCIAL_SHEET_ID, range=f"'{config.TAB_REVENUE}'!B3:C5").execute()
            rows = rev_result.get('values',[])
            if len(rows) >= 3:
                self.data["sub_achieved"] = rows[0][0]
                self.data["topup_achieved"] = rows[1][0]
                self.data["achieved"] = rows[2][0]
                self.data["target"] = rows[2][1]

            ren_result = service.spreadsheets().values().get(
                spreadsheetId=config.FINANCIAL_SHEET_ID, range=f"'{config.TAB_RENEWAL}'!A2:J100").execute()
            self.data["renewal_list"] = ren_result.get('values',[])

            cal_service = self.get_service('calendar', 'v3')
            time_min = datetime.datetime.combine(d, datetime.time.min).isoformat() + 'Z'
            time_max = datetime.datetime.combine(d, datetime.time.max).isoformat() + 'Z'
            self.data["events"] = cal_service.events().list(calendarId=config.OFFICE_CALENDAR_ID, 
                                                            timeMin=time_min, timeMax=time_max,
                                                            singleEvents=True, orderBy='startTime').execute().get('items',[])
            
            # Safely show the current page
            self.show_page(self.current_page)
        except Exception as e: print(f"❌ Sync Error: {e}")

    def create_nav_btn(self, text, page_name):
        btn = ctk.CTkButton(self.sidebar, text=text, height=45, fg_color="transparent", anchor="w",
                            command=lambda: self.show_page(page_name))
        btn.pack(fill="x", padx=15, pady=5)

    def show_page(self, page_name):
        self.current_page = page_name
        frame = self.pages[page_name]
        frame.tkraise()
        frame.update_ui()

if __name__ == "__main__":
    app = CSCommandOS()
    app.mainloop()