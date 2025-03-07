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
logger = logging.getLogger("scraper_api")

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
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920x1080")

        # Set up ChromeDriver service
        service = Service(ChromeDriverManager().install())  
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

        driver.quit()

        extracted_content = ' '.join(body_text.split())[:200000]  # Limit to 200000 chars

        if extracted_content.strip():
            logger.info(f"✅ Successfully extracted {len(extracted_content)} characters.")
            return extracted_content
        else:
            logger.warning("⚠️ No text content found on page!")
            return "Warning: No text found on page"

    except Exception as e:
        logger.error(f"❌ WebDriver failed: {str(e)}")
        return "WebDriver initialization failed, but execution continued."

@app.post("/scrape")
def scrape_url(request: URLRequest):
    """API endpoint to scrape a URL."""
    if not request.url.startswith("http"):
        logger.warning("🚨 Invalid URL format")
        raise HTTPException(status_code=400, detail="Invalid URL format")

    extracted_text = scrape_page(request.url)

    logger.info(f"🔍 Extracted Content Length: {len(extracted_text)}")
    logger.debug(f"📝 Extracted Content Preview: {extracted_text[:500]}...")  

    return {
        "url": request.url,
        "content": extracted_text
    }
