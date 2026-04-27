import customtkinter as ctk
import config

class RenewalsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
    def update_ui(self):
        for widget in self.winfo_children(): 
            widget.destroy()
        
        # --- HEADER ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="Renewal Tracker", font=ctk.CTkFont(family=config.FONT, size=32, weight="bold"), text_color="#FFFFFF").pack(side="left")

        rows = self.controller.data.get("renewal_list",[])
        total_accounts = len([r for r in rows if len(r) > 9])
        ctk.CTkLabel(header_frame, text=f"{total_accounts} Accounts", font=ctk.CTkFont(family=config.FONT, size=16), text_color=config.COLORS["accent"]).pack(side="right", pady=(10,0))

        # --- MAIN CONTAINER ---
        list_card = ctk.CTkFrame(self, fg_color=config.COLORS["card"], corner_radius=15)
        list_card.pack(fill="both", expand=True, pady=(0, 10))

        # --- STRICT TABLE HEADER ---
        table_header = ctk.CTkFrame(list_card, fg_color="transparent", height=40)
        table_header.pack(fill="x", padx=20, pady=(15, 5))
        table_header.pack_propagate(False) # Locks the height

        # Define strict column widths for perfect alignment
        cols =[
            ("CLIENT INFO", 280, "w"),
            ("PLAN", 180, "w"),
            ("AMOUNT", 100, "e"),  # Right-aligned for numbers
            ("DUE DATE", 120, "center"),
            ("STATUS", 180, "center"),
            ("REMARKS", 200, "w")
        ]

        for text, w, align in cols:
            anchor = "w" if align == "w" else ("e" if align == "e" else "center")
            lbl = ctk.CTkLabel(table_header, text=text, width=w, anchor=anchor, font=ctk.CTkFont(family=config.FONT, size=12, weight="bold"), text_color=config.COLORS["text_dim"])
            lbl.pack(side="left", padx=10)

        # Thick Divider Line
        ctk.CTkFrame(list_card, height=1, fg_color=config.COLORS["border"]).pack(fill="x", padx=20)

        # --- SCROLLABLE LIST ---
        scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        if not rows:
            ctk.CTkLabel(scroll, text="No renewals found.", font=ctk.CTkFont(family=config.FONT, size=15), text_color=config.COLORS["text_dim"]).pack(pady=40)
        else:
            for r in rows:
                if len(r) > 9:
                    self.create_renewal_row(scroll, r)

    def create_renewal_row(self, parent, r):
        # 1. Create a rigid row frame
        row = ctk.CTkFrame(parent, fg_color="transparent", height=65)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False) # Forces the row to stay exactly 65px tall
        
        # 2. CLIENT INFO (Width: 280)
        client_col = ctk.CTkFrame(row, fg_color="transparent", width=280)
        client_col.pack(side="left", padx=10, fill="y")
        client_col.pack_propagate(False)
        
        # Inner frame to perfectly center the two lines of text vertically
        inner_client = ctk.CTkFrame(client_col, fg_color="transparent")
        inner_client.place(relx=0, rely=0.5, anchor="w") 
        ctk.CTkLabel(inner_client, text=r[1], font=ctk.CTkFont(family=config.FONT, size=15, weight="bold"), anchor="w").pack(fill="x")
        email = r[2] if r[2] and r[2] != "N/A" else "No email"
        ctk.CTkLabel(inner_client, text=email, font=ctk.CTkFont(family=config.FONT, size=12), text_color=config.COLORS["accent"], anchor="w").pack(fill="x")

        # 3. PLAN (Width: 180)
        plan_col = ctk.CTkFrame(row, fg_color="transparent", width=180)
        plan_col.pack(side="left", padx=10, fill="y")
        plan_col.pack_propagate(False)
        ctk.CTkLabel(plan_col, text=r[5], font=ctk.CTkFont(family=config.FONT, size=14), text_color="#E5E5EA", anchor="w").place(relx=0, rely=0.5, anchor="w")

        # 4. AMOUNT (Width: 100, Right-Aligned)
        amt = str(r[4]).strip()
        amt_text = amt if "₹" in amt else f"₹{amt}" if amt and amt not in ["0", "N/A"] else "₹0"
        amt_col = ctk.CTkFrame(row, fg_color="transparent", width=100)
        amt_col.pack(side="left", padx=10, fill="y")
        amt_col.pack_propagate(False)
        ctk.CTkLabel(amt_col, text=amt_text, font=ctk.CTkFont(family=config.FONT, size=16, weight="bold"), anchor="e").place(relx=1.0, rely=0.5, anchor="e")

        # 5. DUE DATE (Width: 120, Center-Aligned)
        date_col = ctk.CTkFrame(row, fg_color="transparent", width=120)
        date_col.pack(side="left", padx=10, fill="y")
        date_col.pack_propagate(False)
        ctk.CTkLabel(date_col, text=r[6], font=ctk.CTkFont(family=config.FONT, size=14), text_color="#E5E5EA").place(relx=0.5, rely=0.5, anchor="center")

        # 6. STATUS (Width: 180, Center-Aligned Pill)
        status_col = ctk.CTkFrame(row, fg_color="transparent", width=180)
        status_col.pack(side="left", padx=10, fill="y")
        status_col.pack_propagate(False)
        
        st = str(r[8]).strip()
        st_lower = st.lower()
        if "paid" in st_lower or "closed" in st_lower or "safe" in st_lower:
            s_color = config.COLORS["success"]; bg_color = "#1A3B22"
        elif "ongoing" in st_lower or "pending" in st_lower or "soon" in st_lower:
            s_color = config.COLORS["warning"]; bg_color = "#4D3E0C"
        else: 
            s_color = config.COLORS["urgent"]; bg_color = "#4A1A1A"

        badge = ctk.CTkFrame(status_col, fg_color=bg_color, corner_radius=8)
        badge.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(badge, text=st.upper(), font=ctk.CTkFont(family=config.FONT, size=11, weight="bold"), text_color=s_color, padx=12, pady=4).pack()

        # 7. REMARKS (Expands to fill remaining space)
        remark_col = ctk.CTkFrame(row, fg_color="transparent")
        remark_col.pack(side="left", fill="both", expand=True, padx=10)
        remark_text = r[9] if r[9] and r[9] != "N/A" else "--"
        ctk.CTkLabel(remark_col, text=remark_text, font=ctk.CTkFont(family=config.FONT, size=13), text_color=config.COLORS["text_dim"], anchor="w", wraplength=200).place(relx=0, rely=0.5, anchor="w")

        # 8. Subtle Row Divider
        ctk.CTkFrame(parent, height=1, fg_color=config.COLORS["border"]).pack(fill="x", padx=30)