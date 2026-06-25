<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0A0A0F,50:00D4FF,100:00FF88&height=200&section=header&text=GOD%20TIER%20SCRAPER&fontSize=50&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Multi-Source%20Lead%20Generation%20Engine&descSize=16&descAlignY=55" width="100%"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.1.0-00D4FF?style=for-the-badge&labelColor=0A0A0F" />
  <img src="https://img.shields.io/badge/Python-3.10+-FFB800?style=for-the-badge&labelColor=0A0A0F&logo=python&logoColor=FFB800" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-00FF88?style=for-the-badge&labelColor=0A0A0F&logo=fastapi&logoColor=00FF88" />
  <img src="https://img.shields.io/badge/Selenium-4.0+-FF3366?style=for-the-badge&labelColor=0A0A0F&logo=selenium&logoColor=FF3366" />
  <img src="https://img.shields.io/badge/License-MIT-8B8B9E?style=for-the-badge&labelColor=0A0A0F" />
  <img src="https://img.shields.io/github/stars/ranajawadai/God-Tier-Data-Scraper?style=for-the-badge&labelColor=0A0A0F&color=FFB800&logo=github" />
</p>

<p align="center">
  <b>The most powerful open-source lead generation engine.</b><br/>
  Scrape businesses from Google Maps, Google Search, Yelp, and Yellow Pages.<br/>
  Extract emails, phone numbers, tech stacks, social links — with AI-powered lead scoring.<br/>
  <b>100% Free. No API keys. No limits.</b>
</p>

---

## What It Does

<table>
<tr>
<td width="50%">

### Multi-Source Scraping
- **Google Maps** — Business listings with deep crawl
- **Google Search** — Local business results
- **Yelp** — Restaurant & service listings
- **Yellow Pages** — Business directory extraction

</td>
<td width="50%">

### Smart Data Extraction
- Email addresses from business websites
- Phone numbers (international format)
- Business addresses & categories
- Tech stack detection (WordPress, Shopify, Stripe, FB Pixel...)
- Social media links (Facebook, Instagram, LinkedIn, TikTok, YouTube)

</td>
</tr>
<tr>
<td>

### AI Lead Scoring
- **HOT** — Has email + phone + website + marketing tech
- **WARM** — Has partial contact info
- **COLD** — Limited data available
- Score explanation for every lead

</td>
<td>

### Export Formats
- **CSV** — Google Sheets ready (UTF-8 BOM)
- **Excel** (.xlsx) — Formatted spreadsheet
- **JSON** — Developer-friendly structured data
- **PDF** — Professional report with table layout

</td>
</tr>
</table>

---

## The Dashboard

<p align="center">
  <img src="https://via.placeholder.com/900x500/0A0A0F/00D4FF?text=COMMAND+CENTER+DASHBOARD" width="90%" style="border-radius: 12px; border: 1px solid #1A1A2E;" />
</p>

### Dashboard Features
- **Particle stream header** — animated data flow visualization
- **7 stat cards** — Total, Email, Phone, Website, Hot, Warm, Cold
- **Live progress bar** — real-time scraping status
- **Results table** — sort, filter, search, pagination
- **Proxy management panel** — upload, validate, toggle, health ring
- **Connection status** — live backend monitoring
- **Keyboard shortcuts** — Ctrl+Enter to start, Escape to close

---

## Proxy System

Upload your own SOCKS5/HTTP proxy list and route all requests through proxies to avoid blocks.

### Supported Formats

**TXT** (one proxy per line)
```
socks5://174.75.211.193:4145
socks5://206.123.156.233:4476:user:pass
192.168.1.1:1080
```

**CSV** (with headers)
```csv
proxy,protocol,country
socks5://174.75.211.193:4145,socks5,US
```

**JSON** (array of objects)
```json
[
  {"ip": "174.75.211.193", "port": 4145, "type": "socks5"},
  {"ip": "206.123.156.233", "port": 4476, "type": "socks5", "user": "admin", "pass": "secret"}
]
```

