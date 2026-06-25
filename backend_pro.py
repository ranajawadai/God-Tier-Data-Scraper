import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import threading
import time
import os
import random
import pandas as pd
import json
import requests
import re
import logging
import csv
import io
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
app = FastAPI(title="Ultimate Data Scraper PRO", version="3.1.0 (God Tier)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- USER AGENT POOL ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

def get_random_ua():
    return random.choice(USER_AGENTS)

# ==================== PROXY MANAGER ====================
class ProxyManager:
    def __init__(self):
        self.proxies = []  # List of {ip, port, user, pass, type, status, response_time}
        self.enabled = False
        self.lock = threading.Lock()
        self._current_idx = 0

    def parse_txt(self, content: str):
        """Parse TXT format: ip:port, ip:port:user:pass, or socks5://ip:port per line"""
        proxies = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Check if it's a URL format (socks5://ip:port or http://ip:port)
            if '://' in line:
                parsed = self._parse_proxy_url(line)
                if parsed:
                    proxies.append(parsed)
                continue

            # Standard ip:port format
            parts = line.split(':')
            if len(parts) >= 2:
                p = {
                    "ip": parts[0],
                    "port": int(parts[1]) if parts[1].isdigit() else 1080,
                    "user": parts[2] if len(parts) > 2 else "",
                    "pass": parts[3] if len(parts) > 3 else "",
                    "type": "socks5",
                    "status": "unknown",
                    "response_time": 0
                }
                proxies.append(p)
        return proxies

    def parse_csv(self, content: str):
        """Parse CSV format with headers. Supports:
        - ip, port, username, password, type
        - proxy, protocol (where proxy is socks5://ip:port)
        - host, port
        """
        proxies = []
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            # Check if 'proxy' column has full URL format (socks5://ip:port)
            proxy_url = row.get('proxy', row.get('url', '')).strip()
            if proxy_url and '://' in proxy_url:
                parsed = self._parse_proxy_url(proxy_url)
                if parsed:
                    parsed["type"] = row.get('protocol', row.get('type', parsed["type"])).lower()
                    proxies.append(parsed)
                continue

            # Standard ip/port column format
            ip = row.get('ip', row.get('host', '')).strip()
            port_str = row.get('port', '1080').strip()
            p = {
                "ip": ip,
                "port": int(port_str) if port_str.isdigit() else 1080,
                "user": row.get('username', row.get('user', row.get('auth_user', ''))).strip(),
                "pass": row.get('password', row.get('pass', row.get('auth_pass', ''))).strip(),
                "type": row.get('type', row.get('protocol', 'socks5')).strip().lower(),
                "status": "unknown",
                "response_time": 0
            }
            if p["ip"]:
                proxies.append(p)
        return proxies

    def _parse_proxy_url(self, url):
        """Parse proxy URL formats: socks5://ip:port, http://user:pass@ip:port"""
        try:
            url = url.strip()
            # Extract protocol
            proto = "socks5"
            if "://" in url:
                proto, rest = url.split("://", 1)
            else:
                rest = url

            # Extract user:pass@ if present
            user, pwd = "", ""
            if "@" in rest:
                auth, rest = rest.rsplit("@", 1)
                if ":" in auth:
                    user, pwd = auth.split(":", 1)
                else:
                    user = auth

            # Extract ip:port
            if ":" in rest:
                ip, port_str = rest.rsplit(":", 1)
                port = int(port_str) if port_str.isdigit() else 1080
            else:
                ip = rest
                port = 1080

            return {
                "ip": ip.strip(),
                "port": port,
                "user": user,
                "pass": pwd,
                "type": proto.lower().replace("socks4a", "socks4").replace("socks5h", "socks5"),
                "status": "unknown",
                "response_time": 0
            }
        except:
            return None

    def parse_json(self, content: str):
        """Parse JSON format: array of objects"""
        proxies = []
        data = json.loads(content)
        if isinstance(data, list):
            for item in data:
                p = {
                    "ip": item.get('ip', item.get('host', '')),
                    "port": int(item.get('port', 1080)),
                    "user": item.get('user', item.get('username', '')),
                    "pass": item.get('pass', item.get('password', '')),
                    "type": item.get('type', item.get('protocol', 'socks5')).lower(),
                    "status": "unknown",
                    "response_time": 0
                }
                if p["ip"]:
                    proxies.append(p)
        return proxies

    def upload(self, content: str, filename: str):
        """Auto-detect format and parse proxies"""
        with self.lock:
            ext = filename.lower().split('.')[-1] if '.' in filename else 'txt'

            if ext == 'json':
                new_proxies = self.parse_json(content)
            elif ext == 'csv':
                new_proxies = self.parse_csv(content)
            else:
                new_proxies = self.parse_txt(content)

            # Deduplicate
            existing = {f"{p['ip']}:{p['port']}" for p in self.proxies}
            added = 0
            for p in new_proxies:
                key = f"{p['ip']}:{p['port']}"
                if key not in existing:
                    self.proxies.append(p)
                    existing.add(key)
                    added += 1

            return added, len(new_proxies)

    def validate_all(self):
        """Test all proxies concurrently"""
        def test_proxy(idx, proxy):
            proxy_url = self._build_url(proxy)
            try:
                start = time.time()
                r = requests.get(
                    "http://httpbin.org/ip",
                    proxies={"http": proxy_url, "https": proxy_url},
                    timeout=5
                )
                elapsed = round((time.time() - start) * 1000)
                proxy["response_time"] = elapsed
                if r.status_code == 200:
                    proxy["status"] = "working" if elapsed < 2000 else "slow"
                else:
                    proxy["status"] = "dead"
            except requests.exceptions.Timeout:
                proxy["status"] = "dead"
                proxy["response_time"] = 5000
            except Exception:
                proxy["status"] = "dead"
                proxy["response_time"] = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(test_proxy, i, p) for i, p in enumerate(self.proxies)]
            for f in as_completed(futures):
                try: f.result()
                except: pass

        working = sum(1 for p in self.proxies if p["status"] in ("working", "slow"))
        dead = sum(1 for p in self.proxies if p["status"] == "dead")
        return working, dead

    def get_next(self):
        """Get next proxy via round robin"""
        if not self.enabled or not self.proxies:
            return None

        with self.lock:
            working = [p for p in self.proxies if p["status"] in ("working", "slow")]
            if not working:
                return None

            proxy = working[self._current_idx % len(working)]
            self._current_idx += 1
            return proxy

    def get_selenium_proxy(self):
        """Get proxy formatted for Selenium Chrome options"""
        proxy = self.get_next()
        if not proxy:
            return None, None, None

        proxy_str = f"{proxy['ip']}:{proxy['port']}"
        return proxy_str, proxy["type"], proxy

    def create_auth_extension(self, proxy):
        """Create a Chrome extension for SOCKS5/HTTP proxy authentication"""
        if not proxy or not proxy.get("user"):
            return None

        import zipfile
        import tempfile

        manifest = {
            "version": "1.0.0",
            "manifest_version": 3,
            "name": "Proxy Auth",
            "permissions": ["proxy", "webRequest", "webRequestAuthProvider"],
            "host_permissions": ["<all_urls>"],
            "background": {"service_worker": "background.js"},
            "minimum_chrome_version": "120"
        }

        bg_js = f"""
chrome.proxy.settings.set({{
    value: {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "{proxy.get('type', 'socks5')}",
                host: "{proxy['ip']}",
                port: {proxy['port']}
            }}
        }}
    }},
    scope: "regular"
}});

chrome.webRequest.onAuthRequired.addListener(
    (details) => {{
        return {{
            authCredentials: {{
                username: "{proxy['user']}",
                password: "{proxy['pass']}"
            }}
        }};
    }},
    {{urls: ["<all_urls>"]}},
    ["blocking"]
);
"""

        # For MV3, use different approach
        manifest3 = {
            "version": "1.0.0",
            "manifest_version": 3,
            "name": "Proxy Auth",
            "permissions": ["proxy"],
            "host_permissions": ["<all_urls>"],
            "background": {"service_worker": "background.js"},
            "minimum_chrome_version": "120"
        }

        bg_js_v3 = f"""
chrome.proxy.settings.set({{
    value: {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "{proxy.get('type', 'socks5')}",
                host: "{proxy['ip']}",
                port: {proxy['port']}
            }}
        }}
    }},
    scope: "regular"
}});
"""

        tmpdir = tempfile.mkdtemp()
        ext_path = os.path.join(tmpdir, "proxy_auth_ext")
        os.makedirs(ext_path, exist_ok=True)

        # Try MV3 first, fallback to MV2
        try:
            with open(os.path.join(ext_path, "manifest.json"), "w") as f:
                json.dump(manifest3, f)
            with open(os.path.join(ext_path, "background.js"), "w") as f:
                f.write(bg_js_v3)
        except:
            pass

        return ext_path

    def _build_url(self, proxy):
        ptype = proxy.get("type", "socks5")
        if proxy.get("user"):
            return f"{ptype}://{proxy['user']}:{proxy['pass']}@{proxy['ip']}:{proxy['port']}"
        return f"{ptype}://{proxy['ip']}:{proxy['port']}"

    def mark_dead(self, ip, port):
        """Mark a proxy as dead after failure"""
        with self.lock:
            for p in self.proxies:
                if p["ip"] == ip and p["port"] == port:
                    p["status"] = "dead"
                    break

    def clear(self):
        with self.lock:
            self.proxies = []
            self._current_idx = 0

    def get_stats(self):
        total = len(self.proxies)
        working = sum(1 for p in self.proxies if p["status"] == "working")
        slow = sum(1 for p in self.proxies if p["status"] == "slow")
        dead = sum(1 for p in self.proxies if p["status"] == "dead")
        unknown = sum(1 for p in self.proxies if p["status"] == "unknown")
        return {
            "total": total,
            "working": working,
            "slow": slow,
            "dead": dead,
            "unknown": unknown,
            "enabled": self.enabled
        }

