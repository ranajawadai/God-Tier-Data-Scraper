# 🚂 Railway Deployment Guide (God Tier Scraper)

Simple steps to deploy your Python Scraper backend to the cloud for free/cheap 24/7 operation.

## 1. Prerequisites
- GitHub Account (with the code uploaded).
- Railway Account (Login at [railway.app](https://railway.app)).

## 2. Create Project
1. Go to your **Railway Dashboard**.
2. Click **"New Project"**.
3. Select **"Deploy from GitHub repo"**.
4. Search for and select your repository: `God-Tier-Data-Scraper` (or whatever you named it).
5. Click **"Deploy Now"**.

## 3. Important Settings (The Magic Step)
Once the project is created, it might fail initially or waiting for config. **Do this immediately:**

1. Click on the card representing your project.
2. Go to the **"Settings"** tab.
3. Scroll down to **"Networking"**.
4. Click **"Generate Domain"**.
   - You will get a URL like: `ultimate-scraper-production.up.railway.app`
   - **COPY THIS URL.** You will need it later.

5. Go to the **"Variables"** tab.
6. Click **"New Variable"**.
   - **VARIABLE_NAME:** `PORT`
   - **VALUE:** `8000`
7. Click **Add**.

## 4. Automatic Re-Deploy
Railway will detect the changes (Variables added) and automatically trigger a new deployment.
- Go to the **"Deployments"** tab to watch the build log.
- It will install Python, Chrome, and Drivers automatically (thanks to `nixpacks.toml` I added).

## 5. Connect Frontend
1. Open your **Github Pages** or Local `index.html`.
2. Click the **"SERVER"** button in the top right.
3. Paste the Railway URL you copied in Step 3 (e.g., `https://ultimate-scraper-production.up.railway.app`).
4. Click OK.

**🎉 That's it! Your backend is now running in the cloud.**
You can close your laptop, and the server will stay online (as long as you have Railway credits/trial).
