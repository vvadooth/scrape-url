from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

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

        # Set up Chrome (headless mode)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")  # Required for some cloud deployments
        options.add_argument("--disable-dev-shm-usage")  # Prevent memory issues
        options.add_argument("--window-size=1920x1080")

        # Set up ChromeDriver service
        service = Service(ChromeDriverManager().install())  # Auto-installs ChromeDriver
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)

        # Wait for JavaScript to load
        time.sleep(10)

        # Scroll to bottom to load lazy-loaded content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Extract content from body text
        body = driver.find_element("tag name", "body")
        body_text = body.text if body else ""

        if not body_text.strip():
            logger.error("❌ No text content found on page!")
            return "Error: No text found on page"

        extracted_content = ' '.join(body_text.split())[:200000]  # Limit to 5000 chars
        driver.quit()

        logger.info(f"✅ Successfully extracted {len(extracted_content)} characters.")
        return extracted_content

    except Exception as e:
        logger.error(f"❌ Scraping failed: {str(e)}")
        return f"Error: {str(e)}"

@app.post("/scrape")
def scrape_url(request: URLRequest):
    """API endpoint to scrape a URL."""
    if not request.url.startswith("http"):
        logger.warning("🚨 Invalid URL format")
        raise HTTPException(status_code=400, detail="Invalid URL format")

    extracted_text = scrape_page(request.url)

    # 🛠️ Log the extracted text for debugging
    logger.info(f"🔍 Extracted Content Length: {len(extracted_text)}")
    logger.debug(f"📝 Extracted Content Preview: {extracted_text[:500]}...")  # Only log first 500 chars

    # 🛠️ Remove the incorrect error check
    if not extracted_text.strip():
        logger.error(f"❌ No content extracted from {request.url}")
        raise HTTPException(status_code=500, detail="No content extracted")

    return {
        "url": request.url,
        "content": extracted_text
    }
