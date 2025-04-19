"""
Lu.ma Event Data Extractor for Streamlit
----------------------------------------

This application extracts event data from Lu.ma/START_by_BHIVE,
collecting event information and participant LinkedIn URLs.
"""

import streamlit as st
import pandas as pd
import requests
import base64
import re
import io
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="BHIVE Events Data Extractor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS for better UI
st.markdown("""
<style>
    /* Overall Page Styling */
    .main {
        padding: 2rem;
    }
    
    /* Typography */
    h1 {
        color: #4fc3f7;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
        padding-bottom: 1rem;
        border-bottom: 2px solid #4fc3f7;
    }
    
    /* Download button */
    .download-btn {
        display: inline-block;
        background-color: #4fc3f7;
        color: #ffffff;
        padding: 0.75rem 1.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
        text-decoration: none;
        margin-top: 1rem;
    }
    
    /* Info box */
    .info-box {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid #4fc3f7;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Cache to avoid fetching the same profile multiple times
linkedin_cache = {}

def clean_url(url):
    """Clean a URL by removing query parameters"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def get_linkedin_url_from_luma_user(user_url, progress_text=None):
    """
    Fetch the LinkedIn URL from a Lu.ma user profile page with caching
    
    Args:
        user_url (str): The Lu.ma user profile URL
        progress_text: Optional Streamlit text element for updates
        
    Returns:
        dict: Dictionary with LinkedIn URL and user name
    """
    # Clean the URL to avoid duplicates in cache
    clean_user_url = clean_url(user_url)
    
    # Check cache first
    if clean_user_url in linkedin_cache:
        return linkedin_cache[clean_user_url]
    
    try:
        if progress_text:
            progress_text.text(f"Fetching LinkedIn from: {clean_user_url}")
        logger.info(f"Fetching URL: {clean_user_url}")
        
        # Make request to the user profile page
        response = requests.get(clean_user_url)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch user profile: {clean_user_url} (Status: {response.status_code})")
            linkedin_cache[clean_user_url] = None
            return None
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to get user name
        user_name = None
        name_elem = soup.select_one('h1.text-2xl') or soup.select_one('h2.font-bold') or soup.select_one('h1') or soup.select_one('div.fw-medium.text-ellipses') or soup.select_one('div[class*="name"]')
        if name_elem:
            user_name = name_elem.text.strip()
        
        # Look for LinkedIn links
        linkedin_pattern = re.compile(r'https?://(www\.)?linkedin\.com/[^\s"\'<>]+')
        
        # First try to find LinkedIn links in anchor tags
        linkedin_url = None
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href', '')
            if linkedin_pattern.match(href):
                linkedin_url = href
                break
        
        # Also look for social links section specifically
        social_links = soup.select('a.social-link') or soup.select('a[aria-label="LinkedIn"]') or soup.select('a[href*="linkedin.com"]')
        for link in social_links:
            href = link.get('href', '')
            if 'linkedin.com' in href:
                linkedin_url = href
                break
        
        # If not found in anchor tags, look in the entire HTML
        if not linkedin_url:
            matches = linkedin_pattern.findall(response.text)
            if matches:
                linkedin_url = matches[0]  # Return the first match
        
        # Store in cache
        result = {
            'linkedin_url': linkedin_url,
            'name': user_name
        }
        linkedin_cache[clean_user_url] = result
        return result
        
    except Exception as e:
        logger.error(f"Error fetching LinkedIn from {clean_user_url}: {str(e)}")
        linkedin_cache[clean_user_url] = None
        return None

def extract_event_links_from_calendar(url, progress_text=None):
    """
    Extract event links from a Lu.ma calendar page
    
    Args:
        url (str): The calendar URL
        progress_text: Optional Streamlit text element for updates
        
    Returns:
        list: List of event URLs
    """
    try:
        if progress_text:
            progress_text.text(f"Fetching calendar page: {url}")
        logger.info(f"Fetching URL: {url}")
        
        # Make request to the calendar page
        response = requests.get(url)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch calendar page: {url} (Status: {response.status_code})")
            return []
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all event links based on classes mentioned in the query
        event_links = []
        
        # Look for links with specific class structure first
        event_links_elements = soup.select('a.event-link') or soup.select('a.content-link')
        for element in event_links_elements:
            href = element.get('href', '')
            if href and href.startswith('/') and not href.startswith('/user/'):
                # Convert relative URL to absolute
                full_url = urljoin("https://lu.ma", href)
                event_links.append(full_url)
        
        # If no specific class links found, try the generic pattern
        if not event_links:
            event_pattern = re.compile(r'^/[a-zA-Z0-9]+$')
            for a_tag in soup.find_all('a'):
                href = a_tag.get('href', '')
                if href and event_pattern.match(href) and '/user/' not in href and '/u/' not in href:
                    # Convert relative URL to absolute
                    full_url = urljoin("https://lu.ma", href)
                    event_links.append(full_url)
        
        # Remove duplicates
        event_links = list(set(event_links))
        
        if progress_text:
            progress_text.text(f"Found {len(event_links)} event links")
        logger.info(f"Extracted {len(event_links)} event links")
        
        return event_links
        
    except Exception as e:
        logger.error(f"Error extracting event links from {url}: {str(e)}")
        return []

def extract_event_data(url, progress_bar=None, progress_text=None):
    """
    Extract event details from a Lu.ma event URL
    
    Args:
        url (str): The event URL
        progress_bar: Optional Streamlit progress bar
        progress_text: Optional Streamlit text element for updates
        
    Returns:
        tuple: (event_data, participant_links)
    """
    if progress_text:
        progress_text.text(f"Fetching event page: {url}")
    if progress_bar:
        progress_bar.progress(0.1)
    logger.info(f"Fetching URL: {url}")
    
    try:
        # Fetch the event page
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch event page: {url} (Status: {response.status_code})")
            return None, []
        
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        
        # Initialize event data
        event_data = {
            "event_url": url,
            "event_id": urlparse(url).path.strip('/'),
            "event_name": "Unknown Event",
            "event_date": None,
            "event_description": None,
            "participant_count": 0
        }
        
        # Extract event name (usually the largest heading)
        event_name_elem = soup.select_one('h1') or soup.select_one('h2.text-2xl') or soup.select_one('.text-3xl')
        if event_name_elem:
            event_data["event_name"] = event_name_elem.text.strip()
        
        # Extract event date
        date_elem = soup.select_one('time') or soup.select_one('p:contains("202")')
        if date_elem:
            event_data["event_date"] = date_elem.text.strip()
        
        # Extract event description
        desc_elem = soup.select_one('div.whitespace-pre-wrap') or soup.select_one('p.text-gray-600')
        if desc_elem:
            event_data["event_description"] = desc_elem.text.strip()
        
        if progress_bar:
            progress_bar.progress(0.3)
        if progress_text:
            progress_text.text("Searching for participant profiles...")
        
        # Look for host profile links with the specific class structure
        user_links = set()  # Use a set to avoid duplicates
        
        # Look for links with the specific class mentioned in the query
        host_links = soup.select('a.host-row') or soup.select('a.lux-menu-trigger-wrapper')
        for a_tag in host_links:
            href = a_tag.get('href', '')
            if href and href.startswith('/user/'):
                # Convert relative URL to absolute
                full_url = urljoin("https://lu.ma", href)
                user_links.add(full_url)
        
        # If no specific links found, try the generic patterns as fallback
        if not user_links:
            # Extract participant information - patterns for user profiles
            user_patterns = [
                re.compile(r'https?://(www\.)?lu\.ma/user/[^\s"\'<>]+'),
                re.compile(r'https?://(www\.)?lu\.ma/u/[^\s"\'<>]+'),
                re.compile(r'https?://(www\.)?lu\.ma/p/[^\s"\'<>]+')
            ]
            
            # Search with each pattern
            for pattern in user_patterns:
                # Find all links in the page
                for a_tag in soup.find_all('a'):
                    href = a_tag.get('href', '')
                    if pattern.match(href):
                        user_links.add(href)
                
                # Also search in the raw HTML for any user links that might not be in <a> tags
                for match in pattern.finditer(content):
                    user_links.add(match.group(0))
        
        # Also look for relative profile links and convert them
        relative_pattern = re.compile(r'^/user/[^\s"\'<>]+$')
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href', '')
            if relative_pattern.match(href):
                # Convert relative URL to absolute
                full_url = urljoin("https://lu.ma", href)
                user_links.add(full_url)
        
        # Update participant count
        event_data["participant_count"] = len(user_links)
        
        if progress_bar:
            progress_bar.progress(0.5)
        if progress_text:
            progress_text.text(f"Found {len(user_links)} participant profiles")
        
        return event_data, user_links
        
    except Exception as e:
        logger.error(f"Error extracting event data from {url}: {str(e)}")
        return None, []

def fetch_participant_data(user_links, progress_bar=None, progress_text=None):
    """
    Fetch data for each participant including their LinkedIn URL using parallel processing
    
    Args:
        user_links (set): Set of Lu.ma user profile URLs
        progress_bar: Optional Streamlit progress bar
        progress_text: Optional Streamlit text element for updates
        
    Returns:
        list: List of participant data dictionaries
    """
    participants = []
    
    if not user_links:
        return participants
    
    # Calculate progress increment per participant
    if progress_bar:
        progress_increment = 0.5 / len(user_links)
        current_progress = 0.5  # Start from 50%
    
    # Use ThreadPoolExecutor for parallel fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Start the fetching tasks
        future_to_url = {executor.submit(get_linkedin_url_from_luma_user, url, progress_text): url for url in user_links}
        
        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_url)):
            url = future_to_url[future]
            if progress_bar:
                current_progress += progress_increment
                progress_bar.progress(min(current_progress, 1.0))
            if progress_text:
                progress_text.text(f"Processing participant {i+1}/{len(user_links)}")
            
            # Basic participant data
            participant = {
                "luma_profile": url,
                "name": None,
                "linkedin_url": None
            }
            
            # Extract user ID from URL
            user_id_match = re.search(r'user/([\w-]+)', url)
            if user_id_match:
                user_id = user_id_match.group(1)
                participant["user_id"] = user_id
            
            # Get result from future
            try:
                result = future.result()
                if result:
                    participant["linkedin_url"] = result.get('linkedin_url')
                    participant["name"] = result.get('name')
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
            
            participants.append(participant)
    
    return participants

