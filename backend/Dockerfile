FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for PostgreSQL, Chromium and Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    chromium \
    chromium-driver \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy NLP model and NLTK sentiment lexicon
RUN python -m spacy download en_core_web_sm
RUN python -c "import nltk; nltk.download('vader_lexicon')"

# Copy backend codebase
COPY . /app/

# Make start script executable
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]