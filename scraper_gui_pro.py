import customtkinter as ctk
import threading
import sys
import os
from tkinter import messagebox
from ultimate_scraper import UltimateScraper, Colors
import time

# Set Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class ScraperGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ULTIMATE DATA SCRAPER - GOD TIER EDITION")
        self.geometry("900x650")
        self.resizable(False, False)

        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="🕷️ ULTIMATE DATA SCRAPER - BEAST MODE", 
            font=("Roboto", 24, "bold"),
            text_color="#00E5FF"
        )
        self.title_label.pack(pady=20)

        # --- MAIN CONTENT ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        # Input Section
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.pack(fill="x", pady=(0, 20))

        # Query Input
        self.query_label = ctk.CTkLabel(self.input_frame, text="Enter Business Query (e.g. 'Gyms in London'):", font=("Arial", 14))
        self.query_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.query_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type here...", height=40, font=("Arial", 14))
        self.query_entry.pack(fill="x", padx=15, pady=(0, 15))

        # Limit Input
        self.limit_label = ctk.CTkLabel(self.input_frame, text="Max Results:", font=("Arial", 14))
        self.limit_label.pack(side="left", padx=15, pady=15)
        
        self.limit_entry = ctk.CTkEntry(self.input_frame, width=100, font=("Arial", 14))
        self.limit_entry.insert(0, "50")
        self.limit_entry.pack(side="left", pady=15)

        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=(0, 20))

        self.start_btn = ctk.CTkButton(
            self.button_frame, 
            text="🚀 START SCRAPING", 
            font=("Arial", 16, "bold"),
            height=50,
            fg_color="#00C853",
            hover_color="#009624",
            command=self.start_scraping
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.export_btn = ctk.CTkButton(
            self.button_frame, 
            text="💾 EXPORT DATA", 
            font=("Arial", 16, "bold"),
            height=50,
            fg_color="#2962FF",
            hover_color="#0039CB",
            state="disabled",
            command=self.export_data
        )
        self.export_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # --- CONSOLE LOG ---
        self.console_frame = ctk.CTkFrame(self.main_frame)
        self.console_frame.pack(fill="both", expand=True)
        
        self.console_label = ctk.CTkLabel(self.console_frame, text="LIVE LOGS:", font=("Courier New", 12, "bold"))
        self.console_label.pack(anchor="w", padx=10, pady=(5, 0))

        self.console = ctk.CTkTextbox(self.console_frame, font=("Courier New", 12), text_color="#00FF00", fg_color="black")
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        self.console.configure(state="disabled")

        # --- FOOTER ---
        self.footer = ctk.CTkLabel(self, text="Built by RANA JAWAD | God Tier Edition", font=("Arial", 10), text_color="gray")
        self.footer.grid(row=2, column=0, pady=5)

        # Logic Vars
        self.scraper = UltimateScraper(log_callback=self.update_console)
        self.is_running = False

    def update_console(self, message):
        """Callback to update GUI console safely"""
        self.console.configure(state="normal")
        self.console.insert("end", message + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def start_scraping(self):
        query = self.query_entry.get()
        if not query:
            messagebox.showwarning("Input Error", "Please enter a search query!")
            return
            
        try:
            limit = int(self.limit_entry.get())
        except ValueError:
            messagebox.showwarning("Input Error", "Limit must be a number!")
            return

        self.is_running = True
        self.start_btn.configure(state="disabled", text="⏳ RUNNING...")
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        
        # Run in separate thread to keep GUI responsive
        threading.Thread(target=self.run_scraper_thread, args=(query, limit), daemon=True).start()

    def run_scraper_thread(self, query, limit):
        try:
            self.scraper.results = [] # Reset results
            self.scraper.google_maps_scraper(query, limit)
            
            # Post-scrape actions
            self.update_console("\n[✓] SCRAPING COMPLETE! You can now Export.")
            self.start_btn.configure(state="normal", text="🚀 START SCRAPING")
            self.export_btn.configure(state="normal")
            
            # Auto-export as per God Tier features
            self.update_console("\n[*] Auto-Exporting to folder...")
            self.scraper.export_data(query_name=query)
            
        except Exception as e:
            self.update_console(f"\n[!] GUI Thread Error: {e}")
            self.start_btn.configure(state="normal", text="🚀 START SCRAPING")

    def export_data(self):
        query = self.query_entry.get()
        self.scraper.export_data(query_name=query)
        messagebox.showinfo("Success", "Data Exported Successfully!")

if __name__ == "__main__":
    app = ScraperGUI()
    app.mainloop()