def create_formatted_csv(events_data, all_participants):
    """
    Create a formatted CSV string from event and participant data
    
    Args:
        events_data (list): List of event dictionaries
        all_participants (dict): Dictionary mapping event URLs to participant lists
        
    Returns:
        str: CSV data as string
    """
    # Prepare rows for CSV
    rows = []
    
    # Add header with metadata
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata = [
        "# Hidevs Internship Work - BHIVE Events Data",
        f"# Extraction Date: {current_time}",
        f"# Source: https://lu.ma/START_by_BHIVE",
        f"# Format: CSV Version 1.0",
        "#-----------------------------------------------------------",
        ""
    ]
    
    # Add data rows
    for event in events_data:
        event_url = event["event_url"]
        participants = all_participants.get(event_url, [])
        
        for participant in participants:
            row = {
                "Event Name": event["event_name"],
                "Event Date": event["event_date"] or "N/A",
                "Host Name": participant.get("name") or "Unknown",
                "LinkedIn Profile URL": participant.get("linkedin_url") or "Not Available"
            }
            rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Add sequence numbers
    if not df.empty:
        df.insert(0, 'No.', range(1, len(df) + 1))
    
    # Convert to CSV string
    output = io.StringIO()
    output.write("\n".join(metadata))
    if not df.empty:
        df.to_csv(output, index=False)
    else:
        output.write("No data available")
    
    return output.getvalue()

