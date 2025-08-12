# TrustLens — E-Commerce Fake Review & Dark Pattern Detector

TrustLens is an end-to-end e-commerce trust and transparency platform that analyzes product listings and customer-review signals to help users identify potentially **fake reviews, suspicious rating activity, and deceptive pricing patterns**.

The project combines **Django, Django Channels/ASGI, Celery, Redis, PostgreSQL, React, Selenium, spaCy, and sentence-transformers** to create a full-stack detection system with background processing and browser-based analysis.

> **Project Status:** Local development / portfolio project

---

## 🚀 What TrustLens Does

TrustLens focuses on three major trust signals:

### 1. Fake Review Detection
Analyzes review content and behavior to identify suspicious patterns such as:

- Highly similar or duplicated reviews
- Repetitive wording across multiple reviews
- Unusual review bursts
- Suspicious reviewer behavior
- Language patterns that may indicate coordinated reviews

Natural-language processing is performed using tools such as **spaCy** and **sentence-transformers**.

### 2. Rating Velocity Analysis

TrustLens looks at how ratings change over time rather than relying only on the current average rating.

For example:

```text
Normal pattern
100 reviews → gradual rating growth

Suspicious pattern
100 reviews → 180 reviews in a very short period
```

Sudden review or rating spikes can become an additional signal for investigation.

### 3. Dark Pattern / Deceptive Pricing Detection

TrustLens analyzes product-price information to identify potentially misleading pricing techniques, such as:

- Large displayed discounts
- Artificially inflated "original" prices
- Unusual price changes
- Urgency-style pricing signals
- Other suspicious pricing patterns

The goal is not to automatically declare a seller fraudulent, but to surface **risk indicators that deserve closer attention**.

---

# 🏗️ System Architecture

TrustLens uses a full-stack architecture:

```text
                         ┌─────────────────────┐
                         │   React Frontend    │
                         │  Web Dashboard/UI   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Django Backend    │
                         │    REST / Logic     │
                         └───────┬─────┬───────┘
                                 │     │
                    ┌────────────┘     └─────────────┐
                    ▼                                ▼
          ┌─────────────────┐              ┌─────────────────┐
          │   PostgreSQL    │              │      Redis      │
          │  Persistent DB   │              │ Broker / Cache  │
          └─────────────────┘              └────────┬────────┘
                                                     │
                                                     ▼
                                           ┌─────────────────┐
                                           │ Celery Workers  │
                                           │ Background Jobs │
                                           └────────┬────────┘
                                                    │
                         ┌──────────────────────────┼────────────────────┐
                         ▼                          ▼                    ▼
                  ┌─────────────┐          ┌───────────────┐     ┌─────────────┐
                  │  Selenium   │          │ NLP Analysis  │     │   Pricing   │
                  │ Web Scraper │          │ spaCy / ST    │     │   Signals   │
                  └─────────────┘          └───────────────┘     └─────────────┘

                         Chrome Extension
                                │
                                ▼
                       Product Page Signals
```

---

# 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Backend | Django |
| ASGI Server | Daphne |
| Background Jobs | Celery |
| Message Broker / Cache | Redis |
| Database | PostgreSQL |
| Frontend | React |
| Web Scraping | Selenium |
| NLP | spaCy |
| Semantic Similarity | sentence-transformers |
| Browser Integration | Chrome Extension |
| Containerization | Docker / Docker Compose |
| Language | Python / JavaScript |

---

# 📁 Project Structure

A typical TrustLens repository is organized approximately as follows:

```text
trustlens/
│
├── backend/
│   ├── manage.py
│   ├── trustlens_core/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── ...
│   │
│   ├── apps/
│   │   ├── ...
│   │   └── ...
│   │
│   └── venv/
│
├── frontend/
│   ├── package.json
│   ├── src/
│   └── ...
│
├── extension/
│   ├── manifest.json
│   ├── ...
│   └── ...
│
├── docker-compose.yml
├── README.md
└── ...
```

> The exact application/module names may differ depending on the current repository structure.

---

# ⚙️ Prerequisites

Before running TrustLens locally, install:

- Python 3.10+
- Node.js and npm
- PostgreSQL
- Redis
- Google Chrome
- ChromeDriver compatible with your Chrome/Selenium setup
- Git

For the Docker setup:

- Docker
- Docker Compose

---

# 🔧 Local Development Setup

## 1. Clone the Repository

```bash
git clone <https://github.com/sushantk08/TrustLens-E-Commerce-Fake-Review-Dark-Pattern-Detector.git>
cd trustlens
```

---

## 2. Start Supporting Services

TrustLens requires:

