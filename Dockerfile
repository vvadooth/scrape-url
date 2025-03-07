FROM python:3.9

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl \
    libxss1 libappindicator1 libindicator7 \
    fonts-liberation libnss3 lsb-release xdg-utils \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set up ChromeDriver path
ENV CHROME_BIN="/usr/bin/chromium"
ENV CHROMEDRIVER_BIN="/usr/bin/chromedriver"

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application files
COPY . /app
WORKDIR /app

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