### How It Works
1. Upload proxy file via dashboard (drag & drop or click)
2. Click **Validate** to test all proxies (5s timeout each)
3. Toggle proxy routing **ON**
4. Start scraping — every request uses the next proxy (Round Robin)
5. Dead proxies are automatically skipped

---

## Installation

### Quick Start

```bash
# Clone the repo
git clone https://github.com/ranajawadai/God-Tier-Data-Scraper.git
cd God-Tier-Data-Scraper

# Install dependencies
pip install -r requirements.txt

# Start the server
python backend_pro.py
```

Open `http://localhost:8000` in your browser.

### Desktop GUI

```bash
python scraper_gui_pro.py
```

### CLI Mode

```bash
python ultimate_scraper.py --headless
```

### Railway Deployment

```bash
# Already configured — just push to Railway
railway deploy
```

---

## Project Structure

```
God-Tier-Data-Scraper/
├── backend_pro.py          # FastAPI server + scraping engine
├── index.html              # Web dashboard (Command Center)
├── ultimate_scraper.py     # CLI scraper
├── scraper_gui_pro.py      # Desktop GUI (CustomTkinter)
├── config.json             # Centralized configuration
├── requirements.txt        # Python dependencies
├── Procfile                # Railway deployment
├── nixpacks.toml           # Railway build config
├── CLOUD_GUIDE.md          # Cloud deployment guide
└── RAILWAY_DEPLOY_GUIDE.md # Railway-specific guide
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Uvicorn |
| Scraping | Selenium + Chrome |
| Parsing | BeautifulSoup4 |
| Anti-Detection | Stealth scripts + UA rotation |
| Proxy System | SOCKS5/HTTP with auth extension |
| Dashboard | Tailwind CSS + Chart.js |
| Desktop GUI | CustomTkinter |
| Export | Pandas + ReportLab + openpyxl |
| Deployment | Railway + Nixpacks |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scrape` | POST | Start scraping job |
| `/api/stop` | GET | Stop current job |
| `/api/status` | GET | Get live status + logs |
| `/api/results` | GET | Get scraped data (paginated) |
| `/api/export` | GET | Export data (csv/xlsx/json/pdf) |
| `/api/proxy/upload` | POST | Upload proxy file |
| `/api/proxy/list` | GET | List all proxies + stats |
| `/api/proxy/toggle` | GET | Enable/disable proxy routing |
| `/api/proxy/validate` | POST | Test all proxies |
| `/api/proxy/clear` | DELETE | Remove all proxies |
| `/api/health` | GET | Health check |

---

## Configuration

Edit `config.json` to customize:

```json
{
    "default_limit": 50,
    "default_headless": true,
    "default_platform": "google_maps",
    "rate_limit_delay_ms": 1500,
    "max_scroll_attempts": 10,
    "enrichment_workers": 3,
    "request_timeout_seconds": 8
}
```

---

## How Lead Scoring Works

```
Email found       → +30 points
Phone found       → +25 points
Website found     → +15 points
FB Pixel/Stripe   → +20 points
Google Analytics  → +10 points

Score >= 60  → HOT
Score >= 30  → WARM
Score < 30   → COLD
```

---

## Star History

<p align="center">
  <a href="https://star-history.com/#ranajawadai/God-Tier-Data-Scraper&Date">
    <img src="https://api.star-history.com/svg?repos=ranajawadai/God-Tier-Data-Scraper&type=Date" width="600" />
  </a>
</p>

---

## Contributing

Contributions are welcome! Here's how:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Disclaimer

This tool is for **educational and research purposes only**. Respect the Terms of Service of target websites. Use responsibly and ethically.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Developer: Rana Jawad</b><br/>
  <a href="https://github.com/ranajawadai">
    <img src="https://img.shields.io/badge/GitHub-ranajawadai-181717?style=for-the-badge&logo=github&logoColor=white" />
  </a>
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0A0A0F,50:00D4FF,100:00FF88&height=100&section=footer" width="100%"/>
</p>