```text
PostgreSQL → port 5432
Redis      → port 6379
```

Make sure both services are running before starting Django and Celery.

Example PostgreSQL connection:

```text
Host: localhost
Port: 5432
```

Example Redis connection:

```text
redis://localhost:6379/0
```

---

# 🐍 3. Set Up the Django Backend

Move into the backend directory:

```bash
cd backend
```

Create a virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file inside the backend directory.

Example:

```env
DEBUG=True

DATABASE_NAME=trustlens
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

REDIS_URL=redis://localhost:6379/0
```

> Never commit passwords, secret keys, API keys, or other credentials to GitHub.

---

# 🗄️ 5. Run Database Migrations

From the `backend` directory:

```bash
python manage.py migrate
```

Create an administrator account when needed:

```bash
python manage.py createsuperuser
```

---

# 🌐 6. Start Django with Daphne

Start the ASGI server:

```bash
daphne -p 8000 trustlens_core.asgi:application
```

The backend will be available at:

```text
http://localhost:8000
```

---

# 🔄 7. Start the Celery Worker

Open a **new terminal**.

Activate the same virtual environment and move to the backend directory:

### Windows

```bash
cd backend
venv\Scripts\activate
```

### Linux / macOS

```bash
cd backend
source venv/bin/activate
```

Start Celery:

```bash
celery -A trustlens_core worker -l info
```

Celery handles long-running or resource-intensive work in the background instead of blocking the web application.

Typical background tasks may include:

```text
Product scraping
       ↓
Review extraction
       ↓
Text processing
       ↓
Semantic similarity analysis
       ↓
Risk calculation
       ↓
Store results
```

---

# ⚛️ 8. Start the React Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

Open that URL in your browser.

---

# 🌐 9. Install the Chrome Extension

TrustLens can also integrate with a Chrome extension for browser-based product analysis.

### Installation

1. Open Google Chrome.
2. Navigate to:

```text
chrome://extensions
```

3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select:

```text
trustlens/extension
```

6. The TrustLens extension should now appear in your installed extensions.

---

# 🐳 Docker Setup

Docker Compose provides an alternative way to run the supporting TrustLens services together.

Start the stack with:

```bash
docker-compose up --build
```

To run it in the background:

```bash
docker-compose up --build -d
```

To stop the services:

```bash
docker-compose down
```

To rebuild containers after dependency or configuration changes:

```bash
docker-compose up --build
```

A typical Docker deployment contains services such as:

```text
┌────────────────────────────────────┐
│          Docker Compose            │
│                                    │
│  ┌─────────────┐ ┌─────────────┐  │
│  │   Django    │ │    Celery   │  │
│  │   /Daphne   │ │    Worker   │  │
│  └──────┬──────┘ └──────┬──────┘  │
│         │               │          │
│  ┌──────▼──────┐ ┌──────▼──────┐  │
│  │ PostgreSQL  │ │    Redis    │  │
│  └─────────────┘ └─────────────┘  │
└────────────────────────────────────┘
```

---

# 🧠 Detection Pipeline

The core TrustLens workflow can be represented as:

```text
Product URL
    │
    ▼
Selenium Scraper
    │
    ├── Product information
    ├── Price
    ├── Ratings
    └── Reviews
          │
          ▼
     Data Cleaning
          │
          ▼
    ┌──────────────────────────────┐
    │       Analysis Engine       │
    │                              │
    │ Fake Review Signals         │
    │ Rating Velocity              │
    │ Review Similarity            │
    │ Pricing / Dark Patterns      │
    └──────────────┬───────────────┘
                   │
                   ▼
             Risk Scoring
                   │
                   ▼
          PostgreSQL Storage
                   │
                   ▼
             React Dashboard
```

---

# 🤖 NLP & Machine Learning

TrustLens uses multiple NLP techniques rather than relying on a single keyword-based rule.

### spaCy

spaCy can be used for:

- Text preprocessing
- Tokenization
- Linguistic analysis
- Named entities
- Normalization
- Feature extraction

### sentence-transformers

Sentence-transformers are used to generate semantic embeddings.

For example:

```text
Review A:
"Excellent product, highly recommended."

Review B:
"Great product, definitely recommend it."
```

Although the wording is different, their semantic meaning may be very similar.

The system can compare their vector representations to identify potentially repetitive review patterns.

Conceptually:

```text
Review Text
    ↓
Sentence Transformer
    ↓
Embedding Vector
    ↓
Similarity Calculation
    ↓
Suspicion Signal
```

---

# 🕷️ Web Scraping

Selenium provides browser automation for collecting publicly visible product information.

Typical workflow:

