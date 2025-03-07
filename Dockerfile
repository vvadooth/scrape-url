FROM python:3.9

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl \
    libxss1 libappindicator3-1 \
    fonts-liberation libnss3 lsb-release xdg-utils \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set up environment variables for Chrome & ChromeDriver
ENV CHROME_BIN="/usr/bin/chromium"
ENV CHROMEDRIVER_BIN="/usr/bin/chromedriver"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app
WORKDIR /app

# Hardcode the port to 8080
CMD uvicorn main:app --host 0.0.0.0 --port 8080