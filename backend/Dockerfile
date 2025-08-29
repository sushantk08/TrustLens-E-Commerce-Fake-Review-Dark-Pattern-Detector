FROM python:3.12-slim

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

# Install CPU-only PyTorch wheel and ASGI server (Uvicorn)
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir "uvicorn[standard]"
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Download NLP model and lexicon
RUN python -m spacy download en_core_web_sm
RUN python -c "import nltk; nltk.download('vader_lexicon')"

COPY . /app/

# Convert Windows CRLF to Unix LF and ensure executable
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

EXPOSE 10000

CMD ["/app/start.sh"]