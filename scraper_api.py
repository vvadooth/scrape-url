from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
import logging
import requests

# Initialize FastAPI
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class URLRequest(BaseModel):
    url: str

def scrape_page(url: str) -> str:
    """Uses Selenium to scrape the given URL and return text content."""
    try:
        logger.info(f"🌍 Fetching page content: {url}")

        # Check if ChromeDriver is installed
        chromedriver_path = "/usr/bin/chromedriver"  # Default Linux path
        if not os.path.exists(chromedriver_path):
            logger.warning("⚠️ ChromeDriver not found! Trying to install dependencies...")
            os.system("apt-get update && apt-get install -y chromium-browser chromium-chromedriver")

        # Set up Chrome (headless mode)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")  # Required for cloud deployments
        options.add_argument("--disable-dev-shm-usage")  # Prevent memory issues
        options.add_argument("--window-size=1920x1080")
        options.binary_location = "/usr/bin/chromium-browser"  # Manually set Chromium path

        # Set up ChromeDriver service
        try:
            service = Service(chromedriver_path)  # Use system-installed ChromeDriver
            driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.warning(f"⚠️ ChromeDriver initialization failed: {e}")
            return "WebDriver initialization failed."

        driver.get(url)

        # Wait for JavaScript to load
        time.sleep(10)

        # Scroll to bottom to load lazy-loaded content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Extract content from body text
        try:
            body = driver.find_element("tag name", "body")
            body_text = body.text.strip() if body else ""
        except Exception:
            body_text = ""

        driver.quit()

        if not body_text:
            logger.warning("⚠️ No text content found on page!")
            return "No text found on page."

        extracted_content = ' '.join(body_text.split())[:5000]  # Limit to 5000 chars

        logger.info(f"✅ Successfully extracted {len(extracted_content)} characters.")
        return extracted_content

    except Exception as e:
        logger.error(f"❌ Scraping failed: {str(e)}")
        logger.info("🌍 Trying fallback method (Basic HTTP request)...")

        # 🔄 Try basic HTTP request as fallback
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            return response.text[:5000] if response.ok else "Fallback method failed."
        except Exception as e:
            return f"Error: {str(e)}"

@app.post("/scrape")
def scrape_url(request: URLRequest):
    """API endpoint to scrape a URL."""
    if not request.url.startswith("http"):
        logger.warning("🚨 Invalid URL format")
        raise HTTPException(status_code=400, detail="Invalid URL format")

    extracted_text = scrape_page(request.url)

    logger.info(f"🔍 Extracted Content Length: {len(extracted_text)}")
    logger.debug(f"📝 Extracted Content Preview: {extracted_text[:500]}...")  # Only log first 500 chars

    if "error" in extracted_text.lower():
        logger.error(f"❌ Scraping failed for {request.url}")
        raise HTTPException(status_code=500, detail="Scraping failed.")

    return {
        "url": request.url,
        "content": extracted_text
    }
