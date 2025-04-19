
"""
Batch Lu.ma Event Data Extractor

This script extracts data from multiple Lu.ma event pages and compiles all the information into a single CSV file.
For each event, it extracts:
1. Event details (name, date, description)
2. Participant profiles
3. LinkedIn URLs for each participant by visiting their Lu.ma profile pages

The final output is a comprehensive CSV file with all events and participants.
"""

import csv
import json
import re
import os
from urllib.parse import urlparse, parse_qs
from langchain_community.document_loaders import RecursiveUrlLoader
from bs4 import BeautifulSoup
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pandas as pd

# Cache to avoid fetching the same profile multiple times
linkedin_cache = {}

def clean_url(url):
    """
    Clean a URL by removing query parameters
    """
    parsed = urlparse(url)
    # Keep only the path
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def get_linkedin_url_from_luma_user(user_url):
    """
    Fetch the LinkedIn URL from a Lu.ma user profile page with caching
    
    Args:
        user_url (str): The Lu.ma user profile URL
        
    Returns:
        str: LinkedIn URL if found, otherwise None
    """
    # Clean the URL to avoid duplicates in cache
    clean_user_url = clean_url(user_url)
    
    # Check cache first
    if clean_user_url in linkedin_cache:
        return linkedin_cache[clean_user_url]
    
    try:
        # Make request to the user profile page
        response = requests.get(clean_user_url)
        if response.status_code != 200:
            print(f"Failed to fetch user profile: {clean_user_url} (Status: {response.status_code})")
            linkedin_cache[clean_user_url] = None
            return None
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to get user name
        user_name = None
        name_elem = soup.select_one('h1.text-2xl') or soup.select_one('h2.font-bold')
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
        print(f"Error fetching LinkedIn from {clean_user_url}: {str(e)}")
        linkedin_cache[clean_user_url] = None
        return None

def extract_event_data(content, event_url):
    """
    Extract event details from the HTML content
    
    Args:
        content (str): The HTML content of the event page
        event_url (str): The event URL
        
    Returns:
        dict: Event details and set of user links
    """
    soup = BeautifulSoup(content, 'html.parser')
    
    # Initialize event data
    event_data = {
        "event_url": event_url,
        "event_id": urlparse(event_url).path.strip('/'),
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
    
    # Extract participant information
    # Look for user profile links that match Lu.ma user pattern
    user_pattern = re.compile(r'https?://(www\.)?lu\.ma/user/[^\s"\'<>]+')
    
    user_links = set()  # Use a set to avoid duplicates
    
    # Find all links in the page
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href', '')
        if user_pattern.match(href):
            user_links.add(href)
    
    # Also search in the raw HTML for any user links that might not be in <a> tags
    for match in user_pattern.finditer(content):
        user_links.add(match.group(0))
    
    # Update participant count
    event_data["participant_count"] = len(user_links)
    
    print(f"Event: {event_data['event_name']} - Found {len(user_links)} participant profiles")
    
    return event_data, user_links

def fetch_participant_data(user_links, max_workers=5):
    """
    Fetch data for each participant including their LinkedIn URL using parallel processing
    
    Args:
        user_links (set): Set of Lu.ma user profile URLs
        max_workers (int): Maximum number of parallel workers
        
    Returns:
        list: List of participant data dictionaries
    """
    participants = []
    
    # Use ThreadPoolExecutor for parallel fetching
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Start the fetching tasks
        future_to_url = {executor.submit(get_linkedin_url_from_luma_user, url): url for url in user_links}
        
        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_url)):
            url = future_to_url[future]
            print(f"Processing participant {i+1}/{len(user_links)}")
            
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
                print(f"Error processing {url}: {str(e)}")
            
            participants.append(participant)
    
    return participants

def process_event(event_url):
    """
    Process a single event URL to extract all data
    
    Args:
        event_url (str): The event URL
        
    Returns:
        tuple: (event_data, participants)
    """
    print(f"\nProcessing event: {event_url}")
    
    # Initialize the RecursiveUrlLoader
    loader = RecursiveUrlLoader(
        event_url,
        max_depth=1,
        use_async=False,
        timeout=15,
        check_response_status=True,
        continue_on_failure=True
    )
    
    # Load documents
    docs = []
    docs_lazy = loader.lazy_load()
    
    for doc in docs_lazy:
        docs.append(doc)
    
    if not docs:
        print(f"Failed to load content for {event_url}")
        return None, []
    
    # Extract event data and participant links
    event_data, user_links = extract_event_data(docs[0].page_content, event_url)
    
    # Fetch data for each participant
    print(f"Fetching LinkedIn profiles for {len(user_links)} participants...")
    participants = fetch_participant_data(user_links)
    
    return event_data, participants

