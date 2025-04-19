"""
Streamlit UI for Lu.ma Event Data Extractor
-------------------------------------------

This application provides a web interface for the Lu.ma event data extractor,
allowing users to extract and download event data from Lu.ma/START_by_BHIVE.
"""

import streamlit as st
import pandas as pd
import requests
import base64
import os
import re
import csv
import json
import io
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        background-color: #0e1117;
        color: #f7f7f7;
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
    
    h2, h3 {
        color: #4fc3f7;
        font-weight: 600;
    }
    
    /* Components */
    .stButton > button {
        background-color: #4fc3f7;
        color: #0e1117;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 0.375rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #29b6f6;
        box-shadow: 0 0 15px rgba(79, 195, 247, 0.5);
    }
    
    /* Text input */
    .stTextInput > div > div > input {
        background-color: #1e2130;
        color: #f7f7f7;
        border: 1px solid #4fc3f7;
        border-radius: 0.375rem;
    }
    
    /* Container styling */
    .css-18e3th9 {
        padding-top: 1rem;
    }
    
    /* Results container */
    .results-container {
        background-color: #1e2130;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-top: 2rem;
        border-left: 4px solid #4fc3f7;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #4fc3f7;
    }
    
    /* DataFrame styling */
    [data-testid="stDataFrame"] {
        background-color: #1e2130 !important;
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
    [data-testid="stDataFrame"] th {
        background-color: #4fc3f7 !important;
        color: #0e1117 !important;
        font-weight: 600 !important;
        text-align: left !important;
        padding: 0.75rem 1rem !important;
    }
    
    /* Download button */
    .download-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: #4fc3f7;
        color: #0e1117;
        padding: 0.75rem 1.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
        text-decoration: none;
        transition: all 0.3s ease;
        margin-top: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .download-btn:hover {
        background-color: #29b6f6;
        transform: translateY(-2px);
        box-shadow: 0 6px 10px rgba(0, 0, 0, 0.2);
    }
    
    /* Info box */
    .info-box {
        background-color: #1e2130;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid #4fc3f7;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #a0aec0;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #2d3748;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #4fc3f7;
    }
</style>
""", unsafe_allow_html=True)

# Cache to avoid fetching the same profile multiple times
linkedin_cache = {}

def clean_url(url):
    """
    Clean a URL by removing query parameters
    """
    parsed = urlparse(url)
    # Keep only the path
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def get_linkedin_url_from_luma_user(user_url, progress_text):
    """
    Fetch the LinkedIn URL from a Lu.ma user profile page with caching
    
    Args:
        user_url (str): The Lu.ma user profile URL
        progress_text: Streamlit text element for updates
        
    Returns:
        dict: Dictionary with LinkedIn URL and user name
    """
    # Clean the URL to avoid duplicates in cache
    clean_user_url = clean_url(user_url)
    
    # Check cache first
    if clean_user_url in linkedin_cache:
        return linkedin_cache[clean_user_url]
    
    try:
        progress_text.text(f"Fetching LinkedIn from: {clean_user_url}")
        
        # Make request to the user profile page
        response = requests.get(clean_user_url)
        if response.status_code != 200:
            st.warning(f"Failed to fetch user profile: {clean_user_url} (Status: {response.status_code})")
            linkedin_cache[clean_user_url] = None
            return None
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to get user name
        user_name = None
        name_elem = soup.select_one('h1.text-2xl') or soup.select_one('h2.font-bold') or soup.select_one('h1') or soup.select_one('div[class*="name"]')
        if name_elem:
            user_name = name_elem.text.strip()
        
        # Look for LinkedIn links (regular expression pattern)
        linkedin_pattern = re.compile(r'https?://(www\.)?linkedin\.com/[^\s"\'<>]+')
        
        # First try to find LinkedIn links in anchor tags
        linkedin_url = None
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href', '')
            if linkedin_pattern.match(href):
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
        st.error(f"Error fetching LinkedIn from {clean_user_url}: {str(e)}")
        linkedin_cache[clean_user_url] = None
        return None

def extract_event_data(url, progress_bar, progress_text):
    """
    Extract event details from a Lu.ma event URL
    
    Args:
        url (str): The event URL
        progress_bar: Streamlit progress bar
        progress_text: Streamlit text element for updates
        
    Returns:
        tuple: (event_data, participant_links)
    """
    progress_text.text(f"Fetching event page: {url}")
    progress_bar.progress(0.1)
    
    try:
        # Fetch the event page
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Failed to fetch event page: {url} (Status: {response.status_code})")
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
        
        # Extract event date (usually found in a time element or text with date format)
        date_elem = soup.select_one('time') or soup.select_one('p:contains("202")')
        if date_elem:
            event_data["event_date"] = date_elem.text.strip()
        
        # Extract event description
        desc_elem = soup.select_one('div.whitespace-pre-wrap') or soup.select_one('p.text-gray-600')
        if desc_elem:
            event_data["event_description"] = desc_elem.text.strip()
        
        progress_bar.progress(0.3)
        progress_text.text("Searching for participant profiles...")
        
        # Extract participant information - patterns for user profiles
        user_patterns = [
            re.compile(r'https?://(www\.)?lu\.ma/user/[^\s"\'<>]+'),
            re.compile(r'https?://(www\.)?lu\.ma/u/[^\s"\'<>]+'),
            re.compile(r'https?://(www\.)?lu\.ma/p/[^\s"\'<>]+')
        ]
        
        user_links = set()  # Use a set to avoid duplicates
        
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
        
        # Update participant count
        event_data["participant_count"] = len(user_links)
        
        progress_bar.progress(0.5)
        progress_text.text(f"Found {len(user_links)} participant profiles")
        
        return event_data, user_links
        
    except Exception as e:
        st.error(f"Error extracting event data from {url}: {str(e)}")
        return None, []

def fetch_participant_data(user_links, progress_bar, progress_text):
    """
    Fetch data for each participant including their LinkedIn URL using parallel processing
    
    Args:
        user_links (set): Set of Lu.ma user profile URLs
        progress_bar: Streamlit progress bar
        progress_text: Streamlit text element for updates
        
    Returns:
        list: List of participant data dictionaries
    """
    participants = []
    
    if not user_links:
        return participants
    
    # Calculate progress increment per participant
    progress_increment = 0.5 / len(user_links)
    current_progress = 0.5  # Start from 50%
    
    # Use ThreadPoolExecutor for parallel fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Start the fetching tasks
        future_to_url = {executor.submit(get_linkedin_url_from_luma_user, url, progress_text): url for url in user_links}
        
        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_url)):
            url = future_to_url[future]
            current_progress += progress_increment
            progress_bar.progress(min(current_progress, 1.0))
            progress_text.text(f"Processing participant {i+1}/{len(user_links)}")
            
            # Basic participant data
            participant = {
                "luma_profile": url,
                "name": None,
                "linkedin_url": None
            }
            
            # Extract user ID from URL
            user_id_match = re.search(r'user/(usr-[a-zA-Z0-9]+)', url)
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
                st.error(f"Error processing {url}: {str(e)}")
            
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
    df.insert(0, 'No.', range(1, len(df) + 1))
    
    # Convert to CSV string
    output = io.StringIO()
    output.write("\n".join(metadata))
    df.to_csv(output, index=False)
    
    return output.getvalue()

def get_download_link(csv_string, filename="bhive_events_data.csv"):
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
    
    # Extract button
    if st.button("🚀 Extract Event Data"):
        # Set up progress tracking
        progress_bar = st.progress(0)
        progress_text = st.empty()
        
        progress_text.text("Starting extraction process...")
        
        # Process the event
        events_data = []
        all_participants = {}
        
        # Extract event data
        event_data, user_links = extract_event_data(url, progress_bar, progress_text)
        
        if event_data and user_links:
            events_data.append(event_data)
            
            # Limit participants if needed
            if len(user_links) > max_participants:
                progress_text.text(f"Limiting to {max_participants} out of {len(user_links)} participants")
                user_links = list(user_links)[:max_participants]
            
            # Fetch participant data
            participants = fetch_participant_data(user_links, progress_bar, progress_text)
            all_participants[url] = participants
            
            # Calculate success rate
            linkedin_count = sum(1 for p in participants if p.get("linkedin_url"))
            success_rate = linkedin_count / len(participants) if participants else 0
            
            # Show results
            progress_bar.progress(1.0)
            progress_text.text("Extraction complete! Preparing data...")
            
            st.success(f"✅ Successfully extracted event data!\n\n"
                     f"Found: {len(participants)} participants\n"
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
                        get_download_link(csv_string, f"bhive_events_{datetime.now().strftime('%Y%m%d')}.csv"),
                        unsafe_allow_html=True
                    )
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
            st.error("Failed to extract data from the provided URL. Please check the URL and try again.")
    
    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="footer">© 2024 Hidevs Internship Program | Created with ❤️ by Hidevs Team</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