```text
Open product page
      ↓
Wait for dynamic content
      ↓
Extract product information
      ↓
Extract ratings/reviews
      ↓
Normalize data
      ↓
Send analysis job
```

Because e-commerce sites can change their HTML structure, selectors should be maintained carefully and scraping should respect each site's terms and applicable policies.

---

# 📊 Example Risk Signals

TrustLens can combine multiple indicators into an overall risk assessment.

Example:

```text
Review Similarity        → High
Review Burst             → High
Rating Velocity          → Medium
Price Discount Pattern   → High
──────────────────────────────────
Overall Trust Risk       → High
```

The final result should be interpreted as a **risk indicator**, not definitive proof that a review or seller is fraudulent.

---

# 🔐 Security & Privacy Notes

For a production deployment, the following should be implemented:

- Keep secrets in environment variables
- Never commit `.env` files
- Validate user input
- Add authentication and authorization where required
- Apply API rate limiting
- Restrict scraping frequency
- Sanitize external data
- Use HTTPS in production
- Use secure PostgreSQL credentials
- Configure Django `ALLOWED_HOSTS`
- Disable `DEBUG` in production
- Rotate sensitive credentials if accidentally exposed

Example `.gitignore` entries:

```gitignore
.env
venv/
__pycache__/
*.pyc
node_modules/
```

---

# 🧪 Testing

Recommended backend testing:

```bash
cd backend
python manage.py test
```

Frontend tests depend on the configured React testing framework.

For production-quality development, add tests for:

```text
Scraping logic
NLP preprocessing
Similarity calculations
Risk scoring
API endpoints
Celery tasks
Database models
Frontend components
Chrome extension behavior
```

---

# 🛠️ Troubleshooting

## PostgreSQL connection error

Verify PostgreSQL is running and confirm:

```text
Host     = localhost
Port     = 5432
Database = trustlens
```

Also verify the username and password in `.env`.

---

## Redis connection error

Confirm Redis is running:

```text
redis://localhost:6379/0
```

---

## Daphne command not found

Make sure the virtual environment is activated and install Daphne:

```bash
pip install daphne
```

---

## Celery cannot connect to Redis

Check:

```text
Redis running?
REDIS_URL correct?
Port 6379 available?
```

---

## Selenium / ChromeDriver problems

Make sure the installed ChromeDriver version is compatible with your Chrome browser, or configure Selenium to use an appropriate driver-management approach.

---

## React dependency problems

Try:

```bash
cd frontend
npm install
npm run dev
```

If dependencies are corrupted:

```bash
rm -rf node_modules
npm install
```

On Windows PowerShell, you can remove the directory with:

```powershell
Remove-Item -Recurse -Force node_modules
npm install
```

---

# 📌 Development Commands

### Backend

```bash
cd backend
venv\Scripts\activate
python manage.py migrate
daphne -p 8000 trustlens_core.asgi:application
```

### Celery

```bash
cd backend
venv\Scripts\activate
celery -A trustlens_core worker -l info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up --build
```

---

# 🎯 Why This Project Is Useful

TrustLens demonstrates several skills that are useful in real-world Python/backend engineering:

- Full-stack application development
- Django backend development
- ASGI deployment with Daphne
- Asynchronous background processing with Celery
- Redis message brokering
- PostgreSQL database integration
- Web automation with Selenium
- Natural-language processing
- Semantic text similarity
- React frontend development
- Chrome extension integration
- Docker-based deployment
- Data analysis and risk scoring

The project is designed to show how multiple technologies can work together to solve a practical problem instead of demonstrating each technology in isolation.

---

# 📈 Future Improvements

Potential future improvements include:

- Historical price tracking
- Review-author behavior analysis
- Graph-based review-ring detection
- More advanced anomaly detection
- Product comparison across marketplaces
- Explainable AI scoring
- Review timeline visualization
- Browser-side real-time warnings
- Authentication and user accounts
- Cloud deployment on AWS
- Monitoring and observability
- Automated model evaluation
- Scheduled data collection
- Better marketplace-specific scraping adapters

---

# ⚠️ Disclaimer

TrustLens is an analytical and educational project.

A high-risk score does **not** automatically mean that a seller, product, or review is fraudulent. Detection results are based on statistical, behavioral, linguistic, and pricing signals and should be treated as indicators for further investigation.

Scraping and automated access to websites must comply with the applicable website terms, robots policies, laws, and service restrictions.

---

# 📄 License

Add your preferred open-source license here, for example:

```text
MIT License
```

---

# 👨‍💻 Author

**Sushant Kulkarni**

Built as a portfolio project demonstrating Python backend development, automation, NLP, machine learning, asynchronous processing, and full-stack engineering.
