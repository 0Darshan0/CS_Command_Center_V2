import customtkinter as ctk
from google import generativeai as genai
import config
import re
import datetime

class ChurnAnalyzerPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.parsed_data = {} 
        
    def update_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        # --- APPLE AESTHETIC HEADER ---
        ctk.CTkLabel(self, text="AI Churn Predictor & CRM", font=ctk.CTkFont(family=config.FONT, size=32, weight="bold"), text_color="#FFFFFF").pack(anchor="w", pady=(0, 20))

        # --- HEALTH DASHBOARD (Apple Styled Cards) ---
        self.health_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.health_frame.pack(fill="x", pady=(0, 15))
        
        self.health_badge = self.create_health_card(self.health_frame, "CLIENT HEALTH", "-", "#2C2C2E")
        self.risk_badge = self.create_health_card(self.health_frame, "CHURN RISK", "-", "#2C2C2E")
        self.client_badge = self.create_health_card(self.health_frame, "DETECTED CLIENT", "Awaiting notes...", "#2C2C2E")

        # --- INPUT SECTION (Flat macOS Style) ---
        ctk.CTkLabel(self, text="MEETING TRANSCRIPT", font=ctk.CTkFont(family=config.FONT, size=12, weight="bold"), text_color=config.COLORS["text_dim"]).pack(anchor="w", pady=(0, 8))
        
        self.ai_input = ctk.CTkTextbox(self, height=120, fg_color=config.COLORS["card"], text_color="#FFFFFF", border_width=1, border_color=config.COLORS["border"], corner_radius=10, font=ctk.CTkFont(family=config.FONT, size=15), wrap="word")
        self.ai_input.pack(fill="x", pady=(0, 20))
        self.ai_input.insert("0.0", "Paste your entire meeting transcript here...")

        # --- RESPONSIVE BUTTON ROW ---
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 20))
        
        # Primary Action Button (Red/Urgent)
        self.gen_btn = ctk.CTkButton(btn_row, text="Analyze Transcript", font=ctk.CTkFont(family=config.FONT, size=14, weight="bold"), height=36, corner_radius=8, fg_color=config.COLORS["urgent"], hover_color="#D13429", command=self.generate_report)
        self.gen_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # Secondary Action Button (Muted Dark Gray until active)
        self.save_btn = ctk.CTkButton(btn_row, text="Save to CRM", font=ctk.CTkFont(family=config.FONT, size=14, weight="bold"), height=36, corner_radius=8, fg_color="#2C2C2E", hover_color="#3A3A3C", text_color="#FFFFFF", command=self.save_to_crm, state="disabled")
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # --- OUTPUT SECTION ---
        ctk.CTkLabel(self, text="ANALYSIS & MoM", font=ctk.CTkFont(family=config.FONT, size=12, weight="bold"), text_color=config.COLORS["text_dim"]).pack(anchor="w", pady=(0, 8))
        
        self.ai_output = ctk.CTkTextbox(self, fg_color=config.COLORS["card"], text_color="#E5E5EA", border_width=1, border_color=config.COLORS["border"], corner_radius=10, font=ctk.CTkFont(family=config.FONT, size=15), wrap="word")
        self.ai_output.pack(fill="both", expand=True, pady=(0, 10))

    def create_health_card(self, parent, title, val, color):
        card = ctk.CTkFrame(parent, fg_color=config.COLORS["card"], height=70, corner_radius=10, border_width=1, border_color=config.COLORS["border"])
        card.pack(side="left", expand=True, fill="both", padx=(0, 10))
        
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family=config.FONT, size=11, weight="bold"), text_color=config.COLORS["text_dim"]).pack(pady=(12,0))
        
        badge = ctk.CTkFrame(card, fg_color=color, corner_radius=6)
        badge.pack(pady=(5, 12))
        lbl = ctk.CTkLabel(badge, text=val, font=ctk.CTkFont(family=config.FONT, size=14, weight="bold"), text_color="#FFFFFF", padx=12, pady=2)
        lbl.pack()
        return lbl

    def generate_report(self):
        notes = self.ai_input.get("0.0", "end").strip()
        if not notes or "Paste your" in notes: return
        
        self.ai_output.delete("0.0", "end")
        self.ai_output.insert("0.0", "⏳ Gemini is analyzing the transcript and formatting the MoM...")
        self.update()

        try:
            available_models =[m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            best_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
            model = genai.GenerativeModel(best_model)
            
            prompt = f"""
            You are a Senior Client Success Analyst. Read the following meeting transcript.
            
            CRITICAL SPELLING INSTRUCTIONS:
            Meeting transcripts often have phonetic spelling errors. You MUST correct them automatically.
            - E.g., "go quick", "goquick", "goclick" MUST be corrected to "Gokwik".
            - E.g., "cherry o", "cheerio" MUST be corrected to "Cheerio".
            - Fix any other obvious brand names based on context.

            INSTRUCTIONS:
            1. Guess the Client/Company Name.
            2. Analyze sentiment for Health Score (1-10) and Churn Risk (LOW, MEDIUM, HIGH).
            3. Provide a highly structured, professional Minutes of Meeting (MoM).
            
            You MUST use this EXACT format:
            
            ---METRICS---
            [CLIENT:Company Name][HEALTH:8][RISK:LOW]
            
            ---MOM---
            **1. Executive Summary:**
            (2-3 sentences summarizing the overall outcome of the meeting)

            **2. Key Discussion Points:**
            • (Bullet point covering major topics)
            • (Bullet point covering major topics)
            
            **3. Product / Support Feedback:**
            • (Note any bugs, feature requests, or dashboard complaints)
            
            ---NEXT_STEPS---
            • [ ] (Owner Name) - (Specific Action item)
            • [ ] (Owner Name) - (Specific Action item)
            
            ---CHURN_ANALYSIS---
            (1 short paragraph explaining the health score and risk level based on the client's tone)
            
            TRANSCRIPT: {notes}
            """
            response = model.generate_content(prompt)
            full_text = response.text
            
            client_match = re.search(r'\[CLIENT:(.*?)\]', full_text)
            health_match = re.search(r'\[HEALTH:(\d+)\]', full_text)
            risk_match = re.search(r'\[RISK:([A-Z]+)\]', full_text)
            
            if health_match and risk_match and client_match:
                client_name = client_match.group(1).strip()
                health_score = int(health_match.group(1))
                risk_level = risk_match.group(1)
                
                mom = full_text.split("---MOM---")[1].split("---NEXT_STEPS---")[0].strip() if "---MOM---" in full_text else "N/A"
                steps = full_text.split("---NEXT_STEPS---")[1].split("---CHURN_ANALYSIS---")[0].strip() if "---NEXT_STEPS---" in full_text else "N/A"
                
                self.parsed_data = {
                    "client": client_name,
                    "health": health_score,
                    "risk": risk_level,
                    "mom": mom,
                    "next_steps": steps
                }
                
                h_color = config.COLORS["success"] if health_score >= 8 else config.COLORS["warning"] if health_score >= 5 else config.COLORS["urgent"]
                self.health_badge.configure(text=f"{health_score} / 10")
                self.health_badge.master.configure(fg_color=h_color)
                
                r_color = config.COLORS["success"] if risk_level == "LOW" else config.COLORS["warning"] if risk_level == "MEDIUM" else config.COLORS["urgent"]
                self.risk_badge.configure(text=risk_level)
                self.risk_badge.master.configure(fg_color=r_color)
                
                self.client_badge.configure(text=client_name)
                self.client_badge.master.configure(fg_color=config.COLORS["accent"])
                
                display_text = full_text.split("---MOM---")[1].strip() if "---MOM---" in full_text else full_text
                display_text = "--- MINUTES OF MEETING ---\n\n" + display_text
            else:
                display_text = full_text

            self.ai_output.delete("0.0", "end")
            self.ai_output.insert("0.0", display_text)
            
            # Make the Save button "Pop" so the user knows it's ready
            self.save_btn.configure(state="normal", fg_color=config.COLORS["accent"], hover_color="#0070DF")
            
        except Exception as e:
            self.ai_output.delete("0.0", "end")
            self.ai_output.insert("0.0", f"❌ AI Error: {str(e)}")

    def save_to_crm(self):
        self.ai_output.insert("end", "\n\n⏳ Connecting to Google Sheets CRM...")
        self.update()
        
        try:
            service = self.controller.get_service('sheets', 'v4')
            sheet_id = config.CRM_SHEET_ID
            client_name = self.parsed_data.get("client", "Unknown Client")
            tab_name = re.sub(r'[\[\]*?:/\\]', '', client_name)[:30]

            sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheets = sheet_metadata.get('sheets', '')
            sheet_exists = any(s.get("properties", {}).get("title") == tab_name for s in sheets)

            if not sheet_exists:
                requests =[{"addSheet": {"properties": {"title": tab_name}}}]
                service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": requests}).execute()
                headers = [["Date", "Health Score", "Churn Risk", "Minutes of Meeting", "Next Steps"]]
                service.spreadsheets().values().update(
                    spreadsheetId=sheet_id, range=f"'{tab_name}'!A1:E1",
                    valueInputOption="USER_ENTERED", body={"values": headers}
                ).execute()

            today_str = datetime.datetime.now().strftime("%b %d, %Y")
            row_data = [[
                today_str,
                f"{self.parsed_data.get('health', '')}/10",
                self.parsed_data.get("risk", ""),
                self.parsed_data.get("mom", ""),
                self.parsed_data.get("next_steps", "")
            ]]
            
            service.spreadsheets().values().append(
                spreadsheetId=sheet_id, range=f"'{tab_name}'!A2:E2",
                valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
                body={"values": row_data}
            ).execute()
            
            self.ai_output.insert("end", f"\n✅ Successfully saved to CRM Tab: '{tab_name}'!")
            
            # Switch button back to muted gray state after saving
            self.save_btn.configure(state="disabled", text="Saved Successfully", fg_color="#2C2C2E", hover_color="#2C2C2E")
            
        except Exception as e:
            self.ai_output.insert("end", f"\n❌ CRM Save Error: {str(e)}")