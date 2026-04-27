import customtkinter as ctk
from google import generativeai as genai
import config
import webbrowser
import urllib.parse

class AIPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        genai.configure(api_key=config.GEMINI_API_KEY)
        
    def update_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        # --- APPLE AESTHETIC HEADER ---
        ctk.CTkLabel(self, text="Strategic AI Briefing", font=ctk.CTkFont(family=config.FONT, size=32, weight="bold"), text_color="#FFFFFF").pack(anchor="w", pady=(0, 20))

        # --- INPUT SECTION (Flat macOS Style) ---
        ctk.CTkLabel(self, text="MEETING NOTES", font=ctk.CTkFont(family=config.FONT, size=12, weight="bold"), text_color=config.COLORS["text_dim"]).pack(anchor="w", pady=(0, 8))
        
        # Textbox acts as its own native container
        self.ai_input = ctk.CTkTextbox(self, height=140, fg_color=config.COLORS["card"], text_color="#FFFFFF", border_width=1, border_color=config.COLORS["border"], corner_radius=10, font=ctk.CTkFont(family=config.FONT, size=15), wrap="word")
        self.ai_input.pack(fill="x", pady=(0, 25))
        self.ai_input.insert("0.0", "Paste messy notes here (e.g., 'client happy but needs more training on the dashboard next week')")

        # --- RESPONSIVE BUTTON ROW (Apple Standard Buttons) ---
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 25))
        
        # Primary Action (Apple System Blue, height=36, corner_radius=8)
        self.gen_btn = ctk.CTkButton(btn_row, text="Generate Briefing", font=ctk.CTkFont(family=config.FONT, size=14, weight="bold"), height=36, corner_radius=8, fg_color=config.COLORS["accent"], hover_color="#0070DF", command=self.generate_report)
        self.gen_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Secondary Action (macOS Dark Gray, muted)
        self.email_btn = ctk.CTkButton(btn_row, text="Draft in Gmail", font=ctk.CTkFont(family=config.FONT, size=14, weight="bold"), height=36, corner_radius=8, fg_color="#2C2C2E", hover_color="#3A3A3C", text_color="#FFFFFF", command=self.draft_email, state="disabled")
        self.email_btn.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # --- OUTPUT SECTION ---
        ctk.CTkLabel(self, text="BRIEFING OUTPUT", font=ctk.CTkFont(family=config.FONT, size=12, weight="bold"), text_color=config.COLORS["text_dim"]).pack(anchor="w", pady=(0, 8))
        
        self.ai_output = ctk.CTkTextbox(self, fg_color=config.COLORS["card"], text_color="#E5E5EA", border_width=1, border_color=config.COLORS["border"], corner_radius=10, font=ctk.CTkFont(family=config.FONT, size=15), wrap="word")
        self.ai_output.pack(fill="both", expand=True, pady=(0, 10))

    def generate_report(self):
        notes = self.ai_input.get("0.0", "end").strip()
        if not notes or "Paste messy" in notes:
            return
        
        self.ai_output.delete("0.0", "end")
        self.ai_output.insert("0.0", "⏳ AI is processing your strategic brief...")
        self.update()

        try:
            available_models =[m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            best_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
            model = genai.GenerativeModel(best_model)
            
            prompt = f"""
            You are a World-Class Client Success Strategist. 
            Transform these notes into the following 5 sections. 
            You MUST use the exact headings wrapped in '---'.
            
            ---INTERNAL---
            (Write the teammate-style briefing here)
            
            ---EXTERNAL---
            (Write ONLY the body of a highly professional client-facing email. 
            Rule 1: Break it into very short, easy-to-read paragraphs.
            Rule 2: You MUST include a bulleted list for 'Key Takeaways' or 'Next Steps'.
            Rule 3: Do NOT include 'Subject:', 'Dear Client', or 'Best regards'. Just the core message.)
            
            ---VERBAL---
            (1-sentence headline for a quick sync)
            
            ---STATUS---
            (Checklist of Done vs Pending)
            
            ---PRO-TIP---
            (Suggest one proactive 'Power Move')
            
            NOTES: {notes}
            """
            
            response = model.generate_content(prompt)
            self.ai_output.delete("0.0", "end")
            self.ai_output.insert("0.0", response.text)
            
            self.email_btn.configure(state="normal")
            
        except Exception as e:
            self.ai_output.delete("0.0", "end")
            self.ai_output.insert("0.0", f"❌ AI Error: {str(e)}")

    def draft_email(self):
        full_text = self.ai_output.get("0.0", "end")
        email_body = "Could not extract email body. Please copy manually."
        
        if "---EXTERNAL---" in full_text and "---VERBAL---" in full_text:
            extracted = full_text.split("---EXTERNAL---")[1].split("---VERBAL---")[0]
            email_body = extracted.replace("**", "").strip()

        subject = urllib.parse.quote("Update on our recent sync")
        body_text = f"Hi Team,\n\n{email_body}\n\nBest regards,\nDarshan Sheregar"
        body = urllib.parse.quote(body_text)
        
        office_email = config.OFFICE_CALENDAR_ID
        gmail_url = f"https://mail.google.com/mail/u/{office_email}/?view=cm&fs=1&su={subject}&body={body}"
        
        webbrowser.open(gmail_url)