def save_to_csv(events_data, all_participants, filename="luma_events_data.csv"):
    """
    Save all event data and participants to a single CSV file
    
    Args:
        events_data (list): List of event details dictionaries
        all_participants (dict): Dictionary mapping event URLs to participant lists
        filename (str): Output filename
    """
    # Define CSV fields
    fields = [
        "event_name", "event_url", "event_id", "event_date", 
        "participant_name", "luma_profile", "linkedin_url"
    ]
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    
    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        
        # For each event, write all participants
        for event in events_data:
            event_url = event["event_url"]
            participants = all_participants.get(event_url, [])
            
            for participant in participants:
                row = {
                    "event_name": event["event_name"],
                    "event_url": event["event_url"],
                    "event_id": event["event_id"],
                    "event_date": event["event_date"],
                    "participant_name": participant.get("name", "Unknown"),
                    "luma_profile": participant["luma_profile"],
                    "linkedin_url": participant.get("linkedin_url", "")
                }
                writer.writerow(row)
    
    print(f"\nData saved to {filename}")
    
    # Also save the complete data as JSON for reference
    json_filename = filename.replace(".csv", ".json")
    complete_data = {
        "events": events_data,
        "participants_by_event": all_participants
    }
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(complete_data, f, indent=2)
    
    print(f"Complete data saved to {json_filename}")

def main():
    # List of Lu.ma event URLs to process
    event_urls = [
        "https://lu.ma/18tw2f7h?tk=2n42Yn",
        # Add more event URLs as needed
        # "https://lu.ma/another-event",
        # "https://lu.ma/third-event",
    ]
    
    print(f"Processing {len(event_urls)} Lu.ma events")
    
    # Process each event
    events_data = []
    all_participants = {}
    
    for event_url in event_urls:
        event_data, participants = process_event(event_url)
        
        if event_data:
            events_data.append(event_data)
            all_participants[event_url] = participants
    
    # Save all data to CSV
    save_to_csv(events_data, all_participants)
    
    # Print summary
    print("\nSummary:")
    print(f"Processed {len(events_data)} events")
    total_participants = sum(len(participants) for participants in all_participants.values())
    print(f"Found {total_participants} total participants")
    linkedin_count = sum(
        1 for participants in all_participants.values() 
        for p in participants if p.get("linkedin_url")
    )
    print(f"Found {linkedin_count} LinkedIn URLs ({linkedin_count/total_participants*100:.1f}% of participants)")

def get_formatted_csv(df):
    """
    Create a beautifully formatted CSV file from the DataFrame
    
    Args:
        df (DataFrame): Pandas DataFrame containing the event data
        
    Returns:
        bytes: Encoded CSV data
    """
    # Create a CSV string with proper headers and metadata
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    csv_string = f"# Hidevs Internship Work - BHIVE Events Data\n"
    csv_string += f"# Extraction Date: {current_time}\n"
    csv_string += f"# Total Records: {len(df)}\n"
    csv_string += f"# Source: https://lu.ma/START_by_BHIVE\n"
    csv_string += f"# Format: CSV Version 1.0\n"
    csv_string += f"# -------------------------------------------------\n\n"
    
    # Clean the data before export
    clean_df = df.copy()
    
    # Add sequence numbers for better readability
    clean_df.insert(0, 'No.', range(1, len(clean_df) + 1))
    
    # Clean and standardize LinkedIn URLs
    if 'LinkedIn Profile URL' in clean_df.columns:
        clean_df['LinkedIn Profile URL'] = clean_df['LinkedIn Profile URL'].apply(
            lambda x: x if pd.notnull(x) and x.strip() != "" else "Not Available"
        )
    elif 'linkedin_url' in clean_df.columns:
        clean_df['linkedin_url'] = clean_df['linkedin_url'].apply(
            lambda x: x if pd.notnull(x) and x.strip() != "" else "Not Available"
        )
    
    # Clean event names and participant names
    for name_col in ['Event Name', 'event_name', 'participant_name', 'Host Name', 'name']:
        if name_col in clean_df.columns:
            clean_df[name_col] = clean_df[name_col].astype(str).str.strip()
    
    # Format date columns if they exist
    date_cols = ['event_date', 'Event Date']
    for date_col in date_cols:
        if date_col in clean_df.columns:
            try:
                clean_df[date_col] = pd.to_datetime(clean_df[date_col], errors='ignore')
                clean_df[date_col] = clean_df[date_col].dt.strftime('%Y-%m-%d')
            except:
                pass  # If conversion fails, keep as is
    
    # Export to CSV with proper formatting
    csv_string += clean_df.to_csv(index=False)
    return csv_string.encode('utf-8')

def save_formatted_csv(df, filename="bhive_events_data.csv"):
    """
    Save data to a nicely formatted CSV file
    
    Args:
        df (DataFrame): Pandas DataFrame to save
        filename (str): Output filename
    """
    # Get the CSV content
    csv_content = get_formatted_csv(df)
    
    # Write to file
    with open(filename, 'wb') as f:
        f.write(csv_content)
    
    print(f"\nFormatted data saved to {filename}")
    
    # Return the path to the saved file
    return os.path.abspath(filename)

if __name__ == "__main__":
    main()
