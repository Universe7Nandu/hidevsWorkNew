
import requests
from bs4 import BeautifulSoup
import csv
import time
import logging
import os
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://lu.ma/START_by_BHIVE"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
OUTPUT_FILE = "luma_events_data.csv"
REQUEST_DELAY = 2  # Seconds between requests
MAX_RETRIES = 3

def get_page_content(url: str, retry_count: int = 0) -> Optional[str]:
    try:
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        time.sleep(REQUEST_DELAY)
        if response.status_code == 200:
            return response.text
        else:
            logger.warning(f"Failed to fetch {url}, status code: {response.status_code}")
            if retry_count < MAX_RETRIES:
                logger.info(f"Retrying... (Attempt {retry_count + 1}/{MAX_RETRIES})")
                time.sleep(REQUEST_DELAY * 2)
                return get_page_content(url, retry_count + 1)
            return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        if retry_count < MAX_RETRIES:
            logger.info(f"Retrying... (Attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(REQUEST_DELAY * 2)
            return get_page_content(url, retry_count + 1)
        return None

def get_event_links(html_content: str) -> List[str]:
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        event_links = []
        for a_tag in soup.select("a.event-link.content-link[href]"):
            href = a_tag["href"]
            full_url = urljoin("https://lu.ma", href)
            event_links.append(full_url)
        logger.info(f"Extracted {len(event_links)} event links")
        return list(set(event_links))
    except Exception as e:
        logger.error(f"Error extracting event links: {str(e)}")
        return []

def get_host_info(event_url: str) -> Dict[str, str]:
    try:
        html_content = get_page_content(event_url)
        if not html_content:
            return {"Event Name": "Error", "Host Name": "Error", "LinkedIn URL": "Error"}

        soup = BeautifulSoup(html_content, 'html.parser')

        # Get Event Title
        event_name = soup.find("h1")
        event_name = event_name.text.strip() if event_name else "N/A"

        # Find host block
        host_anchors = soup.select("div.content-card a[href^='/user/']")
        if not host_anchors:
            logger.warning(f"No hosts found on {event_url}")
            return {"Event Name": event_name, "Host Name": "N/A", "LinkedIn URL": "N/A"}

        host_anchor = host_anchors[0]
        host_name = host_anchor.text.strip()
        host_relative_url = host_anchor['href']
        host_url = urljoin("https://lu.ma", host_relative_url)

        # Get LinkedIn from host page
        linkedin_url = "N/A"
        host_page = get_page_content(host_url)
        if host_page:
            host_soup = BeautifulSoup(host_page, 'html.parser')
            linkedin_anchor = host_soup.find('a', href=lambda href: href and 'linkedin.com' in href.lower())
            if linkedin_anchor:
                linkedin_url = linkedin_anchor['href']

        return {
            "Event Name": event_name,
            "Host Name": host_name,
            "LinkedIn URL": linkedin_url
        }

    except Exception as e:
        logger.error(f"Error getting host info for {event_url}: {str(e)}")
        return {"Event Name": f"Error: {str(e)}", "Host Name": "Error", "LinkedIn URL": "Error"}

def scrape_all_events() -> List[Dict[str, str]]:
    all_data = []
    html_content = get_page_content(BASE_URL)
    if not html_content:
        logger.error(f"Could not fetch the main page: {BASE_URL}")
        return all_data
    event_links = get_event_links(html_content)
    if not event_links:
        logger.error("No event links found")
        return all_data
    for event_url in event_links:
        try:
            logger.info(f"Processing event: {event_url}")
            info = get_host_info(event_url)
            info["Event URL"] = event_url
            all_data.append(info)
        except Exception as e:
            logger.error(f"Error processing event {event_url}: {str(e)}")
        time.sleep(REQUEST_DELAY)
    return all_data

def export_to_csv(data: List[Dict[str, str]], filename: str = OUTPUT_FILE) -> None:
    if not data:
        logger.warning("No data to export")
        return
    keys = ["Event Name", "Event URL", "Host Name", "LinkedIn URL"]
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"✅ Exported {len(data)} records to {filename}")
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")

def main():
    logger.info("Starting Lu.ma event scraper")
    data = scrape_all_events()
    export_to_csv(data)
    logger.info("Scraping completed")

if __name__ == "__main__":
    main()
