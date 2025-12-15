# ☁️ HOW TO RUN THIS SCRAPER 24/7 FOR FREE (CLOUD GUIDE)

Want to run **10,000+ leads** while your laptop is OFF?
Follow this guide to host it on **AWS Cloud (Free Tier)**.

---

## ✅ STEP 1: Get a Free Cloud Computer (AWS EC2)

1. Go to [aws.amazon.com](https://aws.amazon.com/free/) and create a Free Account.
   - *Requires Credit Card for verification, but they won't charge if you stick to Free Tier.*
2. Go to **EC2 Dashboard** -> Click **Launch Instance**.
3. **Name**: `Scraper-Bot`
4. **OS (AMI)**: Select **Windows Server 2022 Base** (Free Tier Eligible).
5. **Instance Type**: Select `t2.micro` or `t3.micro`.
6. **Key Pair**: Create new key pair -> Download `.pem` file.
7. Click **Launch Instance**.

---

## ✅ STEP 2: Connect to Your Cloud Computer

1. Wait for the instance to start. Select it and click **Connect**.
2. Go to **RDP Client** tab.
3. Click **Get Password** -> Upload your `.pem` file -> Decrypt Password.
4. Open **Remote Desktop Connection** on your laptop.
5. Enter the **Public DNS** and **Password**.
6. BOOM! You are now inside a computer that runs 24/7 in the cloud.

---

## ✅ STEP 3: Setup the Scraper

Inside the AWS Cloud Computer:
1. Open Edge/Chrome and download **Python** (Install "Add to PATH").
2. Copy your **Ultimate-Data-Scraper** folder from your laptop to the Cloud Computer (Copy/Paste works via RDP).
3. Open CMD in that folder and run:
   ```cmd
   pip install -r requirements.txt
   ```

---

## ✅ STEP 4: Run in "Headless Mode" (Important!)

Cloud computers are slow with graphics. Use the new **Headless Mode** I added:

```cmd
python ultimate_scraper.py --headless
```

- This runs *without* opening the Chrome window (saves RAM).
- It will scrape silently in the background.
- You can close the Remote Desktop window, and it will **KEEP RUNNING**!

---

## ⚡ Power Saving Tip
When you are done, **Stop the Instance** in AWS Console so you don't waste free hours.
