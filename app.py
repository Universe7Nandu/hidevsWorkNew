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

# Apply enhanced modern CSS for better UI with improved contrast
st.markdown("""
<style>
    /* Overall Page Styling */
    .main {
        padding: 2.5rem;
        background-color: #1e2a3a;
        color: white;
    }
    .stApp {
        background-color: #1e2a3a;
    }
    
    /* Typography */
    h1 {
        color: #ffffff;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 1rem;
        text-align: center;
        text-shadow: 0 2px 10px rgba(43, 155, 255, 0.3);
    }
    
    h2, h3 {
        color: #ffffff;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    
    p {
        font-family: 'Segoe UI', Arial, sans-serif;
        line-height: 1.6;
        color: #e6e6e6;
        font-size: 1.1rem;
    }
    
    /* Components Styling */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.9rem;
    }
    
    .stButton>button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 100%);
        transform: translateY(-3px);
        box-shadow: 0 7px 14px rgba(59, 130, 246, 0.4);
    }
    
    /* DataTable Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2);
    }
    
    [data-testid="stDataFrame"] table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
    }
    
    [data-testid="stDataFrame"] th {
        background-color: #3b82f6 !important;
        color: white !important;
        padding: 12px 15px !important;
        font-weight: 600 !important;
        text-align: left !important;
        font-size: 14px !important;
        border: none !important;
    }
    
    [data-testid="stDataFrame"] td {
        padding: 12px 15px !important;
        border: none !important;
        font-size: 14px !important;
        color: #333 !important;
    }
    
    [data-testid="stDataFrame"] tr:nth-child(even) {
        background-color: #f3f4f6 !important;
    }
    
    [data-testid="stDataFrame"] tr:nth-child(odd) {
        background-color: #ffffff !important;
    }
    
    [data-testid="stDataFrame"] tr:hover {
        background-color: #e5edff !important;
    }
    
    .stTextInput>div>div>input {
        border-radius: 8px;
        padding: 12px 20px;
        border: 2px solid #3b82f6;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
        background-color: #ffffff;
        color: #333;
        font-size: 1rem;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.4);
    }
    
    .stTextInput>label {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    /* Custom Cards */
    .container {
        background-color: #2d3748;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        border-left: 5px solid #3b82f6;
    }
    
    .info-card {
        background-color: #2d3748;
        border-radius: 12px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        border-left: 5px solid #3b82f6;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .info-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25);
    }
    
    /* Search styling */
    .search-container {
        background-color: #2d3748;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom download button */
    .download-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        text-decoration: none;
        box-shadow: 0 6px 15px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
        margin-top: 1rem;
        width: 200px;
    }
    
    .download-btn:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 100%);
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Dividers */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, rgba(59,130,246,0), rgba(59,130,246,0.5) 50%, rgba(59,130,246,0) 100%);
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #e6e6e6;
        font-size: 0.9rem;
        margin-top: 2rem;
    }
    
    /* App header design */
    .app-header {
        text-align: center;
        padding-bottom: 1.5rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    /* Highlight styling */
    .highlight {
        color: #60a5fa;
        font-weight: 600;
    }
    
    /* Icon styling */
    .icon {
        color: #60a5fa;
        font-size: 1.2em;
        margin-right: 0.5rem;
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
    href = f'<a href="data:file/csv;base64,{b64}" download="{download_filename}" class="download-btn"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:10px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>Download CSV</a>'
    return href

# Main App
def main():
    # Header with beautiful typography and icons
    st.markdown('<div class="app-header">', unsafe_allow_html=True)
    st.markdown('<h1>✨ Hidevs Internship Work ✨</h1>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Information Card
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="margin-top:0;"><span class="icon">📊</span> Event & Host Details</h3>', unsafe_allow_html=True)
    st.markdown('<p>This dataset contains information about various events hosted by <span class="highlight">Hidevs</span>.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get data
    df = extract_event_data()
    
    # Add search functionality with improved styling
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    search_term = st.text_input("🔍 Search Events", placeholder="Type to filter events...")
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="container">', unsafe_allow_html=True)
    st.markdown('<h3 style="margin-top:0;"><span class="icon">📥</span>Download Dataset</h3>', unsafe_allow_html=True)
    
    # Create formatted CSV
    csv = get_formatted_csv(df)
    
    # Display download button with custom styling
    st.markdown('<div style="display:flex; justify-content:center;">', unsafe_allow_html=True)
    st.markdown(get_download_link(csv), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="footer">© 2024 Hidevs Internship Program | Created with ❤️ by Hidevs Team</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