proxy_manager = ProxyManager()

# --- STATE ---
class SystemState:
    def __init__(self):
        self.is_running = False
        self.should_stop = False
        self.logs = []
        self.results = []
        self.progress = {"current": 0, "total": 0, "stage": "idle"}
        self.stats = {
            "total_leads": 0,
            "with_email": 0,
            "with_phone": 0,
            "with_website": 0,
            "hot_leads": 0,
            "warm_leads": 0,
            "cold_leads": 0
        }

state = SystemState()

def add_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    state.logs.append({"time": timestamp, "message": message, "level": level})
    if len(state.logs) > 500:
        state.logs.pop(0)
    logger.info(f"[{level}] {message}")

def update_stats(item):
    state.stats["total_leads"] = len(state.results)
    if item.get("email") and item["email"] != "N/A":
        state.stats["with_email"] += 1
    if item.get("phone") and item["phone"] != "N/A":
        state.stats["with_phone"] += 1
    if item.get("website") and item["website"] != "N/A":
        state.stats["with_website"] += 1

    score = item.get("lead_score", "Cold")
    if score == "Hot":
        state.stats["hot_leads"] += 1
    elif score == "Warm":
        state.stats["warm_leads"] += 1
    else:
        state.stats["cold_leads"] += 1

def calculate_lead_score(item):
    """Calculate lead score with explanation"""
    reasons = []
    score = 0

    has_email = item.get("email") and item["email"] != "N/A"
    has_phone = item.get("phone") and item["phone"] != "N/A"
    has_website = item.get("website") and item["website"] != "N/A"
    tech = item.get("tech_stack", "")

    if has_email:
        score += 30
        reasons.append("Has email")
    if has_phone:
        score += 25
        reasons.append("Has phone")
    if has_website:
        score += 15
        reasons.append("Has website")
    if "Facebook Pixel" in tech or "Stripe" in tech:
        score += 20
        reasons.append("Active marketing tech")
    if "Google Analytics" in tech:
        score += 10
        reasons.append("Uses analytics")

    if score >= 60:
        return "Hot", ", ".join(reasons) if reasons else "Strong online presence"
    elif score >= 30:
        return "Warm", ", ".join(reasons) if reasons else "Partial contact info"
    else:
        return "Cold", ", ".join(reasons) if reasons else "Limited info available"

