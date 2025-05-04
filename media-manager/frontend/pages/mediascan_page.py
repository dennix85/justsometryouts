import streamlit as st
import os
import sys
import time
import pandas as pd
from datetime import datetime

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.scanner.scanner import MediaScanner
from backend.analyzer.analyzer import MediaAnalyzer
from backend.database.db_manager import DatabaseManager
from backend.notification.notification_service import NotificationService

# Initialize components
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'media_db.sqlite')
db_manager = DatabaseManager(DB_PATH)
notification_service = NotificationService(db_manager)
media_scanner = MediaScanner(db_manager)
media_analyzer = MediaAnalyzer(db_manager)

# Set page configuration
st.set_page_config(
    page_title="Media Scan - Media Manager",
    page_icon="🔍",
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
    .scan-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .file-count {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2980b9;
    }
    .issue-count {
        font-size: 1.2rem;
        font-weight: bold;
        color: #e74c3c;
    }
    .scan-summary {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("Media Library Scanner")
st.write("Scan your media files to detect issues and analyze content.")

# Scan Configuration
st.markdown("<div class='scan-card'>", unsafe_allow_html=True)
st.subheader("Scan Configuration")

col1, col2 = st.columns(2)

with col1:
    scan_paths = st.text_area(
        "Media Directories to Scan",
        help="Enter one path per line",
        placeholder="E:\\Movies\nD:\\TV Shows",
        height=100
    )
    
    scan_type = st.radio(
        "Scan Type",
        options=["Full Scan", "Quick Scan (New Files Only)", "Verification Scan (Check Existing)"],
        index=1,
        horizontal=True
    )

with col2:
    file_types = st.multiselect(
        "File Types to Include",
        options=["mp4", "mkv", "avi", "mov", "wmv", "m4v", "mpg", "mpeg", "flv", "webm"],
        default=["mp4", "mkv", "avi"]
    )
    
    analyze_videos = st.checkbox(
        "Analyze Video Properties",
        value=True,
        help="Extract resolution, codec, and other technical details"
    )
    
    check_duration = st.checkbox(
        "Validate Video Duration",
        value=True,
        help="Check if video duration matches expected length"
    )

st.markdown("</div>", unsafe_allow_html=True)

# Advanced Options
with st.expander("Advanced Options"):
    col1, col2 = st.columns(2)
    
    with col1:
        max_threads = st.slider(
            "Max Threads",
            min_value=1,
            max_value=16,
            value=4,
            help="Number of parallel processes for scanning"
        )
        
        exclude_patterns = st.text_input(
            "Exclude Patterns",
            placeholder="sample,trailer",
            help="Comma-separated list of patterns to exclude"
        )
    
    with col2:
        api_lookup = st.checkbox(
            "Enable API Lookup",
            value=True,
            help="Look up additional metadata from online sources"
        )
        
        notify_on_complete = st.checkbox(
            "Notify on Completion",
            value=True,
            help="Send notification when scan completes"
        )

# Scan Controls
st.markdown("<div class='scan-card'>", unsafe_allow_html=True)
scan_col1, scan_col2 = st.columns([3, 1])

with scan_col1:
    start_scan = st.button("Start Scan", type="primary", use_container_width=True)

with scan_col2:
    cancel_scan = st.button("Cancel", type="secondary", use_container_width=True)

# Simulate scan progress
if start_scan:
    # This would normally call your actual scanning logic
    if not scan_paths:
        st.error("Please enter at least one directory to scan")
    else:
        paths_list = [path.strip() for path in scan_paths.split('\n') if path.strip()]
        
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # This is a placeholder for the actual scanning process
        # In a real implementation, you would call your scanner and analyzer here
        total_steps = 100
        scan_results = {"files_found": 0, "files_analyzed": 0, "issues_found": 0}
        
        for i in range(total_steps):
            # Update progress bar
            progress_bar.progress((i + 1) / total_steps)
            
            # Simulate finding files
            if i < 30:
                scan_results["files_found"] += 2
                status_text.text(f"Finding files... {scan_results['files_found']} found")
            # Simulate analyzing files
            elif i < 90:
                scan_results["files_analyzed"] += 1
                if i % 10 == 0:
                    scan_results["issues_found"] += 1
                status_text.text(f"Analyzing files... {scan_results['files_analyzed']}/{scan_results['files_found']} processed")
            # Simulate finalizing
            else:
                status_text.text("Finalizing results...")
            
            time.sleep(0.05)  # Simulate work being done
        
        # Scan completed
        status_text.text("Scan completed!")
        
        # Show scan summary
        st.markdown("<div class='scan-summary'>", unsafe_allow_html=True)
        st.subheader("Scan Summary")
        
        sum_col1, sum_col2, sum_col3 = st.columns(3)
        
        with sum_col1:
            st.metric("Files Scanned", scan_results["files_found"])
        
        with sum_col2:
            st.metric("Files Analyzed", scan_results["files_analyzed"])
        
        with sum_col3:
            st.metric("Issues Found", scan_results["issues_found"])
        
        # If issues were found, show them in a table
        if scan_results["issues_found"] > 0:
            st.subheader("Issues Detected")
            
            # Sample issue data - would be real data in production
            issues_data = {
                "Filepath": [
                    "E:\\Movies\\Example Movie (2023)\\movie.mkv",
                    "D:\\TV Shows\\Example Show\\Season 1\\episode01.mp4",
                    "E:\\Movies\\Another Movie\\video.avi"
                ],
                "Issue Type": [
                    "Duration Mismatch",
                    "Codec Unsupported",
                    "Corrupt File"
                ],
                "Details": [
                    "Expected: 01:32:45, Actual: 00:45:12",
                    "Codec xvd9 not supported by most players",
                    "File is corrupt or incomplete"
                ],
                "Severity": [
                    "Medium",
                    "Low",
                    "High"
                ]
            }
            
            issues_df = pd.DataFrame(issues_data)
            
            # Apply color styling based on severity
            def color_severity(val):
                if val == "High":
                    return 'background-color: #ffcccc'
                elif val == "Medium":
                    return 'background-color: #fff2cc'
                elif val == "Low":
                    return 'background-color: #e6f2ff'
                return ''
            
            st.dataframe(
                issues_df.style.applymap(color_severity, subset=['Severity']),
                use_container_width=True
            )
            
            # Option to export issues
            st.download_button(
                label="Export Issues to CSV",
                data=issues_df.to_csv(index=False).encode('utf-8'),
                file_name=f"media_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Show notification if enabled
        if notify_on_complete:
            try:
                notification_service.send_windows_notification(
                    "Media Scan Complete",
                    f"Scanned {scan_results['files_found']} files, found {scan_results['issues_found']} issues."
                )
                st.success("Notification sent!")
            except Exception as e:
                st.warning(f"Could not send notification: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Recent Scans
st.markdown("<div class='scan-card'>", unsafe_allow_html=True)
st.subheader("Recent Scans")

# This would be loaded from your database in a real implementation
recent_scans = [
    {"id": 1, "timestamp": "2025-05-01 15:32:45", "files_scanned": 1245, "issues": 12, "status": "Completed"},
    {"id": 2, "timestamp": "2025-04-28 10:15:22", "files_scanned": 954, "issues": 5, "status": "Completed"},
    {"id": 3, "timestamp": "2025-04-25 22:08:03", "files_scanned": 843, "issues": 0, "status": "Completed"}
]

recent_scans_df = pd.DataFrame(recent_scans)
st.dataframe(recent_scans_df, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
