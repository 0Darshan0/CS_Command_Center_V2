import customtkinter as ctk
from google import generativeai as genai
import config
import webbrowser
import urllib.parse
import re

class ChurnAnalyzerPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        genai.configure(api_key=config.GEMINI_API_KEY)
        
    def update_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        
        ctk.CTkLabel(self, text="AI Churn Predictor & MoM", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 10))

        # CLIENT HEALTH DASHBOARD
        self.health_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.health_frame.pack(fill="x", pady=10)
        self.health_badge = self.create_health_card(self.health_frame, "CLIENT HEALTH", "-", "#334155")
        self.risk_badge = self.create_health_card(self.health_frame, "CHURN RISK", "-", "#334155")

        # INPUT CARD
        input_card = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=12)
        input_card.pack(fill="x", pady=10)
        
        # Header with Auto-Fetch Button
        input_header = ctk.CTkFrame(input_card, fg_color="transparent")
        input_header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(input_header, text="RAW TRANSCRIPT / NOTES", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["text_dim"]).pack(side="left")
        ctk.CTkButton(input_header, text="📥 Fetch from Google Drive", height=28, font=ctk.CTkFont(size=11, weight="bold"), fg_color=config.COLORS["accent"], command=self.fetch_latest_transcript).pack(side="right")
        
        self.ai_input = ctk.CTkTextbox(input_card, height=120, fg_color="#0f172a", border_width=1, border_color="#334155")
        self.ai_input.pack(fill="x", padx=20, pady=(0, 20))
        self.ai_input.insert("0.0", "Paste your transcript here, or click 'Fetch from Google Drive' to pull your latest Google Meet transcript automatically.")

        # BUTTON ROW
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=10)
        self.gen_btn = ctk.CTkButton(btn_row, text="Analyze Transcript 🚨", font=ctk.CTkFont(size=14, weight="bold"), height=45, fg_color=config.COLORS["urgent"], command=self.generate_report)
        self.gen_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.email_btn = ctk.CTkButton(btn_row, text="📧 Draft Follow-up", font=ctk.CTkFont(size=14, weight="bold"), height=45, fg_color=config.COLORS["success"], command=self.draft_email, state="disabled")
        self.email_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # OUTPUT CARD
        output_card = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=12)
        output_card.pack(fill="both", expand=True)
        self.ai_output = ctk.CTkTextbox(output_card, font=("Segoe UI", 13), fg_color="#0f172a")
        self.ai_output.pack(fill="both", expand=True, padx=20, pady=20)

    def create_health_card(self, parent, title, val, color):
        card = ctk.CTkFrame(parent, fg_color=config.COLORS["card"], height=80, corner_radius=10)
        card.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=config.COLORS["text_dim"]).pack(pady=(10,0))
        badge = ctk.CTkFrame(card, fg_color=color, corner_radius=8)
        badge.pack(pady=5)
        lbl = ctk.CTkLabel(badge, text=val, font=ctk.CTkFont(size=16, weight="bold"), padx=15, pady=2)
        lbl.pack()
        return lbl

    def fetch_latest_transcript(self):
        """Automatically searches Google Drive for the newest Google Meet Transcript"""
        self.ai_input.delete("0.0", "end")
        self.ai_input.insert("0.0", "⏳ Searching Google Drive for the latest transcript...")
        self.update()

        try:
            drive_service = self.controller.get_service('drive', 'v3')
            
            # Search for Google Docs that contain the word "Transcript" in the title
            results = drive_service.files().list(
                q="name contains 'Transcript' and mimeType='application/vnd.google-apps.document'",
                orderBy="createdTime desc",
                pageSize=1,
                fields="files(id, name)"
            ).execute()
            
            items = results.get('files',[])
            
            if not items:
                self.ai_input.delete("0.0", "end")
                self.ai_input.insert("0.0", "❌ No transcripts found in your Google Drive.")
                return
                
            latest_file = items[0]
            
            self.ai_input.delete("0.0", "end")
            self.ai_input.insert("0.0", f"⏳ Downloading '{latest_file['name']}'...")
            self.update()
            
            # Download the text from the Google Doc
            content = drive_service.files().export_media(
                fileId=latest_file['id'], 
                mimeType='text/plain'
            ).execute()
            
            transcript_text = content.decode('utf-8')
            
            self.ai_input.delete("0.0", "end")
            self.ai_input.insert("0.0", transcript_text)
            
        except Exception as e:
            self.ai_input.delete("0.0", "end")
            self.ai_input.insert("0.0", f"❌ Error fetching from Drive: {e}\n(Did you delete token.json and re-authorize?)")

    def generate_report(self):
        notes = self.ai_input.get("0.0", "end").strip()
        if not notes or "Paste your entire" in notes or "Searching" in notes: return
        
        self.ai_output.delete("0.0", "end")
        self.ai_output.insert("0.0", "⏳ Gemini is reading the transcript and analyzing sentiment...")
        self.update()

        try:
            available_models =[m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            best_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
            model = genai.GenerativeModel(best_model)
            
            prompt = f"""
            You are a Senior Client Success Analyst. Read the following meeting transcript/notes.
            First, analyze the client's sentiment and give a Health Score (1-10) and Churn Risk (LOW, MEDIUM, HIGH).
            Then, provide structured Minutes of Meeting.
            
            You MUST use this EXACT format:
            
            ---METRICS---
            [HEALTH:8][RISK:LOW]
            
            ---MOM---
            (Executive summary of the meeting)
            
            ---NEXT_STEPS---
            (Bulleted action items with owners)
            
            ---CHURN_ANALYSIS---
            (1 paragraph explaining why you gave this health score and risk level)
            
            TRANSCRIPT/NOTES: {notes}
            """
            response = model.generate_content(prompt)
            full_text = response.text
            
            health_match = re.search(r'\[HEALTH:(\d+)\]', full_text)
            risk_match = re.search(r'\[RISK:([A-Z]+)\]', full_text)
            
            if health_match and risk_match:
                health_score = int(health_match.group(1))
                risk_level = risk_match.group(1)
                
                h_color = config.COLORS["success"] if health_score >= 8 else config.COLORS["warning"] if health_score >= 5 else config.COLORS["urgent"]
                self.health_badge.configure(text=f"{health_score} / 10")
                self.health_badge.master.configure(fg_color=h_color)
                
                r_color = config.COLORS["success"] if risk_level == "LOW" else config.COLORS["warning"] if risk_level == "MEDIUM" else config.COLORS["urgent"]
                self.risk_badge.configure(text=risk_level)
                self.risk_badge.master.configure(fg_color=r_color)
                
                display_text = full_text.split("---MOM---")[1].strip() if "---MOM---" in full_text else full_text
                display_text = "---MINUTES OF MEETING---\n" + display_text
            else:
                display_text = full_text

            self.ai_output.delete("0.0", "end")
            self.ai_output.insert("0.0", display_text)
            self.email_btn.configure(state="normal")
            
        except Exception as e:
            self.ai_output.delete("0.0", "end")
            self.ai_output.insert("0.0", f"❌ AI Error: {str(e)}")

    def draft_email(self):
        full_text = self.ai_output.get("0.0", "end")
        email_body = full_text
        if "---NEXT_STEPS---" in full_text:
            parts = full_text.split("---CHURN_ANALYSIS---")[0] 
            email_body = parts.replace("---MINUTES OF MEETING---", "Meeting Summary:").replace("---NEXT_STEPS---", "\nNext Steps:").replace("**", "").strip()

        subject = urllib.parse.quote("Notes & Next Steps from our meeting")
        body_text = f"Hi Team,\n\nThank you for the productive call today. Please find the summary below:\n\n{email_body}\n\nBest regards,\nDarshan Sheregar"
        body = urllib.parse.quote(body_text)
        
        office_email = config.OFFICE_CALENDAR_ID
        gmail_url = f"https://mail.google.com/mail/u/{office_email}/?view=cm&fs=1&su={subject}&body={body}"
        webbrowser.open(gmail_url)