def get_download_link(csv_string, filename="luma_events_data.csv"):
    """
    Generate a download link for the CSV data
    
    Args:
        csv_string (str): CSV data as string
        filename (str): Name of the file to download
    
    Returns:
        str: HTML for download link
    """
    b64 = base64.b64encode(csv_string.encode()).decode()
    href = f'<a href="data:text/csv;base64,{b64}" download="{filename}" class="download-btn">📥 Download CSV</a>'
    return href

def main():
    logger.info("Starting Lu.ma event scraper")
    
    # Header
    st.markdown("<h1>BHIVE Events Data Extractor</h1>", unsafe_allow_html=True)
    
    # Info box
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    <p>This tool extracts information from BHIVE events on Lu.ma, including:</p>
    <ul>
        <li>Event Name & Date</li>
        <li>Host Names</li>
        <li>LinkedIn Profile URLs</li>
    </ul>
    <p>The data is compiled into a neatly formatted CSV file that can be downloaded.</p>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # URL input
    url = st.text_input("Enter Lu.ma event URL:", value="https://lu.ma/START_by_BHIVE", 
                       help="Enter a Lu.ma calendar or event URL to extract data")
    
    # Advanced options
    with st.expander("Advanced Options"):
        max_participants = st.slider("Maximum participants to process per event", 1, 100, 50)
        include_description = st.checkbox("Include event descriptions in output", value=False)
        process_all_calendar_events = st.checkbox("Process all events from calendar page", value=True)
    
    # Extract button
    if st.button("🚀 Extract Event Data"):
        # Set up progress tracking
        progress_bar = st.progress(0)
        progress_text = st.empty()
        
        progress_text.text("Starting extraction process...")
        logger.info(f"Fetching URL: {url}")
        
        # Process the event(s)
        events_data = []
        all_participants = {}
        
        # Check if it's a calendar page and extract event links
        event_urls = [url]  # Default to just the provided URL
        
        if process_all_calendar_events and "START_by_BHIVE" in url:
            # This is likely a calendar page, extract all event links
            calendar_event_links = extract_event_links_from_calendar(url, progress_text)
            if calendar_event_links:
                event_urls = calendar_event_links
                progress_text.text(f"Extracted {len(event_urls)} event links")
        
        # Process each event
        total_events = len(event_urls)
        for i, event_url in enumerate(event_urls):
            progress_text.text(f"Processing event {i+1}/{total_events}: {event_url}")
            logger.info(f"Processing event: {event_url}")
            
            # Extract event data
            event_data, user_links = extract_event_data(event_url, progress_bar, progress_text)
            
            if event_data and user_links:
                events_data.append(event_data)
                
                # Limit participants if needed
                if len(user_links) > max_participants:
                    progress_text.text(f"Limiting to {max_participants} out of {len(user_links)} participants")
                    user_links = list(user_links)[:max_participants]
                
                # Fetch participant data
                participants = fetch_participant_data(user_links, progress_bar, progress_text)
                all_participants[event_url] = participants
            
            # Update overall progress
            progress_bar.progress((i + 1) / total_events)
        
        # Show results
        if events_data:
            progress_bar.progress(1.0)
            progress_text.text("Extraction complete! Preparing data...")
            
            # Calculate overall stats
            total_participants = sum(len(participants) for participants in all_participants.values())
            linkedin_count = sum(
                1 for participants in all_participants.values() 
                for p in participants if p.get("linkedin_url")
            )
            success_rate = linkedin_count / total_participants if total_participants else 0
            
            st.success(f"✅ Successfully extracted data from {len(events_data)} events!\n\n"
                     f"Found: {total_participants} total participants\n"
                     f"LinkedIn profiles found: {linkedin_count} ({success_rate:.1%})")
            
            # Display results in tabs
            tab1, tab2 = st.tabs(["📊 Data Preview", "📋 Details"])
            
            with tab1:
                # Create a clean DataFrame for display
                display_data = []
                for event in events_data:
                    event_url = event["event_url"]
                    participants = all_participants.get(event_url, [])
                    
                    for participant in participants:
                        row = {
                            "Event Name": event["event_name"],
                            "Event Date": event["event_date"] or "N/A",
                            "Host Name": participant.get("name") or "Unknown",
                            "LinkedIn Profile": participant.get("linkedin_url") or "Not Available"
                        }
                        display_data.append(row)
                
                if display_data:
                    df = pd.DataFrame(display_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Create CSV and download link
                    csv_string = create_formatted_csv(events_data, all_participants)
                    st.markdown(
                        get_download_link(csv_string, f"luma_events_data.csv"),
                        unsafe_allow_html=True
                    )
                    logger.info(f"✅ Exported {len(display_data)} records to luma_events_data.csv")
                else:
                    st.warning("No data available to display.")
            
            with tab2:
                # Show detailed event information
                for event in events_data:
                    st.subheader(event["event_name"])
                    st.write(f"**Date:** {event['event_date'] or 'N/A'}")
                    st.write(f"**URL:** {event['event_url']}")
                    st.write(f"**Participants found:** {event['participant_count']}")
                    
                    if include_description and event["event_description"]:
                        st.write("**Description:**")
                        st.write(event["event_description"])
        else:
            st.error("Failed to extract data from the provided URL(s). Please check the URL and try again.")
        
        logger.info("Scraping completed")
    
    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="footer">© 2024 Hidevs Internship Program | Created with ❤️ by Hidevs Team</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()