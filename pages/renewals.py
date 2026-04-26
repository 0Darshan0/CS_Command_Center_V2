import customtkinter as ctk
import config

class RenewalsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
    def update_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        
        ctk.CTkLabel(self, text="Detailed Renewal Tracker", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 20))

        scroll = ctk.CTkScrollableFrame(self, fg_color=config.COLORS["card"], corner_radius=12)
        scroll.pack(fill="both", expand=True)

        # TABLE HEADERS
        header = ctk.CTkFrame(scroll, fg_color="#1e293b", height=40)
        header.pack(fill="x", padx=5, pady=5)
        cols = [("CLIENT", 200), ("DATE", 120), ("PLAN", 150), ("STATUS", 120), ("REMARKS", 200)]
        for text, w in cols:
            ctk.CTkLabel(header, text=text, font=ctk.CTkFont(size=11, weight="bold"), width=w, anchor="w").pack(side="left", padx=10)

        # DATA ROWS
        for r in self.controller.data.get("renewal_list", []):
            if len(r) > 9:
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", padx=5, pady=2)
                
                ctk.CTkLabel(row, text=r[1], width=200, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10) # Client
                ctk.CTkLabel(row, text=r[6], width=120, anchor="w").pack(side="left", padx=10) # Date
                ctk.CTkLabel(row, text=r[5], width=150, anchor="w", text_color=config.COLORS["text_dim"]).pack(side="left", padx=10) # Plan
                
                # Status Badge
                st = r[8]
                color = config.COLORS["success"] if "Paid" in st else config.COLORS["warning"]
                badge = ctk.CTkFrame(row, fg_color=color, corner_radius=6, width=120)
                badge.pack(side="left", padx=10)
                ctk.CTkLabel(badge, text=st, font=ctk.CTkFont(size=10, weight="bold")).pack(pady=2)

                ctk.CTkLabel(row, text=r[9], width=200, anchor="w", text_color=config.COLORS["text_dim"]).pack(side="left", padx=10) # Remarks
                ctk.CTkFrame(scroll, height=1, fg_color="#2d3748").pack(fill="x")