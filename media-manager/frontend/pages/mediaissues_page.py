import streamlit as st
import os
import sys
import pandas as pd
import plotly.express as px
from datetime import datetime

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.database.db_manager import DatabaseManager
from backend.notification.notification_service import NotificationService

# Initialize database connection
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'media_db.sqlite')
db_manager = DatabaseManager(DB_PATH)
notification_service = NotificationService(db_manager)

# Set page configuration
st.set_page_config(
    page_title="Media Issues - Media Manager",
    page_icon="⚠️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stApp header {
        background-color: #2c3e50;
    }
    .issues-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .issue-high {
        color: #e74c3c;
        font-weight: bold;
    }
    .issue-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .issue-low {
        color: #3498db;
        font-weight: bold;
    }
    .issue-resolved {
        color: #2ecc71;
        font-weight: bold;
    }
    .fix-button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 5px 10px;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("Media Issues Tracker")
st.write("Track and resolve issues with your media files.")

# Summary metrics
st.markdown("<div class='issues-card'>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

# These would be actual database queries in the real implementation
with col1:
    st.metric("Total Issues", "32")

with col2:
    st.metric("Critical Issues", "5", delta="2 new")

with col3:
    st.metric("Issues Resolved", "18")

with col4:
    st.metric("Resolution Rate", "56%")

st.markdown("</div>", unsafe_allow_html=True)

# Issues by type chart
st.markdown("<div class='issues-card'>", unsafe_allow_html=True)
st.subheader("Issues by Type")

# Sample data - would be real data in production
issue_types = {
    "Issue Type": ["Corrupt File", "Duration Mismatch", "Codec Issues", "Missing Metadata", "Audio Problems", "Other"],
    "Count": [7, 12, 5, 4, 3, 1]
}

issue_types_df = pd.DataFrame(issue_types)

fig = px.bar(
    issue_types_df, 
    x="Issue Type", 
    y="Count",
    color="Issue Type",
    color_discrete_sequence=px.colors.qualitative.Set3,
    height=400
)

fig.update_layout(
    xaxis_title="",
    yaxis_title="Number of Issues",
    showlegend=False,
    margin=dict(l=20, r=20, t=30, b=20)
)

st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Issues list and filters
st.markdown("<div class='issues-card'>", unsafe_allow_html=True)
st.subheader("Issues List")

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    issue_severity = st.multiselect(
        "Severity",
        options=["High", "Medium", "Low"],
        default=["High", "Medium", "Low"]
    )

with col2:
    issue_status = st.multiselect(
        "Status",
        options=["Open", "In Progress", "Resolved"],
        default=["Open", "In Progress"]
    )

with col3:
    issue_type_filter = st.multiselect(
        "Issue Type",
        options=["Corrupt File", "Duration Mismatch", "Codec Issues", "Missing Metadata", "Audio Problems", "Other"],
        default=[]
    )

# Search
search_query = st.text_input("Search by filename or path", placeholder="Search...")

# Sample issues data - would be from database in production
issues_data = {
    "ID": list(range(1, 11)),
    "Filepath": [
        "E:\\Movies\\The Avengers (2012)\\movie.mkv",
        "D:\\TV Shows\\Breaking Bad\\Season 1\\episode01.mp4",
        "E:\\Movies\\Inception (2010)\\inception.avi",
        "D:\\TV Shows\\Game of Thrones\\Season 8\\episode03.mkv",
        "E:\\Movies\\The Dark Knight (2008)\\dark_knight.mp4",
        "D:\\TV Shows\\Stranger Things\\Season 2\\episode05.mkv",
        "E:\\Movies\\Interstellar (2014)\\interstellar.mp4",
        "D:\\TV Shows\\The Office\\Season 4\\episode12.mkv",
        "E:\\Movies\\The Matrix (1999)\\matrix.avi",
        "D:\\TV Shows\\Friends\\Season 6\\episode15.mp4"
    ],
    "Issue Type": [
        "Corrupt File",
        "Duration Mismatch",
        "Codec Issues",
        "Missing Metadata",
        "Audio Problems",
        "Duration Mismatch",
        "Corrupt File",
        "Codec Issues",
        "Duration Mismatch",
        "Missing Metadata"
    ],
    "Details": [
        "File is corrupt or incomplete. Missing 45MB at end of file.",
        "Expected: 01:00:45, Actual: 00:42:12. Missing end of episode.",
        "Codec xvd9 not supported by most players. Consider re-encoding.",
        "Missing director, runtime and genre metadata.",
        "Audio track 2 (5.1) has sync issues. 1.2s delay.",
        "Expected: 00:51:30, Actual: 00:50:15. Missing scene detected.",
        "File header corrupted. May cause playback issues.",
        "Codec not optimized for streaming. High bitrate variant.",
        "Expected: 02:16:00, Actual: 01:58:23. Missing content.",
        "Cover art missing. IMDB ID incorrect."
    ],
    "Severity": [
        "High",
        "High",
        "Medium",
        "Low",
        "Medium",
        "Medium",
        "High",
        "Low",
        "Medium",
        "Low"
    ],
    "Status": [
        "Open",
        "In Progress",
        "Open",
        "Resolved",
        "Open",
        "In Progress",
        "Open",
        "Resolved",
        "Open",
        "In Progress"
    ],
    "Detected": [
        "2025-05-01",
        "2025-05-01",
        "2025-04-30",
        "2025-04-29",
        "2025-04-29",
        "2025-04-28",
        "2025-04-28",
        "2025-04-27",
        "2025-04-26",
        "2025-04-25"
    ]
}

issues_df = pd.DataFrame(issues_data)

# Apply filters
filtered_df = issues_df.copy()

if issue_severity:
    filtered_df = filtered_df[filtered_df["Severity"].isin(issue_severity)]

if issue_status:
    filtered_df = filtered_df[filtered_df["Status"].isin(issue_status)]

if issue_type_filter:
    filtered_df = filtered_df[filtered_df["Issue Type"].isin(issue_type_filter)]

if search_query:
    filtered_df = filtered_df[filtered_df["Filepath"].str.contains(search_query, case=False)]

# Apply styling based on severity and status
def style_issues(df):
    # Create a styler object
    styler = df.style
    
    # Apply style to severity
    def severity_style(val):
        if val == "High":
            return 'background-color: #ffcccc'
        elif val == "Medium":
            return 'background-color: #fff2cc'
        elif val == "Low":
            return 'background-color: #e6f2ff'
        return ''
    
    # Apply style to status
    def status_style(val):
        if val == "Resolved":
            return 'background-color: #d5f5e3'
        elif val == "In Progress":
            return 'background-color: #e8f8f5'
        return ''
    
    # Apply styles to the DataFrame
    styler = styler.applymap(severity_style, subset=['Severity'])
    styler = styler.applymap(status_style, subset=['Status'])
    
    return styler

# Display the styled dataframe
styled_df = style_issues(filtered_df)
st.dataframe(styled_df, use_container_width=True)

# Actions section
if not filtered_df.empty:
    st.subheader("Bulk Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Reanalyze Selected Files", use_container_width=True):
            st.info("Reanalysis would be triggered here")
    
    with col2:
        if st.button("Mark as Resolved", use_container_width=True):
            st.success("Selected issues would be marked as resolved")
    
    with col3:
        if st.button("Generate Issue Report", use_container_width=True):
            st.download_button(
                label="Download Report",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name=f"media_issues_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

st.markdown("</div>", unsafe_allow_html=True)

# Issue Distribution by Location
st.markdown("<div class='issues-card'>", unsafe_allow_html=True)
st.subheader("Issue Distribution by Location")

# Extract drive letters and folder paths for visualization
issues_df['Drive'] = issues_df['Filepath'].str.split(':').str[0]
issues_df['Main Folder'] = issues_df['Filepath'].apply(lambda x: x.split('\\')[1] if '\\' in x else 'Unknown')

# Create two charts side by side
col1, col2 = st.columns(2)

with col1:
    # Issues by drive
    drive_counts = issues_df.groupby('Drive').size().reset_index(name='Count')
    
    fig1 = px.pie(
        drive_counts, 
        values='Count', 
        names='Drive',
        title='Issues by Drive',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig1.update_traces(textposition='inside', textinfo='percent+label')
    fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Issues by main folder
    folder_counts = issues_df.groupby('Main Folder').size().reset_index(name='Count')
    
    fig2 = px.pie(
        folder_counts, 
        values='Count', 
        names='Main Folder',
        title='Issues by Main Folder',
        color_discrete_sequence=px.colors.qualitative.Light24
    )
    
    fig2.update_traces(textposition='inside', textinfo='percent+label')
    fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Issue Resolution Suggestions
st.markdown("<div class='issues-card'>", unsafe_allow_html=True)
st.subheader("Common Issue Resolutions")

# Create expandable sections for each issue type
with st.expander("How to Fix Corrupt Files"):
    st.markdown("""
    ### Corrupt File Resolution Steps
    
    1. **Try playing the file with VLC** to confirm if it's truly corrupted
    2. **Check file integrity** with a tool like MediaInfo
    3. **Attempt to repair** with ffmpeg:
    ```
    ffmpeg -i input.mp4 -c copy repaired_output.mp4
    ```
    4. **For MKV files**, try MKVToolNix repair options
    5. **As a last resort**, re-download or re-encode the file
    """)

with st.expander("How to Fix Duration Mismatches"):
    st.markdown("""
    ### Duration Mismatch Resolution Steps
    
    1. **Verify the expected duration** against a trusted source
    2. **Check if the file was properly downloaded** and is complete
    3. **Look for alternate versions** of the same content
    4. **For TV episodes**, check if there are extended or shortened cuts
    5. **Re-download from a trusted source** if necessary
    """)

with st.expander("How to Fix Codec Issues"):
    st.markdown("""
    ### Codec Issues Resolution Steps
    
    1. **Install K-Lite Codec Pack** or VLC media player for wider codec support
    2. **Trans-code the file** to a more compatible format:
    ```
    ffmpeg -i input.file -c:v libx264 -c:a aac output.mp4
    ```
    3. **For streaming issues**, consider using a lower bitrate or more compatible codec
    4. **Check hardware compatibility** for specialized formats like HEVC/H.265
    """)

with st.expander("How to Fix Missing Metadata"):
    st.markdown("""
    ### Missing Metadata Resolution Steps
    
    1. **Use a media scraper** like Tiny Media Manager
    2. **Manually add metadata** with a tool like MP4Box or MKVToolNix
    3. **Look up correct metadata** on TMDB, IMDB, or TheTVDB
    4. **For file naming conventions**, consider using FileBot to standardize names
    """)

st.markdown("</div>", unsafe_allow_html=True)
