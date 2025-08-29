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
* **Cloud Infrastructure:** Vercel (Frontend), Render (Containerized Backend + Celery), Upstash (Serverless Redis)

---

## 📂 Project Architecture

```text
trustlens/
│
├── README.md
├── .gitignore
├── docker-compose.yml                 # Local multi-service orchestration
│
├── backend/                           # Django API, scraping & AI pipeline
│   ├── Dockerfile                     # Production container image
│   ├── manage.py
│   ├── requirements.txt
│   ├── start.sh                       # Production startup script
│   │
│   ├── trustlens_core/                # Django project configuration
│   │   ├── settings.py                # Environment, database & app config
│   │   ├── urls.py                    # API routing
│   │   ├── asgi.py                    # Daphne / WebSocket entry point
│   │   ├── wsgi.py                    # WSGI entry point
│   │   └── celery.py                  # Celery application configuration
│   │
│   ├── products/                      # Product / business analysis domain
│   │   ├── models.py                  # Database models
│   │   ├── serializers.py             # DRF serializers
│   │   ├── views.py                   # API endpoints
│   │   ├── urls.py                    # App-level API routes
│   │   └── tasks.py                   # Background scraping & analysis tasks
│   │
│   ├── scrapers/                      # Platform-specific data collection
│   │   ├── amazon.py                   # Amazon scraper
│   │   ├── flipkart.py                 # Flipkart scraper
│   │   ├── google_maps.py              # Google Maps scraper
│   │   └── base.py                     # Shared scraper utilities
│   │
│   ├── analysis/                      # AI / ML intelligence layer
│   │   ├── velocity.py                # Review velocity anomalies
│   │   ├── similarity.py              # Semantic duplicate detection
│   │   ├── sentiment.py               # Sentiment & aspect analysis
│   │   ├── credibility.py             # Reviewer credibility signals
│   │   ├── dark_patterns.py           # Pricing & scarcity detection
│   │   └── trust_score.py              # True Trust Score calculation
│   │
│   ├── notifications/                 # Real-time communication
│   │   ├── consumers.py               # WebSocket consumers
│   │   ├── routing.py                 # WebSocket routes
│   │   └── services.py                # Progress/event publishing
│   │
│   └── tests/                         # Backend & analysis tests
│
├── frontend/                          # React dashboard
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── api/
│       │   └── client.js              # REST / WebSocket API client
│       ├── components/                # Reusable dashboard components
│       ├── pages/                     # Dashboard views
│       ├── hooks/                     # Reusable React hooks
│       ├── utils/                     # Frontend helpers
│       ├── App.jsx                    # Application root
│       └── main.jsx                   # React entry point
│
└── extension/                        # Chrome Extension - Manifest V3
    ├── manifest.json                  # Extension configuration
    ├── popup.html                     # Extension popup UI
    ├── popup.js                       # Popup logic & API integration
    ├── content.js                    # Listing-page integration
    └── styles.css                    # Extension styles
```

### Data Flow

```text
Amazon / Flipkart / Google Maps
              │
              ▼
       Selenium Scrapers
              │
              ▼
       Celery Task Queue
              │
              ▼
      Data Cleaning & Parsing
              │
              ▼
       ┌──────┴────────┐
       │               │
       ▼               ▼
  ML / NLP Engine   Dark Pattern Engine
       │               │
       └──────┬────────┘
              ▼
       True Trust Score
              │
       ┌──────┴─────────┐
       ▼                ▼
 PostgreSQL         Redis / Channels
                         │
                         ▼
                 Django + WebSockets
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       React Dashboard       Chrome Extension
```

---

## 💻 Local Development Setup

### 1. Prerequisites

Make sure the following are installed and available in your `PATH`:

* **Python 3.12+**
* **Node.js 18+** and **npm**
* **Google Chrome** (required by Selenium)
* **PostgreSQL** running on port `5432`
* **Redis** running on port `6379`
* **Git**

You can verify the main tools with:

