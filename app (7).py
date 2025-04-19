import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

# Static event data as crawling JavaScript-rendered Luma page requires advanced tools
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

# Streamlit UI
st.title("📊 BHIVE Events & Host LinkedIn Info")

df = extract_event_data()
st.write("### Event & Host Details")
st.dataframe(df)

csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download as CSV",
    data=csv,
    file_name="bhive_event_hosts.csv",
    mime="text/csv"
)
