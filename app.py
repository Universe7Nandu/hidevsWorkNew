import pandas as pd
import streamlit as st
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Set page configuration
st.set_page_config(
    page_title="BHIVE Events Scraper",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS for better UI
st.markdown("""
<style>
    /* Overall Page Styling */
    .main {
        padding: 2rem;
        background-color: #1a202c;
        color: white;
    }
    .stApp {
        background-color: #1a202c;
    }
    
    /* Typography */
    h1 {
        color: #ffffff;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        text-align: center;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #4299e1;
    }
    
    h2, h3 {
        color: #ffffff;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-weight: 600;
    }
    
    p {
        font-family: 'Segoe UI', Arial, sans-serif;
        line-height: 1.6;
        color: #e2e8f0;
    }
    
    /* Components */
    .stButton>button {
        background-color: #4299e1;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #3182ce;
        box-shadow: 0 0 15px rgba(66, 153, 225, 0.5);
    }
    
    /* Status messages */
    .stAlert {
        background-color: #2d3748;
        color: white;
        border: none;
        border-left: 4px solid;
    }
    
    .stAlert.success {
        border-left-color: #48bb78;
    }
    
    .stAlert.warning {
        border-left-color: #ed8936;
    }
    
    .stAlert.error {
        border-left-color: #f56565;
    }
    
    /* Input fields */
    .stTextInput>div>div>input {
        background-color: #2d3748;
        color: white;
        border: 1px solid #4a5568;
        border-radius: 0.375rem;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #4299e1;
        box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.3);
    }
    
    /* DataFrame */
    [data-testid="stDataFrame"] table {
        width: 100%;
    }
    
    [data-testid="stDataFrame"] th {
        background-color: #2d3748 !important;
        color: white !important;
        font-weight: 600 !important;
        text-align: left !important;
        padding: 0.75rem 1rem !important;
        border-bottom: 2px solid #4299e1 !important;
    }
    
    [data-testid="stDataFrame"] td {
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid #4a5568 !important;
        color: #e2e8f0 !important;
    }
    
    [data-testid="stDataFrame"] tr:nth-child(even) {
        background-color: #2d3748 !important;
    }
    
    [data-testid="stDataFrame"] tr:nth-child(odd) {
        background-color: #1a202c !important;
    }
    
    /* Container for sections */
    .container {
        background-color: #2d3748;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #4299e1;
    }
    
    /* Download button */
    .download-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: #4299e1;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
        text-decoration: none;
        transition: all 0.3s ease;
        margin-top: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .download-btn:hover {
        background-color: #3182ce;
        transform: translateY(-2px);
        box-shadow: 0 6px 10px rgba(0, 0, 0, 0.2);
    }
    
    /* Progress indicators */
    .stProgress > div > div > div > div {
        background-color: #4299e1;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1rem;
        margin-top: 2rem;
        color: #a0aec0;
        font-size: 0.875rem;
        border-top: 1px solid #2d3748;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #2d3748;
        margin: 1.5rem 0;
    }
    
    /* Info box */
    .info-box {
        background-color: #2d3748;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #4299e1;
    }
</style>
""", unsafe_allow_html=True)

# Function to scrape BHIVE events data
@st.cache_data(show_spinner=False, ttl=1800)
def scrape_bhive_events(url="https://lu.ma/START_by_BHIVE"):
    logger.info(f"Starting scrape of {url}")
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    try:
        # Use webdriver_manager to handle Chrome driver installation
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        st.success("Chrome driver initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize Chrome driver: {e}")
        st.error(f"Failed to initialize Chrome driver: {str(e)}")
        return pd.DataFrame()
    
    events_data = []
    
    try:
        # Load main page
        logger.info(f"Loading main page: {url}")
        st.info(f"Loading events from {url}")
        
        # Add a retry mechanism for loading the initial page
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get(url)
                # Wait for page to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
                st.success("Page loaded successfully!")
                break
            except (TimeoutException, WebDriverException) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Retry {attempt+1}/{max_retries} for loading {url}: {e}")
                    st.warning(f"Retry {attempt+1}/{max_retries} for loading page...")
                    time.sleep(3)
                else:
                    logger.error(f"Failed to load {url} after {max_retries} retries: {e}")
                    st.error(f"Failed to load page after {max_retries} retries.")
                    return pd.DataFrame()
        
        # Parse the main page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all event links - try multiple selector patterns
        event_links = soup.select("a[href*='/event/']")
        if not event_links:
            # Try alternative selectors
            event_links = soup.select("a[href*='lu.ma/e/']")
        
        logger.info(f"Found {len(event_links)} event links")
        
        if not event_links:
            # Take a screenshot to debug
            driver.save_screenshot("page_source.png")
            logger.warning("No event links found on the page. Page source saved for debugging.")
            
            # Dump HTML for debugging
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            
            st.warning("No event links found. This could be due to changes in the page structure or the page might be protected.")
            st.info("Consider manually checking the URL to ensure events are available.")
            return pd.DataFrame()
            
        # Process each event
        total_events = len(event_links)
        st.info(f"Found {total_events} events to process")
        
        for index, link in enumerate(event_links, 1):
            event_url = urljoin("https://lu.ma", link['href'])
            st.progress(index/total_events, text=f"Processing event {index}/{total_events}")
            logger.info(f"Processing event {index}/{total_events}: {event_url}")
            
            try:
                # Get event title from the link
                event_title_elem = link.select_one('h3, div[class*="title"], span[class*="name"], [class*="event"]')
                event_title = event_title_elem.get_text(strip=True) if event_title_elem else "Unknown Event"
                
                # Load event page
                driver.get(event_url)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
                
                # Parse event page
                event_soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Try to get event title from event page if not found on listing
                if event_title == "Unknown Event":
                    event_title_elem = event_soup.select_one('h1, div[class*="title"], [class*="event-title"]')
                    if event_title_elem:
                        event_title = event_title_elem.get_text(strip=True)
                
                # Find host section - try multiple approaches
                host_section = event_soup.select_one('div[class*="creator"], div[class*="host"], section:contains("Hosted by")')
                
                if not host_section:
                    # Try alternative methods to find host links
                    host_links = event_soup.select('a[href*="/u/"], a[href*="/p/"]')
                else:
                    # Get host links from host section
                    host_links = host_section.select('a[href*="/u/"], a[href*="/p/"]')
                
                if not host_links:
                    # If no host found, add event with empty host
                    logger.warning(f"No hosts found for event: {event_title}")
                    events_data.append({
                        "Event Name": event_title,
                        "Host Name": "Unknown",
                        "LinkedIn Profile URL": ""
                    })
                    continue
                
                # Process each host
                for host_link in host_links:
                    host_url = urljoin("https://lu.ma", host_link['href'])
                    
                    try:
                        # Get host name from link
                        host_name_elem = host_link.select_one('span, div')
                        host_name = host_name_elem.get_text(strip=True) if host_name_elem else "Unknown Host"
                        
                        # Load host profile page
                        driver.get(host_url)
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                        )
                        
                        # Parse host page
                        host_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        
                        # Try to get host name from profile page if not found
                        if host_name == "Unknown Host":
                            host_name_elem = host_soup.select_one('h1, div[class*="name"], div[class*="title"]')
                            if host_name_elem:
                                host_name = host_name_elem.get_text(strip=True)
                        
                        # Find LinkedIn URL
                        linkedin_url = ""
                        # Look for LinkedIn link
                        linkedin_links = host_soup.select('a[href*="linkedin.com"]')
                        if linkedin_links:
                            linkedin_url = linkedin_links[0]['href']
                        
                        # Add to dataset
                        events_data.append({
                            "Event Name": event_title,
                            "Host Name": host_name,
                            "LinkedIn Profile URL": linkedin_url
                        })
                        logger.info(f"Added host: {host_name} for event: {event_title}")
                        
                    except Exception as e:
                        logger.error(f"Error processing host {host_url}: {str(e)}")
                        
                    # Prevent rate limiting
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error processing event {event_url}: {str(e)}")
            
            # Prevent rate limiting
            time.sleep(2)
            
        # Return the collected data
        if events_data:
            st.success(f"Successfully extracted {len(events_data)} entries!")
            return pd.DataFrame(events_data)
        else:
            st.warning("No data could be extracted from the events.")
            return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        st.error(f"Scraping failed: {str(e)}")
        return pd.DataFrame()
        
    finally:
        driver.quit()

