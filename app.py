import pandas as pd
import streamlit as st
import base64
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Hidevs Internship Work",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply enhanced modern CSS for better UI
st.markdown("""
<style>
    /* Overall Page Styling */
    .main {
        padding: 2.5rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Typography */
    h1 {
        color: #1a365d;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(90deg, #1a365d, #3182ce);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    
    h2, h3 {
        color: #2c5282;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    
    p {
        font-family: 'Segoe UI', Arial, sans-serif;
        line-height: 1.6;
    }
    
    /* Components Styling */
    .stButton>button {
        background: linear-gradient(90deg, #1a365d 0%, #2c5282 100%);
        color: white;
        border-radius: 50px;
        padding: 0.6rem 1.5rem;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.9rem;
    }
    
    .stButton>button:hover {
        background: linear-gradient(90deg, #2c5282 0%, #1a365d 100%);
        transform: translateY(-3px);
        box-shadow: 0 7px 14px rgba(0, 0, 0, 0.2);
    }
    
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
    }
    
    .stTextInput>div>div>input {
        border-radius: 50px;
        padding-left: 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Custom Cards */
    .download-container {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        margin-top: 2rem;
        border-left: 5px solid #3182ce;
    }
    
    .info-card {
        background: white;
        padding: 1.8rem;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
        border-left: 5px solid #4299e1;
        transition: transform 0.3s ease;
    }
    
    .info-card:hover {
        transform: translateY(-5px);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8fafc;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Search styling */
    .search-container {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    /* Custom download button */
    .download-btn {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(90deg, #1a365d 0%, #2c5282 100%);
        color: white;
        padding: 15px 30px;
        border-radius: 50px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        margin-top: 10px;
    }
    
    .download-btn:hover {
        background: linear-gradient(90deg, #2c5282 0%, #1a365d 100%);
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.25);
    }
    
    /* Dividers */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, rgba(99,179,237,0), rgba(99,179,237,0.5) 50%, rgba(99,179,237,0) 100%);
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #4a5568;
        font-size: 0.9rem;
        margin-top: 2rem;
    }
    
    /* Table header styling */
    thead tr th {
        background-color: #edf2f7 !important;
        color: #2d3748 !important;
        font-weight: 600 !important;
    }
    
    /* Table row styling */
    tbody tr:nth-child(even) {
        background-color: #f7fafc !important;
    }
    
    tbody tr:hover {
        background-color: #e6f7ff !important;
    }
</style>
""", unsafe_allow_html=True)

# Static event data without Date and Location
def extract_event_data():
    sample_data = [
        {
            "Event Name": "Workshop: Mastering Contextual Leadership: The Art of Playing Multiple Personas",
            "Host Name": "Ravindra M.K, Vijetha & Nikhita Habib",
            "LinkedIn Profile URL": "https://www.linkedin.com/company/bhive-workspace"
        },
        {
            "Event Name": "Ai Day for startups",
            "Host Name": "Ravindra M.K & Vijetha",
            "LinkedIn Profile URL": "https://www.linkedin.com/company/bhive-workspace"
        },
        {
            "Event Name": "New Experiment for CHROs: AI Agents",
            "Host Name": "Waqar Ahmed & Ravindra M.K",
            "LinkedIn Profile URL": "https://www.linkedin.com/company/bhive-workspace"
        },
        {
            "Event Name": "Money Meets Tech - Lessons in Building Wealth & Fintech Products",
            "Host Name": "Women in Product India, Ravindra M.K, Vijetha",
            "LinkedIn Profile URL": "https://www.linkedin.com/company/wip-india/"
        },
        {
            "Event Name": "Build your Mocks with No-Code AI Tools",
            "Host Name": "Ravindra M.K & Vijetha",
            "LinkedIn Profile URL": "https://www.linkedin.com/company/bhive-workspace/"
        },
        {
            "Event Name": "How to get Ranked #1 on Product Hunt",
            "Host Name": "Ravindra M.K & Vijetha",
            "LinkedIn Profile URL": "https://www.linkedin.com/company/bhive-workspace/"
        }
    ]
    return pd.DataFrame(sample_data)

# Function to create a beautifully formatted CSV with a title
def get_formatted_csv(df):
    # Create a CSV string with a title and well-formatted headers
    csv_string = "Hidevs Internship Work\n\n"
    csv_string += df.to_csv(index=False)
    return csv_string.encode('utf-8')

# Function to create a download link with custom styling
def get_download_link(csv):
    b64 = base64.b64encode(csv).decode()
    current_date = datetime.now().strftime("%Y-%m-%d")
    download_filename = f"hidevs_internship_data_{current_date}.csv"
    href = f'<a href="data:file/csv;base64,{b64}" download="{download_filename}" class="download-btn"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:12px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>Download CSV</a>'
    return href

# Main App
def main():
    # Header with beautiful typography
    st.markdown("<h1>✨ Hidevs Internship Work ✨</h1>", unsafe_allow_html=True)
    
    # Information Card
    st.markdown("<div class='info-card'><h3 style='margin-top:0;'>📊 Event & Host Details</h3><p>This dataset contains information about various events hosted by Hidevs.</p></div>", unsafe_allow_html=True)
    
    # Get data
    df = extract_event_data()
    
    # Add search functionality with improved styling
    st.markdown("<div class='search-container'>", unsafe_allow_html=True)
    search_term = st.text_input("🔍 Search Events", placeholder="Type to filter events...")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Filter dataframe based on search
    if search_term:
        filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
    else:
        filtered_df = df
        
    # Display the dataframe with better styling
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Event Name": st.column_config.TextColumn("Event Name", width="large"),
            "Host Name": st.column_config.TextColumn("Host Name", width="medium"),
            "LinkedIn Profile URL": st.column_config.LinkColumn("LinkedIn", width="medium", display_text="View Profile"),
        }
    )
    
    # Download section with improved styling
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='download-container'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0;'>Download Dataset</h3>", unsafe_allow_html=True)
    
    # Create formatted CSV
    csv = get_formatted_csv(df)
    
    # Display download button with custom styling
    st.markdown(get_download_link(csv), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='footer'>© 2024 Hidevs Internship Program | Created with ❤️ by Hidevs Team</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
