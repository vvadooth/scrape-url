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

# Start FastAPI server using the correct port from Railway
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
