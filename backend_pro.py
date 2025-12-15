import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import time
import os
import random
import pandas as pd
import json
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# --- CONFIGURATION ---
app = FastAPI(title="Ultimate Data Scraper PRO", version="2.5.0 (God Tier)")

# Enable CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENHANCED STATE & API ---
class SystemState:
    def __init__(self):
        self.is_running = False
        self.logs = [] # List of dicts {time, message}
        self.results = []
        self.proxy_list = []
        # Expanded Stats
        self.stats = {
            "total_leads": 0,
            "with_email": 0,
            "with_phone": 0,
            "hot_leads": 0,
            "warm_leads": 0,
            "cold_leads": 0
        }

state = SystemState()

def add_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    # Store structured log
    state.logs.append({"time": timestamp, "message": message})
    if len(state.logs) > 500: state.logs.pop(0)
    print(f"[{timestamp}] {message}")

def fetch_free_proxies():
    """Get free proxies for rotation"""
    add_log("Fetching fresh FREE proxies...", "PROXY")
    try:
        # Example source: proxylist.geonode.com (Free API)
        url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5) # Reduced timeout
        if r.status_code == 200:
            data = r.json()
            proxies = [f"{p['ip']}:{p['port']}" for p in data['data']]
            state.proxy_list = proxies
            add_log(f"Loaded {len(proxies)} proxies!", "SUCCESS")
        else:
            add_log("Failed to fetch proxies. Using direct connection.", "WARNING")
            state.proxy_list = [] # Fallback
    except Exception as e:
        add_log(f"Proxy Fetch Failed ({e}). Switching to Direct Mode.", "WARNING")
        state.proxy_list = [] # Fallback

