import customtkinter as ctk
import threading
import sys
import os
from tkinter import messagebox
from ultimate_scraper import UltimateScraper, Colors
import time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class ScraperGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GOD TIER SCRAPER v3.0")
        self.geometry("950x700")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#0A0A0F")
        self.header_frame.grid(row=0, column=0, sticky="ew")

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="GOD TIER SCRAPER — COMMAND CENTER",
            font=("Consolas", 22, "bold"),
            text_color="#00D4FF"
        )
        self.title_label.pack(pady=(18, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Multi-Source Lead Generation Engine",
            font=("Consolas", 11),
            text_color="#8B8B9E"
        )
        self.subtitle_label.pack(pady=(0, 15))

        # --- MAIN CONTENT ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # --- SOURCE SELECTOR ---
        self.source_frame = ctk.CTkFrame(self.main_frame, fg_color="#12121A", corner_radius=10)
        self.source_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(self.source_frame, text="SOURCE:", font=("Consolas", 11, "bold"), text_color="#8B8B9E").pack(side="left", padx=(15, 10), pady=12)

        self.source_var = ctk.StringVar(value="google_maps")
        sources = [("Maps", "google_maps"), ("Search", "google_search"), ("Yelp", "yelp"), ("YellowPages", "yellowpages")]
        for text, val in sources:
            btn = ctk.CTkRadioButton(
                self.source_frame, text=text, variable=self.source_var, value=val,
                font=("Consolas", 11), text_color="#E0E0E8",
                fg_color="#00D4FF", hover_color="#00B8D9",
                border_color="#2A2A3E"
            )
            btn.pack(side="left", padx=10, pady=12)

        # --- INPUT SECTION ---
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="#12121A", corner_radius=10)
        self.input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Query
        ctk.CTkLabel(self.input_frame, text="QUERY:", font=("Consolas", 11, "bold"), text_color="#8B8B9E").pack(anchor="w", padx=15, pady=(12, 3))
        self.query_entry = ctk.CTkEntry(
            self.input_frame, placeholder_text="e.g. Dentists in New York",
            height=38, font=("Consolas", 13), fg_color="#0A0A0F",
            border_color="#1A1A2E", text_color="#E0E0E8"
        )
        self.query_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Limit + Buttons row
        bottom_row = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        bottom_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(bottom_row, text="LIMIT:", font=("Consolas", 11, "bold"), text_color="#8B8B9E").pack(side="left")
        self.limit_entry = ctk.CTkEntry(bottom_row, width=80, font=("Consolas", 13), fg_color="#0A0A0F", border_color="#1A1A2E", text_color="#E0E0E8")
        self.limit_entry.insert(0, "50")
        self.limit_entry.pack(side="left", padx=(8, 20))

        self.headless_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(bottom_row, text="Headless", variable=self.headless_var, font=("Consolas", 11), text_color="#8B8B9E", fg_color="#00D4FF", border_color="#2A2A3E").pack(side="left", padx=(0, 20))

        self.start_btn = ctk.CTkButton(
            bottom_row, text="START SCRAPING", font=("Consolas", 13, "bold"),
            height=38, fg_color="#00D4FF", hover_color="#00B8D9",
            text_color="#0A0A0F", command=self.start_scraping
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            bottom_row, text="STOP", font=("Consolas", 13, "bold"),
            height=38, fg_color="#1A1A2E", hover_color="#FF3366",
            text_color="#FF3366", border_color="#FF3366", border_width=1,
            command=self.stop_scraping, state="disabled"
        )
        self.stop_btn.pack(side="left")

        # --- CONSOLE LOG ---
        self.console_frame = ctk.CTkFrame(self.main_frame, fg_color="#12121A", corner_radius=10)
        self.console_frame.grid(row=2, column=0, sticky="nsew")

        header_row = ctk.CTkFrame(self.console_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(header_row, text="LIVE FEED", font=("Consolas", 11, "bold"), text_color="#8B8B9E").pack(side="left")
        self.log_count_label = ctk.CTkLabel(header_row, text="0", font=("Consolas", 10), text_color="#8B8B9E")
        self.log_count_label.pack(side="left", padx=8)

        self.console = ctk.CTkTextbox(
            self.console_frame, font=("Consolas", 11),
            text_color="#00FF88", fg_color="#050508",
            scrollbar_button_color="#1A1A2E", scrollbar_button_hover_color="#2A2A3E"
        )
        self.console.pack(fill="both", expand=True, padx=8, pady=8)
        self.console.configure(state="disabled")

        # --- FOOTER ---
        self.footer = ctk.CTkLabel(self, text="Built by RANA JAWAD | God Tier v3.0", font=("Consolas", 9), text_color="#8B8B9E")
        self.footer.grid(row=2, column=0, pady=5)

        # --- STATS BAR ---
        self.stats_frame = ctk.CTkFrame(self, fg_color="#0D0D15", corner_radius=0, height=40)
        self.stats_frame.grid(row=3, column=0, sticky="ew")

        self.stats_labels = {}
        stats = [("TOTAL", "0"), ("EMAIL", "0"), ("PHONE", "0"), ("HOT", "0"), ("WARM", "0"), ("COLD", "0")]
        for i, (name, val) in enumerate(stats):
            lbl = ctk.CTkLabel(self.stats_frame, text=f"{name}: {val}", font=("Consolas", 10, "bold"), text_color="#8B8B9E")
            lbl.pack(side="left", padx=15, pady=8)
            self.stats_labels[name.lower()] = lbl

        # Logic
        self.scraper = None
        self.is_running = False
        self.log_count = 0

    def update_console(self, message):
        self.console.configure(state="normal")
        self.console.insert("end", message + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")
        self.log_count += 1
        self.log_count_label.configure(text=str(self.log_count))

    def start_scraping(self):
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("Input Error", "Enter a search query!")
            return

        try:
            limit = int(self.limit_entry.get())
        except ValueError:
            messagebox.showwarning("Input Error", "Limit must be a number!")
            return

        source = self.source_var.get()

        self.is_running = True
        self.start_btn.configure(state="disabled", text="SCRAPING...", fg_color="#1A1A2E")
        self.stop_btn.configure(state="normal")
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        self.log_count = 0

        threading.Thread(target=self.run_scraper_thread, args=(query, limit, source), daemon=True).start()

    def stop_scraping(self):
        self.is_running = False
        self.update_console("\n[SYSTEM] Stop requested...")

    def run_scraper_thread(self, query, limit, source):
        try:
            self.scraper = UltimateScraper(log_callback=self.update_console, headless=self.headless_var.get())
            self.scraper.results = []

            if source == "google_maps":
                self.scraper.google_maps_scraper(query, limit)
            else:
                # For other sources, use Google Maps as fallback (CLI mode)
                # Full multi-source is available via web dashboard
                self.update_console(f"\n[INFO] {source} is optimized for web dashboard. Using Google Maps fallback in CLI mode.")
                self.scraper.google_maps_scraper(query, limit)

            self.update_console(f"\n[DONE] Scraping complete! Found {len(self.scraper.results)} results.")
            self.scraper.export_data(query_name=query)

            # Update stats
            total = len(self.scraper.results)
            email_count = sum(1 for r in self.scraper.results if r.get('email', 'N/A') != 'N/A')
            phone_count = sum(1 for r in self.scraper.results if r.get('phone', 'N/A') != 'N/A')
            self.stats_labels["total"].configure(text=f"TOTAL: {total}")
            self.stats_labels["email"].configure(text=f"EMAIL: {email_count}")
            self.stats_labels["phone"].configure(text=f"PHONE: {phone_count}")

        except Exception as e:
            self.update_console(f"\n[ERROR] {e}")
        finally:
            self.is_running = False
            self.start_btn.configure(state="normal", text="START SCRAPING", fg_color="#00D4FF")
            self.stop_btn.configure(state="disabled")

if __name__ == "__main__":
    app = ScraperGUI()
    app.mainloop()