```bash
python --version
node --version
npm --version
psql --version
redis-server --version
git --version
```

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd trustlens
```

### 3. Configure PostgreSQL

Create a PostgreSQL database for local development:

```sql
CREATE DATABASE trustlens_db;
```

Make sure PostgreSQL is running before starting Django.

### 4. Start Redis

Redis is used by Celery for background jobs and Django Channels for real-time updates.

Start Redis using your local Redis installation. The default development URL is:

```text
redis://127.0.0.1:6379/0
```

### 5. Backend Setup

Open a terminal in the project root and create the Python virtual environment:

**Windows (PowerShell):**

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Git Bash):**

```bash
cd backend
python -m venv venv
source venv/Scripts/activate
```

**macOS / Linux:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

Install the backend dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Install the NLP resources used by the analysis pipeline:

```bash
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('vader_lexicon')"
```

### 6. Configure Environment Variables

Create a file named `backend/.env`:

```env
DB_NAME=trustlens_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
REDIS_URL=redis://127.0.0.1:6379/0
```

Use the PostgreSQL username and password configured on your machine. Never commit `.env` to Git.

### 7. Initialize the Django Backend

From the `backend` directory, run:

```bash
python manage.py check
python manage.py migrate
```

If your project contains custom database data or admin users, create them as needed:

```bash
python manage.py createsuperuser
```

### 8. Start the Django ASGI Server

For local development, start Django with:

```bash
python manage.py runserver 8000
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

### 9. Start the Celery Worker

Open a **second terminal**, activate the same virtual environment, and run:

```bash
cd backend
```

**Windows:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Git Bash:**

```bash
source venv/Scripts/activate
```

Start the Celery worker:

```bash
celery -A trustlens_core worker -l info -P solo
```

Keep this terminal running. Scraping and analysis jobs are executed by Celery.

### 10. Start the Frontend

Open a **third terminal** from the project root:

```bash
cd frontend
npm install
npm run dev
```

The React dashboard will normally be available at:

```text
http://localhost:5173
```

The frontend should be configured to use the local backend API and WebSocket endpoint during development.

### 11. Chrome / Selenium Setup

TrustLens uses Selenium with Google Chrome for Amazon, Flipkart, and Google Maps scraping.

Before running a scraper, make sure:

* Google Chrome is installed.
* Your installed Chrome version is compatible with the Selenium driver setup used by the project.
* The scraper can launch Chrome successfully from the backend virtual environment.

A simple Selenium check can be performed with the project's scraper/test scripts.

### 12. Install the Chrome Extension

1. Open Chrome and go to `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select the `trustlens/extension` directory.
5. Pin the TrustLens extension to the Chrome toolbar for easier access.

The extension communicates with the configured TrustLens backend and can be used to inspect supported Amazon, Flipkart, and Google Maps pages.

### 13. Recommended Local Startup Order

Start the services in this order:

```text
PostgreSQL
   ↓
Redis
   ↓
Django backend
   ↓
Celery worker
   ↓
React frontend
   ↓
Chrome extension
```

A normal development session therefore uses three terminals:

**Terminal 1 — Backend**

```bash
cd backend
# activate venv first
python manage.py runserver 8000
```

**Terminal 2 — Celery**

```bash
cd backend
# activate venv first
celery -A trustlens_core worker -l info -P solo
```

**Terminal 3 — Frontend**

```bash
cd frontend
npm run dev
```

### 14. Verify the Local Setup

Before testing a full scrape, verify that:

```text
Frontend      → http://localhost:5173
Backend       → http://127.0.0.1:8000
PostgreSQL    → localhost:5432
Redis         → localhost:6379
Celery        → worker shows as ready
Chrome/Selenium → browser launches successfully
```

Then open the dashboard and run a supported analysis workflow. Monitor the Django and Celery terminals for scraping, task, and WebSocket errors.

### 15. Common Development Commands

```bash
# Backend checks
python manage.py check
python manage.py showmigrations

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run backend tests
python manage.py test

# Start Django
python manage.py runserver 8000

# Start Celery
celery -A trustlens_core worker -l info -P solo

# Frontend
npm install
npm run dev
```

---

## 🐳 Docker Deployment (Alternative)

To run the entire ecosystem (PostgreSQL, Redis, Daphne ASGI, Celery) in Docker:

```bash
docker-compose up --build
```

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
