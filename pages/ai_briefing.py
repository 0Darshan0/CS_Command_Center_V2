import customtkinter as ctk
import requests
import threading
import queue
import json
import config
import webbrowser
import urllib.parse

class AIPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.ui_queue = queue.Queue()
        self.meetings_map = {} # This will store { "Meeting Title": "Recording_ID" }
        self.after(100, self.process_queue) 
        
    def process_queue(self):
        """Safely processes background thread messages on the main macOS UI thread."""
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                action = msg.get("action")
                
                if action == "update_fathom":
                    self.ai_input.delete("0.0", "end")
                    self.ai_input.insert("0.0", msg["text"])
                    self.fetch_btn.configure(state="normal")
                    
                elif action == "update_groq":
                    self.ai_output.delete("0.0", "end")
                    self.ai_output.insert("0.0", msg["text"])
                    self.gen_btn.configure(state="normal")
                    self.email_btn.configure(state=msg["email_state"])
                    
                elif action == "update_dropdown":
                    # Populate the dropdown menu safely on the UI thread
                    self.meetings_map = msg["map"]
                    self.meeting_dropdown.configure(values=msg["values"], state="normal")
                    self.meeting_dropdown.set(msg["values"][0]) # Select the first one automatically
                    self.fetch_btn.configure(state="normal")
                    
                elif action == "dropdown_error":
                    self.meeting_dropdown.configure(values=[msg["text"]])
                    self.meeting_dropdown.set(msg["text"])
                    
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue) 
            
    def update_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        # --- APPLE AESTHETIC HEADER ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="Strategic AI Briefing", font=ctk.CTkFont(family=config.FONT, size=32, weight="bold"), text_color="#FFFFFF").pack(side="left")

        # --- INPUT SECTION (Flat macOS Style) ---
        label_row = ctk.CTkFrame(self, fg_color="transparent")
        label_row.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(label_row, text="MEETING NOTES / TRANSCRIPT", font=ctk.CTkFont(family=config.FONT, size=12, weight="bold"), text_color=config.COLORS["text_dim"]).pack(side="left")
        
        # 🆕 NEW: The Fetch Button
        self.fetch_btn = ctk.CTkButton(label_row, text="🎙️ Fetch Transcript", font=ctk.CTkFont(family=config.FONT, size=12, weight="bold"), height=24, width=130, corner_radius=6, fg_color="#361763", hover_color=config.COLORS["accent"], command=self.fetch_fathom_meeting, state="disabled")
        self.fetch_btn.pack(side="right", padx=(10, 0))

        # 🆕 NEW: The Dropdown Menu
        self.meeting_dropdown = ctk.CTkOptionMenu(label_row, values=["Loading recent meetings..."], font=ctk.CTkFont(family=config.FONT, size=12), width=250, height=24, corner_radius=6, fg_color=config.COLORS["card"], button_color="#361763", button_hover_color=config.COLORS["accent"], state="disabled")
        self.meeting_dropdown.pack(side="right")

        # Textbox acts as its own native container
        self.ai_input = ctk.CTkTextbox(self, height=140, fg_color=config.COLORS["card"], text_color="#FFFFFF", border_width=1, border_color=config.COLORS["border"], corner_radius=10, font=ctk.CTkFont(family=config.FONT, size=15), wrap="word")
        self.ai_input.pack(fill="x", pady=(0, 25))
        self.ai_input.insert("0.0", "Paste messy notes here OR select a meeting from the dropdown above to auto-populate...")

        # --- RESPONSIVE BUTTON ROW ---
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 25))
        
        self.gen_btn = ctk.CTkButton(btn_row, text="Generate Briefing", font=ctk.CTkFont(family=config.FONT, size=14, weight="bold"), height=36, corner_radius=8, fg_color=config.COLORS["accent"], hover_color="#0070DF", command=self.generate_report)
        self.gen_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.email_btn = ctk.CTkButton(btn_row, text="Draft in Gmail", font=ctk.CTkFont(family=config.FONT, size=14, weight="bold"), height=36, corner_radius=8, fg_color="#2C2C2E", hover_color="#3A3A3C", text_color="#FFFFFF", command=self.draft_email, state="disabled")
        self.email_btn.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # --- OUTPUT SECTION ---
        ctk.CTkLabel(self, text="BRIEFING OUTPUT", font=ctk.CTkFont(family=config.FONT, size=12, weight="bold"), text_color=config.COLORS["text_dim"]).pack(anchor="w", pady=(0, 8))
        
        self.ai_output = ctk.CTkTextbox(self, fg_color=config.COLORS["card"], text_color="#E5E5EA", border_width=1, border_color=config.COLORS["border"], corner_radius=10, font=ctk.CTkFont(family=config.FONT, size=15), wrap="word")
        self.ai_output.pack(fill="both", expand=True, pady=(0, 10))
        
        # Kick off the background thread to load the dropdown menu!
        self.load_meetings_list()


    # ==========================================
    # FATHOM API INTEGRATION
    # ==========================================
    def load_meetings_list(self):
        """Fetches the last 15 meetings in the background to populate the dropdown."""
        threading.Thread(target=self._meetings_list_worker, daemon=True).start()
        
    def _meetings_list_worker(self):
        try:
            api_key = getattr(config, "FATHOM_API_KEY", None)
            if not api_key:
                self.ui_queue.put({"action": "dropdown_error", "text": "Missing API Key"})
                return

            headers = {"X-Api-Key": api_key}
            meetings_url = "https://api.fathom.ai/external/v1/meetings"
            response = requests.get(meetings_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Grab top 15 meetings
            meetings = response.json().get("items", [])[:15]
            
            if not meetings:
                self.ui_queue.put({"action": "dropdown_error", "text": "No recent meetings found"})
                return
                
            meetings_map = {}
            dropdown_values = []
            
            for m in meetings:
                rec_id = m.get("recording_id")
                title = m.get("meeting_title", "Untitled Call")
                # Format: "Meeting Title (ID)" to prevent duplicates
                display_name = f"{title} ({rec_id})"
                
                meetings_map[display_name] = rec_id
                dropdown_values.append(display_name)
                
            self.ui_queue.put({
                "action": "update_dropdown", 
                "values": dropdown_values,
                "map": meetings_map
            })
            
        except Exception as e:
            self.ui_queue.put({"action": "dropdown_error", "text": f"Error loading meetings"})

    def fetch_fathom_meeting(self):
        """Fetches the specific meeting selected in the dropdown."""
        selected_display_name = self.meeting_dropdown.get()
        
        # Check if they actually selected a valid meeting
        if selected_display_name not in self.meetings_map:
            return
            
        recording_id = self.meetings_map[selected_display_name]
        
        self.ai_input.delete("0.0", "end")
        self.ai_input.insert("0.0", f"⏳ Grabbing transcript for {selected_display_name}...")
        self.fetch_btn.configure(state="disabled")
        
        threading.Thread(target=self._transcript_worker, args=(recording_id, selected_display_name), daemon=True).start()

    def _transcript_worker(self, recording_id, display_name):
        try:
            api_key = getattr(config, "FATHOM_API_KEY", None)
            headers = {"X-Api-Key": api_key}
            
            transcript_url = f"https://api.fathom.ai/external/v1/recordings/{recording_id}/transcript"
            t_response = requests.get(transcript_url, headers=headers, timeout=15)
            t_response.raise_for_status()
            
            transcript_data = t_response.json()
            lines = [f"=== FATHOM TRANSCRIPT: {display_name} ===\n"]
            
            for line in transcript_data.get("transcript", []):
                speaker = line.get("speaker", {}).get("display_name", "Unknown")
                text = line.get("text", "")
                lines.append(f"{speaker}: {text}")
                
            full_transcript = "\n".join(lines)
            self.ui_queue.put({"action": "update_fathom", "text": full_transcript})
            
        except Exception as e:
            self.ui_queue.put({"action": "update_fathom", "text": f"❌ Error fetching transcript: {str(e)}"})


    # ==========================================
    # GROQ AI INTEGRATION
    # ==========================================
    def generate_report(self):
        notes = self.ai_input.get("0.0", "end").strip()
        if not notes or "Paste messy" in notes: return
        
        self.ai_output.delete("0.0", "end")
        self.ai_output.insert("0.0", "⏳ Groq Llama 3.3 70B is analyzing the transcript...")
        self.gen_btn.configure(state="disabled")
        
        threading.Thread(target=self._groq_worker, args=(notes,), daemon=True).start()

    def _groq_worker(self, notes):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a World-Class Client Success Strategist. Transform these notes into the following 5 sections. You MUST use the exact headings wrapped in '---'.\n\n---INTERNAL---\n(Write the teammate-style briefing here)\n\n---EXTERNAL---\n(Write ONLY the body of a highly professional client-facing email. Break it into short paragraphs. Include a bulleted list for Key Takeaways. No Subject or Best Regards.)\n\n---VERBAL---\n(1-sentence headline for a quick sync)\n\n---STATUS---\n(Checklist of Done vs Pending)\n\n---PRO-TIP---\n(Suggest one proactive 'Power Move')"},
                {"role": "user", "content": f"NOTES / TRANSCRIPT:\n{notes}"}
            ],
            "temperature": 0.5,
            "max_tokens": 1500
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            result_text = response.json()["choices"][0]["message"]["content"]
            self.ui_queue.put({"action": "update_groq", "text": result_text, "email_state": "normal"})
        except Exception as e:
            self.ui_queue.put({"action": "update_groq", "text": f"❌ Groq API Error: {str(e)}", "email_state": "disabled"})

    # ==========================================
    # GMAIL DRAFTING
    # ==========================================
    def draft_email(self):
        full_text = self.ai_output.get("0.0", "end")
        email_body = "Could not extract email body. Please copy manually."
        
        if "---EXTERNAL---" in full_text and "---VERBAL---" in full_text:
            extracted = full_text.split("---EXTERNAL---")[1].split("---VERBAL---")[0]
            email_body = extracted.replace("**", "").strip()

        subject = urllib.parse.quote("Update on our recent sync")
        body = urllib.parse.quote(f"Hi Team,\n\n{email_body}\n\nBest regards,\nDarshan Sheregar")
        office_email = getattr(config, "OFFICE_CALENDAR_ID", "your_email@gmail.com")
        gmail_url = f"https://mail.google.com/mail/u/{office_email}/?view=cm&fs=1&su={subject}&body={body}"
        webbrowser.open(gmail_url)