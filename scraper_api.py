from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import time
import logging
from youtube_transcript_api import YouTubeTranscriptApi
import os
import re
import requests

# Initialize FastAPI
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

class URLRequest(BaseModel):
    url: str

class YouTubeRequest(BaseModel):
    video_url: str

def expand_dropdowns_and_hidden_content(driver):
    """Attempts to find and click on elements that might expand hidden content."""
    try:
        # Common selectors for dropdowns, accordions, and show more buttons
        expandable_selectors = [
            # Dropdowns and accordions
            "button.dropdown-toggle", ".accordion-toggle", ".accordion-button", 
            "details summary", "[aria-expanded='false']", ".expander", ".toggleButton",
            # Show more buttons
            "button:contains('Show more')", "a:contains('Read more')", 
            ".show-more", ".read-more", ".view-more", 
            # Common class names
            ".collapsible", ".expandable", ".toggle"
        ]
        
        # Try to expand all potential elements
        expanded_count = 0
        for selector in expandable_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            driver.execute_script("arguments[0].click();", element)
                            expanded_count += 1
                            # Small delay to let content load
                            time.sleep(0.5)
                    except (ElementNotInteractableException, Exception) as e:
                        # Just skip elements that can't be interacted with
                        continue
            except Exception:
                # If a selector doesn't work, just move to the next one
                continue
                
        logger.info(f"✅ Expanded {expanded_count} interactive elements")
        
        # Try to also open iframes content if needed
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for i, iframe in enumerate(iframes):
                try:
                    driver.switch_to.frame(iframe)
                    # Extract content from the iframe
                    iframe_text = driver.find_element(By.TAG_NAME, "body").text
                    # Switch back to main content
                    driver.switch_to.default_content()
                except Exception:
                    driver.switch_to.default_content()
                    continue
        except Exception:
            # If iframe handling fails, continue with main content
            pass
            
    except Exception as e:
        logger.warning(f"⚠️ Error expanding dropdowns: {str(e)}")

def scrape_page(url: str) -> str:
    """Uses Selenium to scrape the given URL and return text content."""
    try:
        logger.info(f"🌍 Fetching page content: {url}")

        # Set up Chrome options
        options = Options()
        options.binary_location = "/usr/bin/chromium"  # Explicitly set Chromium path
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920x1080")

        # Set up ChromeDriver service
        service = Service("/usr/bin/chromedriver")  # Explicitly set ChromeDriver path
        driver = webdriver.Chrome(service=service, options=options)

        # Add a page load timeout
        driver.set_page_load_timeout(30)
        
        driver.get(url)

        # Wait for JavaScript to load (initial wait)
        time.sleep(5)

        # Scroll through the page multiple times to trigger lazy loading
        scroll_height = 300
        max_height = driver.execute_script("return document.body.scrollHeight")
        
        while scroll_height < max_height:
            driver.execute_script(f"window.scrollTo(0, {scroll_height});")
            time.sleep(0.5)  # Short delay while scrolling
            scroll_height += 300
            
        # Scroll to top before attempting to interact with elements
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Expand dropdowns and hidden content
        expand_dropdowns_and_hidden_content(driver)
        
        # Final scroll to bottom to ensure all content is loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Extract content from body text
        body = driver.find_element(By.TAG_NAME, "body")
        body_text = body.text if body else ""

        # Also try to get text from specific elements that might contain content
        additional_text = ""
        for tag in ["p", "div", "article", "section", "main"]:
            elements = driver.find_elements(By.TAG_NAME, tag)
            for el in elements:
                additional_text += " " + el.text
                
        # Combine all text and clean it up
        combined_text = body_text + " " + additional_text
        extracted_content = ' '.join(combined_text.split())[:200000]  

        driver.quit()

        if not extracted_content.strip():
            logger.error("❌ No text content found on page!")
            return "Error: No text found on page"

        logger.info(f"✅ Successfully extracted {len(extracted_content)} characters.")
        return extracted_content

    except Exception as e:
        logger.error(f"❌ Scraping failed: {str(e)}")
        try:
            driver.quit()
        except:
            pass
        return f"Error: {str(e)}"

@app.post("/scrape")
def scrape_url(request: URLRequest):
    """API endpoint to scrape a URL."""
    if not request.url.startswith("http"):
        logger.warning("🚨 Invalid URL format")
        raise HTTPException(status_code=400, detail="Invalid URL format")

    extracted_text = scrape_page(request.url)

    if extracted_text.startswith("Error:"):
        logger.error(f"❌ Error scraping {request.url}: {extracted_text}")
        raise HTTPException(status_code=500, detail=extracted_text)

    if not extracted_text.strip():
        logger.error(f"❌ No content extracted from {request.url}")
        raise HTTPException(status_code=500, detail="No content extracted")

    return {
        "url": request.url,
        "content": extracted_text
    }


def extract_video_id(url: str) -> str:
    """Extracts YouTube video ID from a given URL."""
    regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

def get_video_title(video_id: str) -> str:
    """Fetch video title from YouTube API"""
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}"
    response = requests.get(url).json()
    
    if "items" in response and response["items"]:
        return response["items"][0]["snippet"]["title"]
    return "Unknown Title"

@app.post("/get-transcript")
def get_youtube_transcript(request: YouTubeRequest):
    """API endpoint to fetch a YouTube video's transcript and title."""
    video_id = extract_video_id(request.video_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        title = get_video_title(video_id)
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join(entry["text"] for entry in transcript)

        return {
            "url": request.video_url,
            "title": title,
            "transcript": transcript_text
        }
    except Exception as e:
        logger.error(f"❌ Failed to get transcript: {str(e)}")
        raise HTTPException(status_code=500, detail="Transcript not available")
