import customtkinter as ctk
from google import generativeai as genai
import config

class AIPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        # Configure AI with your key
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
        
        self.ai_input = ctk.CTkTextbox(input_card, height=150, fg_color="#0f172a", border_width=1, border_color="#334155")
        self.ai_input.pack(fill="x", padx=20, pady=(0, 20))
        self.ai_input.insert("0.0", "Paste messy notes here (e.g., 'client happy but needs more training on the dashboard next week')")

        # Action Button
        self.gen_btn = ctk.CTkButton(self, text="GENERATE STRATEGIC BRIEFING 🚀", font=ctk.CTkFont(size=14, weight="bold"), height=45, fg_color=config.COLORS["accent"], command=self.generate_report)
        self.gen_btn.pack(fill="x", pady=20)

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
        self.ai_output.insert("0.0", "⏳ AI is searching for a working model and strategizing...")
        self.update()

        try:
            # The "Standup_Pro" Brain: Automatically find a working model
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            best_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
            
            model = genai.GenerativeModel(best_model)
            
            prompt = f"""
            You are a World-Class Client Success Strategist. 
            Transform these notes into:
            1. INTERNAL (Teammate-style briefing)
            2. EXTERNAL (Professional Value summary for the client)
            3. VERBAL (1-sentence headline for a quick sync)
            4. STATUS (Checklist of Done vs Pending)
            5. PRO-TIP (Suggest one proactive 'Power Move')
            
            NOTES: {notes}
            """
            
            response = model.generate_content(prompt)
            self.ai_output.delete("0.0", "end")
            self.ai_output.insert("0.0", response.text)
            
        except Exception as e:
            self.ai_output.delete("0.0", "end")
            self.ai_output.insert("0.0", f"❌ AI Error: {str(e)}")