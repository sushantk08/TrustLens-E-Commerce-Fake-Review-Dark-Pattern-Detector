# TrustLens: E-Commerce & Local Business Review Anomaly & Dark Pattern Detector

TrustLens is an AI-powered intelligence platform that analyzes customer reviews and pricing behavior across **Amazon**, **Flipkart**, and **Google Maps** (restaurants, hospitals, automotive services). It exposes inorganic review velocity surges, AI-generated bot rings, deceptive pre-sale price hikes, and extracts feature-level sentiment to calculate an authentic **True Trust Score**.

---

## 🌐 Live Deployments

* **Web Dashboard:** [https://trustlens-tau-eight.vercel.app](https://trustlens-tau-eight.vercel.app)  
* **Backend API & WebSockets:** [https://trustlens-backend-tkda.onrender.com](https://trustlens-backend-tkda.onrender.com)

---

## 🚀 Key Features

1. **Asynchronous Scraping Engine (Selenium & Celery):**  
     
   * Headless Chrome driver configured with Chrome DevTools Protocol (CDP) anti-bot stealth mitigation.  
   * Multi-platform support: **Amazon India/US**, **Flipkart**, and **Google Maps**.  
   * Extracts customer reviews, star ratings, reviewer profiles, and historical pricing points.

   

2. **Real-Time Progress Streaming (Django Channels & WebSockets):**  
     
   * Uses Daphne (ASGI) and Redis Pub/Sub channel layers.  
   * Streams live scraping and analysis progress directly to the React frontend in real time.

   

3. **Review Velocity & Rating Anomaly Detection (Pandas & NumPy):**  
     
   * Detects abnormal time-series surges (sudden influxes of positive reviews over narrow date windows).  
   * Identifies polarized bimodal distributions (clusters of 5-star promotional reviews masking 1-star product defects).

   

4. **Semantic Duplicate Detection (Sentence-Transformers & PyTorch):**  
     
   * Uses dense vector embeddings (`all-MiniLM-L6-v2`) and cosine similarity.  
   * Flags paraphrased and AI-spun bot reviews that traditional keyword matching misses.

   

5. **Multi-Domain Aspect-Based Sentiment Analysis (spaCy & NLTK VADER):**  
     
   * Category-aware feature extraction:  
     * **E-Commerce:** Battery, Display, Camera, Performance, Build Quality, Sound, Delivery.  
     * **Restaurants & Cafes:** Food Quality & Taste, Ambience & Vibe, Service & Staff, Hygiene, Value for Money.  
     * **Healthcare & Hospitals:** Doctor Expertise, Nursing Care, Facilities & Cleanliness, Billing & Insurance, Wait Times.  
     * **Automotive:** Service Quality, Pricing Transparency, Delivery Timelines, Staff Handling.

   

6. **Dark Pattern & Fraud Alert Engine:**  
     
   * **E-Commerce:** Identifies artificial pre-sale price hikes and persistent fake scarcity warnings (*"Only 1 left in stock"*).  
   * **Google Maps:** Detects single-review account rings (bulk accounts with only 1 lifetime review) and flags the absence of verified Local Guides.

   

7. **Browser Extension (Manifest V3):**  
     
   * Seamless one-click inspection directly inside the browser while viewing an Amazon, Flipkart, or Google Maps listing.

---

## 🛠️ Tech Stack

* **Backend & API:** Python 3.12, Django 6, Django REST Framework, Daphne (ASGI)  
* **Real-Time & Tasks:** Django Channels, Celery, Redis (Pub/Sub)  
* **Data Science & ML:** Pandas, NumPy, Scikit-learn, Sentence-Transformers, PyTorch, spaCy, NLTK  
* **Scraping:** Selenium, BeautifulSoup4, WebDriver Manager  
* **Database:** PostgreSQL (Neon.tech / Managed Postgres)  
* **Frontend:** React (Vite), Tailwind CSS, Lucide Icons, Recharts  
* **Extension:** Chrome Extension Manifest V3  
* **Cloud Infrastructure:** Vercel (Frontend), Render (Containerized Backend \+ Celery), Upstash (Serverless Redis)

---

## 📂 Project Architecture

trustlens/

├── .gitignore

├── README.md

├── docker-compose.yml

│

├── backend/

│   ├── Dockerfile

│   ├── manage.py

│   ├── requirements.txt

│   ├── start.sh                       \# Production boot script for Daphne \+ Celery

│   ├── trustlens\_core/                \# Django project root (settings, asgi, urls, celery)

│   ├── products/                      \# Models, DRF serializers, views, Celery tasks

│   ├── scrapers/                      \# Selenium drivers for Amazon, Flipkart, Google Maps

│   ├── analysis/                      \# Velocity, semantic, credibility, and aspect engines

│   └── notifications/                 \# Channels consumers and WebSocket routing

│

├── frontend/                          \# React \+ Vite dashboard

│   ├── src/

│   │   ├── api/client.js              \# Dynamic API client

│   │   ├── components/                \# Modular UI widgets (Progress, Badges, Aspects)

│   │   ├── App.jsx

│   │   └── main.jsx

│   ├── tailwind.config.js

│   └── vite.config.js

│

└── extension/                         \# Chrome Extension (Manifest V3)

    ├── manifest.json

    ├── popup.html

    └── popup.js

---

## 💻 Local Development Setup

### 1\. Prerequisites

* Python 3.12+  
* Node.js 18+  
* PostgreSQL running on port `5432`  
* Redis running on port `6379`

### 2\. Backend Setup

cd backend

\# Create and activate virtual environment

python \-m venv venv

source venv/bin/activate       \# On Windows: venv\\Scripts\\activate

\# Install dependencies

pip install \-r requirements.txt

python \-m spacy download en\_core\_web\_sm

python \-c "import nltk; nltk.download('vader\_lexicon')"

\# Configure .env file

\# Create a .env file inside backend/ with your database credentials:

\# DB\_NAME=trustlens\_db

\# DB\_USER=postgres

\# DB\_PASSWORD=your\_password

\# DB\_HOST=localhost

\# DB\_PORT=5432

\# REDIS\_URL=redis://127.0.0.1:6379/0

\# Apply migrations

python manage.py migrate

\# Start development ASGI server

python manage.py runserver 8000

### 3\. Start Celery Worker (In a separate terminal)

cd backend

\# Activate virtual environment

celery \-A trustlens\_core worker \-l info \-P solo

### 4\. Frontend Setup (In a separate terminal)

cd frontend

npm install

npm run dev

Open `http://localhost:5173` in your browser.

### 5\. Install Chrome Extension

1. Open Google Chrome and navigate to `chrome://extensions`.  
2. Toggle on **Developer mode** in the top-right corner.  
3. Click **Load unpacked** and select the `trustlens/extension` directory.

---

## 🐳 Docker Deployment (Alternative)

To run the entire ecosystem (PostgreSQL, Redis, Daphne ASGI, Celery) in Docker:

docker-compose up \--build

---

## 📄 License

This project is open source and available under the [MIT License](http://LICENSE).  
