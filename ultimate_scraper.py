"""
ULTIMATE DATA SCRAPER - "NO LIMIT" EDITION
Powered by ETH-MENTOR

Features:
- Google Maps Business Extractor (Infinite Scroll)
- Social Media Email/Phone Hunter
- Multi-threaded Architecture
- Premium Exports: CSV, PDF, DOCX
- Anti-Detection System

dependencies: selenium, pandas, reportlab, python-docx, webdriver-manager, beautifulsoup4
"""

import os
import sys
import time
import random
import threading
import csv
import json
import logging
import re
import argparse
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Try to import dependencies, warn if missing
try:
    import pandas as pd
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from docx import Document
except ImportError as e:
    print(f"\n[!] Missing critical dependency: {e.name}")
    print(f"[*] Please run: pip install selenium pandas reportlab python-docx webdriver-manager beautifulsoup4")
    sys.exit(1)

# Configuration & Colors
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

logging.basicConfig(
    filename='scraper_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class UltimateScraper:
    def __init__(self, log_callback=None, headless=False):
        self.results = []
        self.driver = None
        self.lock = threading.Lock()
        self.log_callback = log_callback
        self.headless = headless
        # Enable Windows ANSI colors
        if os.name == 'nt':
            os.system('color')

    def log(self, message, color=Colors.END):
        """Dual logging: Print to console AND send to GUI"""
        print(f"{message}{Colors.END}")
        if self.log_callback:
            # Strip ANSI color codes for GUI
            clean_msg = re.sub(r'\x1b\[[0-9;]*m', '', message)
            self.log_callback(clean_msg)
        
    def setup_driver(self):
        """Setup Chrome Driver with Anti-Detection"""
        self.log(f"{Colors.YELLOW}[*] Initializing Chrome Browser... (Please Wait){Colors.END}")
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
            self.log(f"{Colors.MAGENTA}[*] Running in HEADLESS Mode (No Window){Colors.END}")
            
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-notifications")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Anti-detection tweaks
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try using WebDriver Manager
            service = Service(ChromeDriverManager().install())
        except:
            # Fallback to default Selenium Manager
            service = Service()

        driver = webdriver.Chrome(service=service, options=options)
        
        # Stealth scripts
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        self.log(f"{Colors.GREEN}[+] Browser Launched Successfully!{Colors.END}")
        return driver

    def random_sleep(self, min_sec=1, max_sec=3):
        time.sleep(random.uniform(min_sec, max_sec))

    def google_maps_scraper(self, query, limit=50):
        self.log(f"\n{Colors.CYAN}[*] Starting Google Maps Scraper for: {Colors.YELLOW}{query}{Colors.END}")

        try:
            self.driver = self.setup_driver()

            url = f"https://www.google.com/maps/search/{query}"
            self.log(f"{Colors.CYAN}[*] Navigating to Google Maps...{Colors.END}")
            self.driver.get(url)
            self.random_sleep(3, 5)

            self.log(f"{Colors.GREEN}[+] Page loaded. Analyzing results...{Colors.END}")

            scraped_count = 0
            processed_urls = set()
            scroll_fails = 0

            # Infinite Scroll Logic
            while scraped_count < limit:
                try:
                    # Try multiple selectors for feed container
                    feed = None
                    for selector in ["div[role='feed']", "div[role='main']", "div.m6QErb"]:
                        try:
                            feed = self.driver.find_element(By.CSS_SELECTOR, selector)
                            break
                        except: continue

                    if feed:
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
                    else:
                        # Fallback: scroll the page body
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

                    self.random_sleep(1, 2)

                    # Try multiple selectors for result elements
                    elements = []
                    for selector in ["div[role='article']", "a[href*='/maps/place/']", ".hfpxzc"]:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            break

                    if not elements:
                        scroll_fails += 1
                        if scroll_fails > 5:
                            self.log(f"{Colors.RED}[!] Could not find results after {scroll_fails} attempts. Google may be blocking.{Colors.END}")
                            break
                        continue

                    scroll_fails = 0

                    for elem in elements:
                        if scraped_count >= limit:
                            break

                        try:
                            # Get link
                            link = None
                            if elem.tag_name == 'a':
                                link = elem.get_attribute("href")
                            else:
                                link_elem = elem.find_element(By.CSS_SELECTOR, "a")
                                link = link_elem.get_attribute("href")

                            if not link or link in processed_urls:
                                continue

                            # Extract basic data visible in list
                            text_content = elem.text.split('\n')
                            name = text_content[0] if len(text_content) > 0 else "N/A"
                            if not name or name == "N/A":
                                name = elem.get_attribute("aria-label") or "N/A"

                            rating = "N/A"
                            try:
                                rating_elem = elem.find_element(By.CSS_SELECTOR, "span[role='img']")
                                rating = rating_elem.get_attribute("aria-label")
                            except: pass

                            data = {
                                "source": "Google Maps",
                                "name": name,
                                "rating": rating,
                                "link": link,
                                "address": "Scanning...",
                                "phone": "Scanning...",
                                "website": "Scanning..."
                            }

                            self.results.append(data)
                            processed_urls.add(link)
                            scraped_count += 1

                            self.log(f"{Colors.GREEN}[+] Found: {name}{Colors.END}")

                        except Exception as e:
                            continue

                    # Check if end of list
                    page_source = self.driver.page_source
                    if "You've reached the end of the list" in page_source or "No more results" in page_source:
                        self.log(f"{Colors.YELLOW}[!] Reached end of results.{Colors.END}")
                        break

                except Exception as e:
                    self.log(f"{Colors.RED}[!] Scrolling error: {e}{Colors.END}")
                    scroll_fails += 1
                    if scroll_fails > 3:
                        break

            self.log(f"\n{Colors.CYAN}[*] Basic scan complete. Found {len(self.results)} businesses. Now enriching data (Deep Scan)...{Colors.END}")
            self.driver.quit()

            # Deep Scan (Visit each link for details)
            self.enrich_data()

        except Exception as e:
            self.log(f"{Colors.RED}[!] Critical Error: {e}{Colors.END}")
            if self.driver:
                try: self.driver.quit()
                except: pass

    def enrich_data(self):
        """Deep Scan: Visit G-Maps links AND Business Websites for Emails"""
        self.driver = self.setup_driver()

        total = len(self.results)
        self.log(f"\n{Colors.CYAN}[*] Starting GOD TIER Deep Scan on {total} businesses...{Colors.END}")
        self.log(f"{Colors.YELLOW}[*] This includes visiting their websites to hunt for Emails!{Colors.END}\n")

        enriched = 0
        try:
            for i, item in enumerate(self.results, 1):
                try:
                    self.log(f"  [{i}/{total}] Analyzing: {Colors.BOLD}{item['name']}{Colors.END}")
                    self.driver.get(item['link'])
                    self.random_sleep(1, 2)

                    # Extract phone
                    try:
                        phone_elem = self.driver.find_element(By.CSS_SELECTOR, "button[data-tooltip='Copy phone number']")
                        item['phone'] = phone_elem.get_attribute("aria-label").replace("Copy phone number", "").strip()
                    except:
                        try:
                            actions = self.driver.find_elements(By.CSS_SELECTOR, "button[data-item-id^='phone:']")
                            if actions: item['phone'] = actions[0].get_attribute("aria-label").replace("Phone: ", "").strip()
                        except: pass

                    # Extract website
                    try:
                        web_elem = self.driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
                        item['website'] = web_elem.get_attribute("href")
                    except: pass

                    # Extract address
                    try:
                        addr_elem = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']")
                        item['address'] = addr_elem.get_attribute("aria-label").replace("Address: ", "").strip()
                    except: pass

                    # Visit website for emails & socials
                    if item.get('website') and "google" not in item['website']:
                        self.log(f"      {Colors.MAGENTA}-> Visiting Website to hunt Emails...{Colors.END}")
                        self.crawl_website(item)

                    enriched += 1

                except Exception as e:
                    self.log(f"  {Colors.RED}[!] Error enriching {item.get('name', '?')}: {e}{Colors.END}")
                    continue
        finally:
            self.driver.quit()
            self.log(f"\n{Colors.GREEN}[+] Deep Scan complete: {enriched}/{total} businesses enriched.{Colors.END}")

    def crawl_website(self, item):
        """Visit business website and extract emails/social links + TECH STACK"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            try:
                response = requests.get(item['website'], headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text()
                    html_content = response.text

                    # Detect CMS
                    cms = "Custom/Unknown"
                    if "wp-content" in html_content or "WordPress" in html_content:
                        cms = "WordPress"
                    elif "shopify" in html_content:
                        cms = "Shopify"
                    elif "wix.com" in html_content:
                        cms = "Wix"
                    elif "squarespace" in html_content:
                        cms = "Squarespace"
                    elif "joomla" in html_content:
                        cms = "Joomla"
                    item['cms'] = cms

                    # Detect Marketing Tech
                    valuable_tech = []
                    if "UA-" in html_content or "G-" in html_content or "googletagmanager" in html_content:
                        valuable_tech.append("Google Analytics")
                    if "fbevents.js" in html_content or "fbq(" in html_content:
                        valuable_tech.append("Facebook Pixel")
                    if "shopify.com" in html_content:
                        valuable_tech.append("Shopify Pay")
                    if "stripe" in html_content:
                        valuable_tech.append("Stripe")
                    item['tech_stack'] = ", ".join(valuable_tech) if valuable_tech else "None"

                    self.log(f"      {Colors.BLUE}[⚡] Tech Detected: {cms} | {item['tech_stack']}{Colors.END}")

                    # Extract Emails
                    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
                    valid_emails = [e for e in emails if not e.endswith(('png','jpg','jpeg','gif','css','js'))]
                    if valid_emails:
                        item['email'] = ", ".join(valid_emails[:3])
                        self.log(f"      {Colors.GREEN}[$] Emails Found: {item['email']}{Colors.END}")
                    else:
                        item['email'] = "N/A"

                    # Extract Social Links
                    socials = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if any(s in href for s in ['facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com']):
                            socials.append(href)
                    item['social_links'] = ", ".join(list(set(socials))[:3])
                else:
                    self.log(f"      {Colors.YELLOW}[!] Website returned {response.status_code}{Colors.END}")
                    item['email'] = "N/A"
                    item['cms'] = "N/A"
                    item['tech_stack'] = "N/A"
            except requests.exceptions.Timeout:
                self.log(f"      {Colors.YELLOW}[!] Website timeout: {item['website']}{Colors.END}")
                item['email'] = "N/A"
                item['cms'] = "N/A"
                item['tech_stack'] = "N/A"
            except requests.exceptions.ConnectionError:
                self.log(f"      {Colors.YELLOW}[!] Cannot connect: {item['website']}{Colors.END}")
                item['email'] = "N/A"
                item['cms'] = "N/A"
                item['tech_stack'] = "N/A"
            except Exception as e:
                self.log(f"      {Colors.RED}[!] Crawl error: {e}{Colors.END}")
                item['email'] = "N/A"
                item['cms'] = "N/A"
                item['tech_stack'] = "N/A"
        except Exception as e:
            self.log(f"      {Colors.RED}[!] Website crawl failed: {e}{Colors.END}")
            item['email'] = "N/A"
            item['cms'] = "N/A"
            item['tech_stack'] = "N/A"

    def export_data(self, query_name="export"):
        if not self.results:
            self.log(f"\n{Colors.RED}[!] No data to export.{Colors.END}")
            return

        # Clean filename logic (God Tier Request)
        safe_name = "".join([c if c.isalnum() else "_" for c in query_name])
        timestamp = datetime.now().strftime("%Y%m%d")
        base_filename = f"{safe_name}_{timestamp}"
        
        self.log(f"\n{Colors.CYAN}[*] Exporting data to Google Sheet Ready Formats...{Colors.END}")
        
        df = pd.DataFrame(self.results)
        
        # REORDER COLUMNS (User Request: Name first, then Email, Phone, Website, Address)
        desired_order = ['name', 'email', 'phone', 'website', 'cms', 'tech_stack', 'address', 'rating', 'social_links', 'link']
        # Add missing columns with N/A
        for col in desired_order:
            if col not in df.columns:
                df[col] = "N/A"
        
        # Filling NaNs
        df = df.fillna("N/A")
        
        # Select and reorder
        df = df[desired_order]
        
        # 1. CSV EXPORT (Google Sheets Ready)
        csv_file = f"{base_filename}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig') # utf-8-sig for proper Excel display
        self.log(f"{Colors.GREEN}[+] Google Sheet CSV Saved: {Colors.BOLD}{csv_file}{Colors.END}")
        
        # 2. EXCEL EXPORT (Optional but premium)
        try:
            xlsx_file = f"{base_filename}.xlsx"
            df.to_excel(xlsx_file, index=False)
            self.log(f"{Colors.GREEN}[+] Excel File Saved: {Colors.BOLD}{xlsx_file}{Colors.END}")
        except: pass

        # 3. PDF REPORT
        pdf_file = f"{base_filename}_Report.pdf"
        try:
            self.create_pdf_report(pdf_file, df)
            self.log(f"{Colors.GREEN}[+] PDF Report Saved: {pdf_file}{Colors.END}")
        except: pass

    def create_pdf_report(self, filename, df):
        c = canvas.Canvas(filename, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "ULTIMATE DATA SCRAPER - GOD TIER REPORT")
        c.setFont("Helvetica", 10)
        c.drawString(50, 735, f"Generated on: {datetime.now()}")
        c.line(50, 730, 550, 730)
        
        y = 700
        for index, row in df.iterrows():
            if y < 100:
                c.showPage()
                y = 750
            
            # Format: Name | Email | Phone
            text = f"{str(row['name'])[:30]} | {str(row['email'])[:30]} | {str(row['phone'])[:15]}"
            c.drawString(50, y, text)
            y -= 20
        c.save()

def print_banner():
    print(f"""{Colors.MAGENTA}
   _____  ____  _____     _______ _____ ______ _____
  / ____|/ __ \\|  __ \\   |__   __|_   _|  ____|  __ \\
 | |  __| |  | | |  | |     | |    | | | |__  | |__) |
 | | |_ | |  | | |  | |     | |    | | |  __| |  _  /
 | |__| | |__| | |__| |     | |   _| |_| |____| | \\ \\
  \\_____|\\____/|_____/      |_|  |_____|______|_|  \\_\\

    GOD TIER DATA EXTRACTOR - GOOGLE SHEETS READY
    {Colors.END}""")

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Ultimate Data Scraper - God Tier")
        parser.add_argument("--headless", action="store_true", help="Run in headless mode (no browser window)")
        args = parser.parse_args()
        
        print_banner()
        scraper = UltimateScraper(headless=args.headless)
        
        # Enable Windows ANSI colors
        if os.name == 'nt':
            os.system('color')
        
        while True:
            print(f"\n{Colors.CYAN}=== GOD TIER MENU ==={Colors.END}")
            print("1. Google Maps Beast Mode (Scrape + Email Hunt)")
            print("2. Export Last Session")
            print("0. Exit")
            
            choice = input(f"\n{Colors.YELLOW}Select Option: {Colors.END}")
            
            if choice == '1':
                query = input("Enter Business Niche & Location (e.g., 'Dentist in New York'): ")
                try:
                    limit_input = input("Enter Limit (Press Enter for 50): ")
                    limit = int(limit_input) if limit_input.isdigit() else 50
                except: limit = 50
                
                scraper.google_maps_scraper(query, limit)
                scraper.export_data(query_name=query) # Auto export after scrape
                
            elif choice == '2':
                name = input("Enter query name for filename: ")
                scraper.export_data(query_name=name)
                
            elif choice == '0':
                print("Exiting...")
                break
                
    except ImportError as e:
        print(f"Missing dependency: {e}")
        input("Press Enter to exit")
    except Exception as e:
        print(f"Critical Error: {e}")
        input("Press Enter to exit")
