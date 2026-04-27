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
        
        # Header
        ctk.CTkLabel(self, text="Strategic AI Briefing", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 20))

        # Input Card
        input_card = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=12)
        input_card.pack(fill="x", pady=10)
        
        ctk.CTkLabel(input_card, text="MEETING NOTES", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.ai_input = ctk.CTkTextbox(input_card, height=120, fg_color="#0f172a", border_width=1, border_color="#334155")
        self.ai_input.pack(fill="x", padx=20, pady=(0, 20))
        self.ai_input.insert("0.0", "Paste messy notes here (e.g., 'client happy but needs more training on the dashboard next week')")

        # BUTTON ROW
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=10)
        
        self.gen_btn = ctk.CTkButton(btn_row, text="Generate Briefing 🚀", font=ctk.CTkFont(size=14, weight="bold"), height=45, fg_color=config.COLORS["accent"], command=self.generate_report)
        self.gen_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.email_btn = ctk.CTkButton(btn_row, text="📧 Draft in Gmail", font=ctk.CTkFont(size=14, weight="bold"), height=45, fg_color=config.COLORS["success"], command=self.draft_email, state="disabled")
        self.email_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Output Card
        output_card = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=12)
        output_card.pack(fill="both", expand=True)
        
        self.ai_output = ctk.CTkTextbox(output_card, font=("Segoe UI", 13), fg_color="#0f172a")
        self.ai_output.pack(fill="both", expand=True, padx=20, pady=20)

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
            
            # --- UPGRADED PROMPT FOR BETTER EMAIL FORMATTING ---
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
            # Replace bold markdown to keep it clean in plain text emails
            email_body = extracted.replace("**", "").strip()

        subject = urllib.parse.quote("Update on our recent sync")
        body_text = f"Hi Team,\n\n{email_body}\n\nBest regards,\nDarshan Sheregar"
        body = urllib.parse.quote(body_text)
        
        # --- THE PROFILE FIX ---
        # We inject your office email directly into the Gmail URL. 
        # This forces the browser to use your work account!
        office_email = config.OFFICE_CALENDAR_ID
        gmail_url = f"https://mail.google.com/mail/u/{office_email}/?view=cm&fs=1&su={subject}&body={body}"
        
        webbrowser.open(gmail_url)