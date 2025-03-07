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

# Copy the entrypoint script and ensure it's executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use the entrypoint script to start the FastAPI app
CMD ["/entrypoint.sh"]