# Function to create a beautifully formatted CSV
def get_formatted_csv(df):
    # Create a CSV string with headers and formatting
    csv_string = "Hidevs Internship Work - BHIVE Events Data\n"
    csv_string += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    csv_string += df.to_csv(index=False)
    return csv_string.encode('utf-8')

# Function to create a download link
def get_download_link(csv):
    b64 = base64.b64encode(csv).decode()
    current_date = datetime.now().strftime("%Y-%m-%d")
    download_filename = f"bhive_events_data_{current_date}.csv"
    href = f'<a href="data:file/csv;base64,{b64}" download="{download_filename}" class="download-btn"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>Download CSV</a>'
    return href

# Main app
def main():
    # Header
    st.markdown("<h1>BHIVE Events Data Extractor</h1>", unsafe_allow_html=True)
    
    # Information section
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    <p>This tool extracts information from BHIVE events on Lu.ma, including:</p>
    <ul>
        <li>Event Name</li>
        <li>Host Name</li>
        <li>LinkedIn Profile URL of Host</li>
    </ul>
    <p>The tool is pre-configured to scrape from <a href="https://lu.ma/START_by_BHIVE" target="_blank">https://lu.ma/START_by_BHIVE</a></p>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add a troubleshooting section
    with st.expander("Troubleshooting & Help"):
        st.markdown("""
        ### Common Issues and Solutions
        
        - **Chrome Driver Error**: The app will attempt to install Chrome driver automatically. If it fails, ensure you have Google Chrome installed on your system.
        
        - **No Events Found**: The page structure might have changed or the URL might be incorrect. Try using a different Lu.ma URL with known events.
        
        - **Slow Processing**: Scraping takes time as the tool needs to visit each event and host page. Be patient during extraction.
        
        - **Data Not Complete**: Some LinkedIn profiles might not be found if they're not properly linked on the host's page.
        """)
    
    # Optional custom URL input
    use_custom_url = st.checkbox("Use a different Lu.ma URL")
    
    if use_custom_url:
        url = st.text_input("Enter Lu.ma URL:", value="https://lu.ma/START_by_BHIVE")
    else:
        url = "https://lu.ma/START_by_BHIVE"
    
    # Scrape button
    if st.button("🚀 Extract BHIVE Events Data"):
        try:
            # Create a placeholder for real-time updates
            status_placeholder = st.empty()
            status_placeholder.info("Initializing scraper...")
            
            # Perform the scraping
            df = scrape_bhive_events(url)
            
            if not df.empty:
                # Display the data
                st.markdown("<h3>Extracted Event and Host Data</h3>", unsafe_allow_html=True)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Event Name": st.column_config.TextColumn("Event Name", width="large"),
                        "Host Name": st.column_config.TextColumn("Host Name", width="medium"),
                        "LinkedIn Profile URL": st.column_config.LinkColumn("LinkedIn Profile", width="medium", display_text="View Profile"),
                    }
                )
                
                # Download section
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown('<div class="container">', unsafe_allow_html=True)
                st.markdown("<h3>Download the Data</h3>", unsafe_allow_html=True)
                st.markdown("<p>Download the complete dataset in CSV format with proper formatting and title.</p>", unsafe_allow_html=True)
                
                # Create formatted CSV and download button
                csv = get_formatted_csv(df)
                st.markdown('<div style="display:flex; justify-content:center;">', unsafe_allow_html=True)
                st.markdown(get_download_link(csv), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.warning("No data could be extracted. Please check if the URL is correct or try again later.")
                
        except Exception as e:
            st.error(f"An error occurred during scraping: {str(e)}")
    
    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="footer">© 2024 Hidevs Internship Program | Created with ❤️ by Hidevs Team</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