# --- BROWSER ENGINE ---
class BrowserManager:
    def __init__(self):
        self.driver = None

    def start(self, headless=True):
        options = Options()
        is_cloud = os.getenv("RAILWAY_STATIC_URL") or os.getenv("DYNO") or os.name != 'nt'

        if is_cloud or headless:
            options.add_argument("--headless=new")
            add_log("Browser: HEADLESS mode", "SYSTEM")
            if is_cloud:
                import shutil
                chrome_bin = shutil.which("chromium") or shutil.which("google-chrome")
                driver_bin = shutil.which("chromedriver")
                if chrome_bin:
                    options.binary_location = chrome_bin
                if driver_bin:
                    service = Service(executable_path=driver_bin)
                elif ChromeDriverManager:
                    service = Service(ChromeDriverManager().install())
                else:
                    service = Service()
            elif ChromeDriverManager:
                service = Service(ChromeDriverManager().install())
            else:
                service = Service()
        else:
            add_log("Browser: VISIBLE mode", "SYSTEM")
            if ChromeDriverManager:
                service = Service(ChromeDriverManager().install())
            else:
                service = Service()

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--window-size={random.choice(['1920,1080','1366,768','1536,864','1440,900'])}")
        options.add_argument(f"user-agent={get_random_ua()}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Proxy injection with auth support
        proxy_str, proxy_type, proxy_obj = proxy_manager.get_selenium_proxy()
        if proxy_str:
            if proxy_obj and proxy_obj.get("user"):
                # Use Chrome extension for authenticated proxies
                ext_path = proxy_manager.create_auth_extension(proxy_obj)
                if ext_path:
                    options.add_argument(f'--load-extension={ext_path}')
                    add_log(f"Using authenticated proxy: {proxy_str} ({proxy_type})", "PROXY")
                else:
                    options.add_argument(f'--proxy-server={proxy_str}')
                    add_log(f"Using proxy: {proxy_str} ({proxy_type})", "PROXY")
            else:
                options.add_argument(f'--proxy-server={proxy_str}')
                add_log(f"Using proxy: {proxy_str} ({proxy_type})", "PROXY")

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                window.chrome = { runtime: {} };
            """
        })
        add_log("Browser launched successfully", "SUCCESS")

    def quit(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def random_sleep(self, min_s=1, max_s=3):
        time.sleep(random.uniform(min_s, max_s))

# --- SCRAPER ENGINE ---
class ScraperEngine:
    def __init__(self):
        self.browser = BrowserManager()

    def stop_requested(self):
        return state.should_stop

    # ==================== GOOGLE MAPS ====================
    def scrape_google_maps(self, query, limit, headless=True):
        add_log(f"Google Maps scraping: {query} (limit: {limit})", "START")
        max_retries = 3 if proxy_manager.enabled else 1
        success = False

        for attempt in range(max_retries):
            if self.stop_requested():
                break
            try:
                if attempt > 0:
                    add_log(f"Retry {attempt + 1}/{max_retries} with next proxy...", "PROXY")
                    self.browser.quit()
                    time.sleep(1)

                self.browser.start(headless)
                driver = self.browser.driver
                driver.set_page_load_timeout(30)

                driver.get(f"https://www.google.com/maps/search/{query}")
                self.browser.random_sleep(3, 5)

                # Consent popup
                try:
                    consent = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Accept all') or contains(@aria-label, 'Reject all')]"))
                    )
                    consent.click()
                    self.browser.random_sleep(1, 2)
                except:
                    pass

                processed = set()
                scroll_fails = 0

                for scroll_num in range((limit // 5) + 10):
                    if self.stop_requested() or len(state.results) >= limit:
                        break

                    elements = []
                    for sel in ["a[href*='/maps/place/']", ".hfpxzc", "div[role='article'] a", "a[data-item-id]"]:
                        elements = driver.find_elements(By.CSS_SELECTOR, sel)
                        if elements:
                            break

                    if not elements:
                        try:
                            feed = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
                            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
                        except:
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                        self.browser.random_sleep(2, 3)
                        scroll_fails += 1
                        if scroll_fails > 5:
                            add_log("No more results found or Google is blocking", "WARNING")
                            break
                        continue

                    scroll_fails = 0

                    for elem in elements:
                        if self.stop_requested() or len(state.results) >= limit:
                            break
                        try:
                            link = elem.get_attribute("href")
                            if not link or link in processed:
                                continue
                            processed.add(link)
                            name = elem.get_attribute("aria-label") or elem.text.split('\n')[0]
                            if not name or name.strip() == "":
                                continue

                            rating = "N/A"
                            try:
                                parent = elem.find_element(By.XPATH, "./..")
                                rating_spans = parent.find_elements(By.CSS_SELECTOR, "span[role='img']")
                                if rating_spans:
                                    rating = rating_spans[0].get_attribute("aria-label")
                            except:
                                pass

                            item = {
                                "source": "Google Maps",
                                "name": name.strip(),
                                "rating": rating,
                                "link": link,
                                "address": "N/A", "phone": "N/A", "email": "N/A",
                                "website": "N/A", "tech_stack": "N/A",
                                "social_links": "N/A", "category": "N/A",
                            }
                            state.results.append(item)
                            add_log(f"Found: {name.strip()}", "DATA")
                        except:
                            continue

                    try:
                        feed = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
                    except:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    self.browser.random_sleep(1, 2)

                if len(state.results) > 0:
                    success = True
                    break
                else:
                    add_log("No results found, trying next proxy...", "WARNING")

            except Exception as e:
                error_msg = str(e)
                if "ERR_CONNECTION" in error_msg or "ERR_PROXY" in error_msg or "timeout" in error_msg.lower():
                    add_log(f"Proxy connection failed: {error_msg[:80]}...", "WARNING")
                    if proxy_manager.enabled:
                        proxy_manager.mark_dead(proxy_str if 'proxy_str' in dir() else "", 0)
                else:
                    add_log(f"Scraping error: {error_msg[:100]}", "ERROR")
                    break

        if success:
            add_log(f"Found {len(state.results)} businesses. Starting deep enrichment...", "SYSTEM")
            self.browser.quit()
            self._enrich_all_results()

        try:
            self.browser.quit()
        except:
            pass
        state.is_running = False
        add_log("Scraping finished!", "DONE")

    # ==================== GOOGLE SEARCH ====================
    def scrape_google_search(self, query, limit, headless=True):
        add_log(f"Google Search scraping: {query} (limit: {limit})", "START")
        try:
            self.browser.start(headless)
            driver = self.browser.driver

            search_query = f"{query} business contact email phone"
            driver.get(f"https://www.google.com/search?q={search_query}&num={min(limit, 100)}")
            self.browser.random_sleep(2, 4)

            # Handle consent
            try:
                consent = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Accept all') or contains(@aria-label, 'Reject all')]")
                consent.click()
                self.browser.random_sleep(1, 2)
            except:
                pass

            processed = set()
            page = 0

            while len(state.results) < limit and not self.stop_requested():
                page += 1
                add_log(f"Scanning page {page}...", "SYSTEM")

                # Extract search results
                results = driver.find_elements(By.CSS_SELECTOR, "div.g")

                for result in results:
                    if self.stop_requested() or len(state.results) >= limit:
                        break

                    try:
                        link_elem = result.find_element(By.CSS_SELECTOR, "a")
                        link = link_elem.get_attribute("href")
                        if not link or link in processed or "google.com" in link:
                            continue
                        processed.add(link)

                        title = result.find_element(By.CSS_SELECTOR, "h3").text
                        snippet = ""
                        try:
                            snippet = result.find_element(By.CSS_SELECTOR, ".VwiC3b").text
                        except:
                            pass

                        # Extract emails/phones from snippet
                        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                        phones = re.findall(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}', snippet)

                        item = {
                            "source": "Google Search",
                            "name": title,
                            "link": link,
                            "email": emails[0] if emails else "N/A",
                            "phone": phones[0] if phones else "N/A",
                            "website": link,
                            "address": "N/A",
                            "rating": "N/A",
                            "tech_stack": "N/A",
                            "social_links": "N/A",
                            "category": "N/A",
                        }

                        state.results.append(item)
                        add_log(f"Found: {title}", "DATA")

                    except:
                        continue

                # Try next page
                if len(state.results) < limit and not self.stop_requested():
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "a#pnnext")
                        next_btn.click()
                        self.browser.random_sleep(2, 3)
                    except:
                        add_log("No more pages available", "WARNING")
                        break

            # Enrich results
            add_log(f"Found {len(state.results)} results. Starting enrichment...", "SYSTEM")
            self.browser.quit()
            self._enrich_all_results()

        except Exception as e:
            add_log(f"Google Search error: {e}", "ERROR")
        finally:
            self.browser.quit()
            state.is_running = False
            add_log("Scraping finished!", "DONE")

    # ==================== YELP ====================
    def scrape_yelp(self, query, limit, headless=True):
        add_log(f"Yelp scraping: {query} (limit: {limit})", "START")
        try:
            self.browser.start(headless)
            driver = self.browser.driver

            # Format query for Yelp
            search_term = query.replace(" ", "+")
            driver.get(f"https://www.yelp.com/search?find_desc={search_term}&find_loc=")
            self.browser.random_sleep(3, 5)

            processed = set()
            page = 0

            while len(state.results) < limit and not self.stop_requested():
                page += 1

                # Extract business cards
                cards = driver.find_elements(By.CSS_SELECTOR, "div.container__09f24__21w3G, div.businessName__09f24__2IGlE, [class*='businessName']")

                if not cards:
                    # Try alternative selectors
                    cards = driver.find_elements(By.CSS_SELECTOR, "h3 a[href*='/biz/']")

                for card in cards:
                    if self.stop_requested() or len(state.results) >= limit:
                        break

                    try:
                        # Get link and name
                        link_elem = card
                        if card.tag_name != 'a':
                            links = card.find_elements(By.CSS_SELECTOR, "a[href*='/biz/']")
                            if not links:
                                continue
                            link_elem = links[0]

                        link = link_elem.get_attribute("href")
                        if not link or link in processed:
                            continue
                        processed.add(link)

                        name = link_elem.text.strip()
                        if not name:
                            continue

                        item = {
                            "source": "Yelp",
                            "name": name,
                            "link": link,
                            "email": "N/A",
                            "phone": "N/A",
                            "website": "N/A",
                            "address": "N/A",
                            "rating": "N/A",
                            "tech_stack": "N/A",
                            "social_links": "N/A",
                            "category": "N/A",
                        }

                        # Try to get rating
                        try:
                            parent = card.find_element(By.XPATH, "./ancestor::div[contains(@class,'container')]")
                            rating_elem = parent.find_element(By.CSS_SELECTOR, "[aria-label*='star'], [role='img']")
                            item["rating"] = rating_elem.get_attribute("aria-label") or "N/A"
                        except:
                            pass

                        state.results.append(item)
                        add_log(f"Found: {name}", "DATA")

                    except:
                        continue

                # Next page
                if len(state.results) < limit and not self.stop_requested():
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "a.next-link, a[aria-label='Next']")
                        next_btn.click()
                        self.browser.random_sleep(2, 3)
                    except:
                        add_log("No more Yelp pages", "WARNING")
                        break

            # Enrich
            add_log(f"Found {len(state.results)} Yelp results. Enriching...", "SYSTEM")
            self.browser.quit()
            self._enrich_all_results()

        except Exception as e:
            add_log(f"Yelp error: {e}", "ERROR")
        finally:
            self.browser.quit()
            state.is_running = False
            add_log("Scraping finished!", "DONE")

    # ==================== YELLOW PAGES ====================
    def scrape_yellowpages(self, query, limit, headless=True):
        add_log(f"Yellow Pages scraping: {query} (limit: {limit})", "START")
        try:
            self.browser.start(headless)
            driver = self.browser.driver

            search_term = query.replace(" ", "+")
            driver.get(f"https://www.yellowpages.com/search?search_terms={search_term}&geo_location_terms=")
            self.browser.random_sleep(3, 5)

            processed = set()
            page = 0

            while len(state.results) < limit and not self.stop_requested():
                page += 1

                # Extract listings
                listings = driver.find_elements(By.CSS_SELECTOR, ".result, .srp-listing, div[class*='result']")

                if not listings:
                    listings = driver.find_elements(By.CSS_SELECTOR, "div.info, div.business-card")

                for listing in listings:
                    if self.stop_requested() or len(state.results) >= limit:
                        break

                    try:
                        # Get name and link
                        name_elem = listing.find_elements(By.CSS_SELECTOR, "a.business-name, h2 a, h3 a, a[class*='name']")
                        if not name_elem:
                            continue

                        link = name_elem[0].get_attribute("href")
                        name = name_elem[0].text.strip()

                        if not name or not link or link in processed:
                            continue
                        processed.add(link)

                        # Make full URL
                        if link.startswith("/"):
                            link = f"https://www.yellowpages.com{link}"

                        # Get phone
                        phone = "N/A"
                        phone_elems = listing.find_elements(By.CSS_SELECTOR, ".phones, .phone, [class*='phone']")
                        if phone_elems:
                            phone = phone_elems[0].text.strip()

                        # Get address
                        address = "N/A"
                        addr_elems = listing.find_elements(By.CSS_SELECTOR, ".street-address, .address, [class*='address']")
                        if addr_elems:
                            address = addr_elems[0].text.strip()

                        # Get category
                        category = "N/A"
                        cat_elems = listing.find_elements(By.CSS_SELECTOR, ".categories, .category, [class*='category']")
                        if cat_elems:
                            category = cat_elems[0].text.strip()

                        item = {
                            "source": "Yellow Pages",
                            "name": name,
                            "link": link,
                            "email": "N/A",
                            "phone": phone,
                            "website": "N/A",
                            "address": address,
                            "rating": "N/A",
                            "tech_stack": "N/A",
                            "social_links": "N/A",
                            "category": category,
                        }

                        state.results.append(item)
                        add_log(f"Found: {name}", "DATA")

                    except:
                        continue

                # Next page
                if len(state.results) < limit and not self.stop_requested():
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "a.next, a[aria-label='Next'], .pagination .next a")
                        next_btn.click()
                        self.browser.random_sleep(2, 3)
                    except:
                        add_log("No more Yellow Pages results", "WARNING")
                        break

            # Enrich
            add_log(f"Found {len(state.results)} Yellow Pages results. Enriching...", "SYSTEM")
            self.browser.quit()
            self._enrich_all_results()

        except Exception as e:
            add_log(f"Yellow Pages error: {e}", "ERROR")
        finally:
            self.browser.quit()
            state.is_running = False
            add_log("Scraping finished!", "DONE")

    # ==================== DEEP ENRICHMENT ====================
    def _enrich_all_results(self):
        """Visit each business website for emails, phones, tech stack, social links"""
        total = len(state.results)
        if total == 0:
            return

        add_log(f"Starting deep enrichment on {total} businesses...", "SYSTEM")

        def enrich_single(idx, item):
            if self.stop_requested():
                return
            try:
                state.progress["current"] = idx + 1
                state.progress["stage"] = f"Enriching {item['name'][:30]}"

                # If we have a Google Maps link, visit it for details
                if item.get("source") == "Google Maps" and "/maps/place/" in item.get("link", ""):
                    self._enrich_from_gmaps(item)

                # Visit business website for emails/tech
                website = item.get("website", "N/A")
                if website and website != "N/A" and "google" not in website.lower():
                    self._crawl_website(item)

                # Calculate lead score
                score, explanation = calculate_lead_score(item)
                item["lead_score"] = score
                item["score_reason"] = explanation

                add_log(f"[{idx+1}/{total}] {item['name'][:30]} -> {score}", "DATA")

            except Exception as e:
                add_log(f"Enrich error for {item.get('name', '?')}: {e}", "WARNING")

        # Use thread pool for parallel enrichment
        state.progress["total"] = total
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for i, item in enumerate(state.results):
                if self.stop_requested():
                    break
                futures.append(executor.submit(enrich_single, i, item))
                time.sleep(0.2)  # Small delay between submissions

            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass

        state.progress["stage"] = "Complete"
        add_log(f"Deep enrichment complete!", "SUCCESS")

    def _enrich_from_gmaps(self, item):
        """Visit Google Maps page to extract phone, address, website"""
        try:
            browser = BrowserManager()
            browser.start(headless=True)
            driver = browser.driver

            driver.get(item["link"])
            browser.random_sleep(2, 3)

            # Phone
            try:
                phone_btn = driver.find_element(By.CSS_SELECTOR, "button[data-tooltip='Copy phone number']")
                item["phone"] = phone_btn.get_attribute("aria-label").replace("Copy phone number", "").strip()
            except:
                try:
                    phone_btns = driver.find_elements(By.CSS_SELECTOR, "button[data-item-id^='phone:']")
                    if phone_btns:
                        item["phone"] = phone_btns[0].get_attribute("aria-label").replace("Phone: ", "").strip()
                except:
                    pass

            # Website
            try:
                web_elem = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
                item["website"] = web_elem.get_attribute("href")
            except:
                pass

            # Address
            try:
                addr_elem = driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']")
                item["address"] = addr_elem.get_attribute("aria-label").replace("Address: ", "").strip()
            except:
                pass

            # Category
            try:
                cat_elem = driver.find_element(By.CSS_SELECTOR, "button[jsaction*='category'], span[class*='category']")
                item["category"] = cat_elem.text.strip()
            except:
                pass

            browser.quit()

        except Exception as e:
            pass

    def _crawl_website(self, item):
        """Crawl business website for emails, social links, tech stack"""
        website = item.get("website", "N/A")
        if not website or website == "N/A":
            return

        try:
            headers = {'User-Agent': get_random_ua()}
            response = requests.get(website, headers=headers, timeout=8, allow_redirects=True)

            if response.status_code != 200:
                return

            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()

            # Emails
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
            valid_emails = [e for e in emails if not e.endswith(('png', 'jpg', 'jpeg', 'gif', 'css', 'js', 'svg', 'webp'))]
            if valid_emails and item.get("email", "N/A") == "N/A":
                item["email"] = valid_emails[0]

            # Additional phones
            if item.get("phone", "N/A") == "N/A":
                phones = re.findall(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}', text)
                clean_phones = [p.strip() for p in phones if len(re.sub(r'[^\d]', '', p)) >= 7]
                if clean_phones:
                    item["phone"] = clean_phones[0]

            # Tech stack
            techs = []
            if "wp-content" in html or "WordPress" in html:
                techs.append("WordPress")
            if "shopify" in html:
                techs.append("Shopify")
            if "wix.com" in html:
                techs.append("Wix")
            if "squarespace" in html:
                techs.append("Squarespace")
            if "joomla" in html:
                techs.append("Joomla")
            if "UA-" in html or "G-" in html or "googletagmanager" in html:
                techs.append("Google Analytics")
            if "fbevents.js" in html or "fbq(" in html:
                techs.append("Facebook Pixel")
            if "stripe" in html.lower():
                techs.append("Stripe")
            if "paypal" in html.lower():
                techs.append("PayPal")

            if techs:
                item["tech_stack"] = ", ".join(techs)

            # Social links
            socials = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                for domain in ['facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com', 'tiktok.com', 'youtube.com']:
                    if domain in href:
                        socials.append(href)
                        break
            if socials:
                item["social_links"] = ", ".join(list(set(socials))[:5])

        except requests.exceptions.Timeout:
            pass
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            pass

# --- API MODELS ---
class ScrapeRequest(BaseModel):
    query: str
    limit: int = 50
    platform: str = "google_maps"
    headless: bool = True

class ExportRequest(BaseModel):
    format: str = "csv"

# --- API ROUTES ---
@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "3.1.0", "timestamp": datetime.now().isoformat()}

# --- PROXY ENDPOINTS ---
@app.post("/api/proxy/upload")
async def upload_proxy(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode('utf-8', errors='ignore')
    added, total = proxy_manager.upload(text, file.filename)
    add_log(f"Uploaded {file.filename}: {added} new proxies ({total} total in file)", "PROXY")
    return {"added": added, "total_in_file": total, "total_loaded": len(proxy_manager.proxies)}

@app.get("/api/proxy/list")
def list_proxies():
    return {
        "proxies": proxy_manager.proxies,
        "stats": proxy_manager.get_stats()
    }

@app.get("/api/proxy/toggle")
def toggle_proxy():
    proxy_manager.enabled = not proxy_manager.enabled
    status = "ENABLED" if proxy_manager.enabled else "DISABLED"
    add_log(f"Proxy routing: {status}", "PROXY")
    return {"enabled": proxy_manager.enabled}

@app.post("/api/proxy/validate")
def validate_proxies():
    if not proxy_manager.proxies:
        raise HTTPException(status_code=400, detail="No proxies loaded")
    add_log(f"Validating {len(proxy_manager.proxies)} proxies...", "PROXY")
    working, dead = proxy_manager.validate_all()
    add_log(f"Validation complete: {working} working, {dead} dead", "PROXY")
    return {"working": working, "dead": dead, "stats": proxy_manager.get_stats()}

@app.delete("/api/proxy/clear")
def clear_proxies():
    count = len(proxy_manager.proxies)
    proxy_manager.clear()
    add_log(f"Cleared {count} proxies", "PROXY")
    return {"cleared": count}

@app.post("/api/scrape")
def start_scraping(req: ScrapeRequest, background_tasks: BackgroundTasks):
    if state.is_running:
        raise HTTPException(status_code=400, detail="Scraper is already running. Stop it first.")

    state.is_running = True
    state.should_stop = False
    state.results = []
    state.logs = []
    state.progress = {"current": 0, "total": 0, "stage": "starting"}
    state.stats = {k: 0 for k in state.stats}

    engine = ScraperEngine()

    # Select platform
    platform_map = {
        "google_maps": engine.scrape_google_maps,
        "google_search": engine.scrape_google_search,
        "yelp": engine.scrape_yelp,
        "yellowpages": engine.scrape_yellowpages,
    }

    scrape_func = platform_map.get(req.platform, engine.scrape_google_maps)
    background_tasks.add_task(scrape_func, req.query, req.limit, req.headless)

    add_log(f"Started {req.platform} scraping for: {req.query}", "SYSTEM")
    return {"status": "started", "platform": req.platform, "query": req.query}

@app.get("/api/stop")
def stop_scraping():
    state.should_stop = True
    state.is_running = False
    add_log("Stop requested by user", "SYSTEM")
    return {"status": "stopping"}

@app.get("/api/status")
def get_status():
    return {
        "running": state.is_running,
        "progress": state.progress,
        "total_leads": state.stats["total_leads"],
        "with_email": state.stats["with_email"],
        "with_phone": state.stats["with_phone"],
        "with_website": state.stats.get("with_website", 0),
        "hot_leads": state.stats["hot_leads"],
        "warm_leads": state.stats["warm_leads"],
        "cold_leads": state.stats["cold_leads"],
        "logs": state.logs[-50:],
    }

@app.get("/api/results")
def get_results(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None
):
    results = state.results
    if search:
        search_lower = search.lower()
        results = [r for r in results if search_lower in r.get("name", "").lower()
                   or search_lower in r.get("email", "").lower()
                   or search_lower in r.get("phone", "").lower()]

    total = len(results)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": results[offset:offset+limit]
    }

@app.get("/api/export")
def export_data(format: str = "csv"):
    if not state.results:
        raise HTTPException(status_code=400, detail="No data to export")

    df = pd.DataFrame(state.results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ensure all columns exist
    for col in ["name", "email", "phone", "website", "address", "rating", "tech_stack", "social_links", "lead_score", "score_reason", "source", "category"]:
        if col not in df.columns:
            df[col] = "N/A"
    df = df.fillna("N/A")

    if format == "json":
        return JSONResponse(content=state.results)

    filename = f"scrape_export_{timestamp}.{format.replace('excel', 'xlsx')}"

    if "csv" in format:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
    elif "xlsx" in format or "excel" in format:
        df.to_excel(filename, index=False)
    elif "pdf" in format:
        _create_pdf_report(filename, df)

    return FileResponse(filename, filename=filename)

@app.post("/api/export")
def export_data_post(req: ExportRequest):
    return export_data(req.format)

def _create_pdf_report(filename, df):
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch

    c = canvas.Canvas(filename, pagesize=landscape(letter))
    width, height = landscape(letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "GOD TIER DATA SCRAPER - EXPORT REPORT")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Records: {len(df)}")
    c.line(50, height - 80, width - 50, height - 80)

    y = height - 100
    line_height = 18
    cols = ["name", "email", "phone", "website", "lead_score"]
    col_widths = [200, 200, 120, 200, 60]

    # Header
    c.setFont("Helvetica-Bold", 9)
    x = 50
    for i, col in enumerate(cols):
        c.drawString(x, y, col.upper())
        x += col_widths[i]
    y -= line_height
    c.line(50, y + 5, width - 50, y + 5)

    # Rows
    c.setFont("Helvetica", 8)
    for _, row in df.iterrows():
        if y < 50:
            c.showPage()
            y = height - 50

        x = 50
        for i, col in enumerate(cols):
            text = str(row.get(col, "N/A"))[:35]
            c.drawString(x, y, text)
            x += col_widths[i]
        y -= line_height

    c.save()

# --- STARTUP ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    add_log(f"Server starting on port {port}", "SYSTEM")
    uvicorn.run(app, host="0.0.0.0", port=port)