# --- SCRAPING ENGINE ---
class ScraperEngine:
    def __init__(self):
        self.driver = None

    def start_browser(self, headless_req=True):
        options = Options()
        
        # INTELLIGENT MODE SWITCHING
        # If running on Railway/Cloud (Linux) OR explicit Headless env -> Force Headless
        # Also respect User Request if local
        is_cloud = os.getenv("RAILWAY_STATIC_URL") or os.getenv("DYNO") or os.name != 'nt'
        
        if is_cloud or headless_req:
            options.add_argument("--headless=new")
            add_log("Browser Mode: HEADLESS (Stealth)", "SYSTEM")
        else:
            add_log("Browser Mode: VISIBLE", "SYSTEM")

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Anti-detection tweaks
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Proxy Injection (Simple Rotation)
        if state.proxy_list:
            proxy = random.choice(state.proxy_list)
            options.add_argument(f'--proxy-server={proxy}')
            add_log(f"Using Proxy: {proxy}", "PROXY")

        try:
            service = Service(ChromeDriverManager().install())
        except:
            service = Service()
            
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Stealth scripts
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

    def analyze_tech_stack(self, html):
        stack = []
        if "wp-content" in html: stack.append("WordPress")
        if "shopify" in html: stack.append("Shopify")
        if "wix" in html: stack.append("Wix")
        if "fbq(" in html: stack.append("FB Pixel")
        if "UA-" in html or "G-" in html: stack.append("Google Analytics")
        return ", ".join(stack) if stack else "Unknown"

    def crawl_website_deep(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            # Try requests first for speed
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                text = soup.get_text()
                
                emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
                phones = set(re.findall(r'\+?\d[\d -]{8,15}\d', text))
                tech = self.analyze_tech_stack(r.text)
                
                return {
                    "emails": list(emails)[:2],
                    "phones": list(phones)[:2],
                    "tech": tech
                }
        except:
            return None
        return None

    def run_google_maps(self, query, limit, headless=True):
        add_log(f"Starting Google Maps Scraping for: {query}", "START")
        try:
            if not self.driver: self.start_browser(headless)
            
            self.driver.get(f"https://www.google.com/maps/search/{query}")
            time.sleep(5) # Wait for load
            
            # Consent Check
            try:
                consent_btn = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Reject all') or contains(@aria-label, 'Accept all')]")
                consent_btn.click()
                time.sleep(2)
            except: pass
            
            processed = set()
            scroll_fails = 0
            
            while len(state.results) < limit and state.is_running:
                # Scroll Logic (More Robust)
                # Try multiple selectors for results
                elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
                if not elements:
                    elements = self.driver.find_elements(By.CLASS_NAME, "hfpxzc") # Alternative class often used
                
                if not elements:
                    add_log("No results found. Scrolling to trigger load...", "WAIT")
                    # Try blind scroll
                    try:
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
                        # Also try clicking a canvas or main pane if possible
                        pane = self.driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", pane)
                    except:
                        pass
                        
                    time.sleep(3)
                    scroll_fails += 1
                    if scroll_fails > 5:
                        add_log("Could not find any results. Google blocking?", "ERROR")
                        break
                    continue
                
                scroll_fails = 0 # Reset fail counter
                
                for elem in elements:
                    if len(state.results) >= limit: break
                    link = elem.get_attribute("href")
                    if link in processed: continue
                    
                    processed.add(link)
                    try:
                        name = elem.get_attribute("aria-label")
                        if not name: continue
                        
                        # Basic Info
                        add_log(f"Found: {name}", "DATA")
                        
                        item = {
                            "name": name,
                            "link": link,
                            "emails": "N/A",
                            "phones": "N/A",
                            "tech": "N/A",
                            "lead_score": "Cold"
                        }
                        
                        # DEEP CRAWL (Simplified for stability in loop)
                        # In real world, do this async or partially
                        # For demo, let's fake check or do quick check if website in results
                        # Future: Add crawl logic here
                        
                        # AI Lead Scoring Logic
                        score = "Cold"
                        if "N/A" not in item.get("emails", "N/A") or "N/A" not in item.get("phones", "N/A"):
                            score = "Warm"
                        if "N/A" not in item.get("emails", "N/A") and "Pixel" in item.get("tech", ""):
                            score = "Hot"
                        
                        item["lead_score"] = score
                        state.results.append(item)
                        
                        # Update Stats
                        state.stats["total_leads"] += 1
                        if item.get("emails") != "N/A": state.stats["with_email"] += 1
                        if item.get("phones") != "N/A": state.stats["with_phone"] += 1
                        
                        if score == "Hot": state.stats["hot_leads"] += 1
                        elif score == "Warm": state.stats["warm_leads"] += 1
                        else: state.stats["cold_leads"] += 1
                        
                    except: continue

                # Scroll Down Safely
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", elements[-1])
                    time.sleep(2)
                except Exception as e:
                    add_log(f"Scrolling warning: {e}", "WARNING")
                    break
                
        except Exception as e:
            add_log(f"Scraping Error: {e}", "ERROR")
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
            state.is_running = False
            add_log("Scraping finished!", "DONE")

# --- API ROUTES ---

class ScrapeRequest(BaseModel):
    query: str
    limit: int = 50
    platform: str = "google_maps"
    use_proxy: bool = False
    headless: bool = True

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.post("/api/scrape")
def start_scraping_api(req: ScrapeRequest, background_tasks: BackgroundTasks):
    if state.is_running:
        raise HTTPException(status_code=400, detail="Scraper is already running")
    
    state.is_running = True
    state.results = []
    state.logs = []
    # Reset stats
    state.stats = {k: 0 for k in state.stats}
    
    if req.use_proxy:
        fetch_free_proxies()
    else:
        state.proxy_list = []

    scraper = ScraperEngine()
    background_tasks.add_task(scraper.run_google_maps, req.query, req.limit, req.headless)
    
    return {"status": "started", "message": f"Scraping started"}

@app.get("/api/status") # Frontend polls this
def get_status_api():
    return {
        "running": state.is_running,
        "total_leads": state.stats["total_leads"],
        "with_email": state.stats["with_email"],
        "with_phone": state.stats["with_phone"],
        "hot_leads": state.stats["hot_leads"],
        "warm_leads": state.stats["warm_leads"],
        "cold_leads": state.stats["cold_leads"],
        "logs": state.logs[-50:] # Send last 50 logs
    }

@app.get("/api/stats") # Alias
def get_stats_api():
    return get_status_api()

@app.get("/api/results")
def get_results_api():
    return state.results

@app.get("/api/stop")
def stop_scraping_api():
    state.is_running = False
    add_log("Stopping scraper...", "SYSTEM")
    return {"status": "stopped"}

@app.post("/api/export")
def export_data_post(format: str = "csv"):
    return export_data_get(format)

@app.get("/api/export")
def export_data_get(format: str = "csv"):
    if not state.results:
        raise HTTPException(status_code=400, detail="No data to export")
    
    df = pd.DataFrame(state.results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == "json":
        return state.results
        
    filename = f"export_{timestamp}.{format.replace('excel', 'xlsx')}"
    
    if "csv" in format:
        df.to_csv(filename, index=False)
    elif "xlsx" in format or "excel" in format:
        df.to_excel(filename, index=False)
        
    return FileResponse(filename, filename=filename)

# --- STARTUP ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # No browser launch logic
    add_log(f"Server starting on Port {port} (Cloud Ready)", "SYSTEM")
    uvicorn.run(app, host="0.0.0.0", port=port)
