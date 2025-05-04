import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from datetime import datetime

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database.db_manager import DatabaseManager
from backend.scanner.scanner import MediaScanner
from backend.analyzer.analyzer import MediaAnalyzer
from backend.validators.duration_validator import DurationValidator
from backend.notification.notification_service import NotificationService
from backend.api_integration.api_service import ApiService

# Initialize database connection
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'media_db.sqlite')
db_manager = DatabaseManager(DB_PATH)

# Initialize services
api_service = ApiService(db_manager)
notification_service = NotificationService(db_manager)
scanner = MediaScanner(db_manager)
analyzer = MediaAnalyzer(db_manager)
validator = DurationValidator(db_manager)

# Set page configuration
st.set_page_config(
    page_title="Media Manager Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .stDataFrame {
        max-height: 400px;
        overflow-y: auto;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .info-card {
        background-color: #e8f4f8;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .warning-card {
        background-color: #fff3cd;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .error-card {
        background-color: #f8d7da;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px; 
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar menu
st.sidebar.title("Media Manager")
menu_options = ["Overview", "Media Library", "Issues & Problems", "Settings", "Scan Now"]
selected_menu = st.sidebar.selectbox("Navigate", menu_options)

# Helper functions
def get_media_stats():
    """Get statistics about media library"""
    total_files = db_manager.get_total_files_count()
    file_types = db_manager.get_file_types_count()
    issues_count = db_manager.get_issues_count()
    duration_issues = db_manager.get_duration_issues_count()
    storage_used = db_manager.get_total_storage_used()
    
    return {
        "total_files": total_files,
        "file_types": file_types,
        "issues_count": issues_count,
        "duration_issues": duration_issues,
        "storage_used": storage_used
    }

def format_size(size_bytes):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def run_scan():
    """Run a media scan and update the UI"""
    with st.spinner("Scanning media files..."):
        scan_results = scanner.scan()
        st.success(f"Scan completed. Found {scan_results['total_files']} files.")
        
        # Run analyzer on new files
        if scan_results['new_files']:
            with st.spinner("Analyzing new files..."):
                analyzer.analyze_files(scan_results['new_files'])
                
        # Run validator on new files
        if scan_results['new_files']:
            with st.spinner("Validating file durations..."):
                validator.validate_batch(scan_results['new_files'])
                
        # Send notification
        notification_service.send_notification(
            "Media Scan Completed",
            f"Found {len(scan_results['new_files'])} new files, {len(scan_results['modified_files'])} modified files."
        )
        
    return scan_results

# Main content based on menu selection
if selected_menu == "Overview":
    st.title("Media Library Overview")
    
    # Get statistics
    stats = get_media_stats()
    
    # Display metrics in cards using columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Media Files", stats["total_files"])
        st.markdown(f"Storage Used: {format_size(stats['storage_used'])}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("File Types", len(stats["file_types"]))
        file_types_text = ", ".join([f"{ext}" for ext, count in list(stats["file_types"].items())[:5]])
        if len(stats["file_types"]) > 5:
            file_types_text += "..."
        st.markdown(f"Types: {file_types_text}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Issues Found", stats["issues_count"])
        st.markdown(f"Duration Issues: {stats['duration_issues']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # File distribution chart
    if stats["file_types"]:
        st.subheader("File Type Distribution")
        file_types_df = pd.DataFrame(
            {"File Type": list(stats["file_types"].keys()),
             "Count": list(stats["file_types"].values())}
        )
        fig = px.pie(file_types_df, values="Count", names="File Type", hole=0.4)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("Recent Activity")
    recent_files = db_manager.get_recent_files(limit=5)
    if recent_files:
        recent_df = pd.DataFrame(recent_files)
        recent_df['added_date'] = pd.to_datetime(recent_df['added_date'])
        recent_df['added_date'] = recent_df['added_date'].dt.strftime('%Y-%m-%d %H:%M')
        recent_df['size_formatted'] = recent_df['size'].apply(format_size)
        st.dataframe(recent_df[['path', 'size_formatted', 'added_date']], hide_index=True)
    else:
        st.info("No recent file activity found.")

elif selected_menu == "Media Library":
    st.title("Media Library")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        file_types = ["All"] + list(db_manager.get_file_types_count().keys())
        selected_type = st.selectbox("File Type", file_types)
    
    with col2:
        sort_options = ["Date Added (Newest)", "Date Added (Oldest)", "Size (Largest)", "Size (Smallest)"]
        sort_by = st.selectbox("Sort By", sort_options)
        
    with col3:
        search_query = st.text_input("Search", placeholder="Enter filename or path...")
    
    # Retrieve files based on filters
    file_filter = None if selected_type == "All" else selected_type
    
    if search_query:
        files = db_manager.search_files(search_query, file_type=file_filter)
    else:
        files = db_manager.get_all_files(file_type=file_filter)
    
    # Apply sorting
    if files and len(files) > 0:
        files_df = pd.DataFrame(files)
        
        if sort_by == "Date Added (Newest)":
            files_df = files_df.sort_values(by="added_date", ascending=False)
        elif sort_by == "Date Added (Oldest)":
            files_df = files_df.sort_values(by="added_date", ascending=True)
        elif sort_by == "Size (Largest)":
            files_df = files_df.sort_values(by="size", ascending=False)
        elif sort_by == "Size (Smallest)":
            files_df = files_df.sort_values(by="size", ascending=True)
        
        # Format columns for display
        files_df['added_date'] = pd.to_datetime(files_df['added_date']).dt.strftime('%Y-%m-%d %H:%M')
        files_df['size_formatted'] = files_df['size'].apply(format_size)
        
        # Display results count
        st.write(f"Showing {len(files_df)} files")
        
        # Display files
        st.dataframe(
            files_df[['path', 'size_formatted', 'added_date', 'duration_status']],
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No files found matching your criteria.")

elif selected_menu == "Issues & Problems":
    st.title("Media Issues & Problems")
    
    # Tabs for different issue types
    tab1, tab2, tab3 = st.tabs(["Duration Issues", "Quality Issues", "Missing Metadata"])
    
    with tab1:
        st.subheader("Files with Duration Issues")
        duration_issues = db_manager.get_files_with_duration_issues()
        
        if duration_issues:
            issues_df = pd.DataFrame(duration_issues)
            issues_df['added_date'] = pd.to_datetime(issues_df['added_date']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Add color coding based on issue type
            def highlight_row(row):
                if row['duration_status'] == 'corrupted':
                    return ['background-color: #ffcccc'] * len(row)
                elif row['duration_status'] == 'too_short':
                    return ['background-color: #ffffcc'] * len(row)
                return [''] * len(row)
            
            styled_df = issues_df.style.apply(highlight_row, axis=1)
            st.dataframe(
                styled_df,
                hide_index=True,
                use_container_width=True
            )
            
            # Action buttons for fixing issues
            if st.button("Re-validate Selected Files"):
                st.warning("Re-validation functionality will be implemented soon")
                
        else:
            st.success("No duration issues found!")
    
    with tab2:
        st.subheader("Files with Quality Issues")
        # This will be implemented in future updates
        st.info("Quality analysis functionality will be available in a future update.")
    
    with tab3:
        st.subheader("Files Missing Metadata")
        # This will be implemented in future updates
        st.info("Metadata validation will be available in a future update.")

elif selected_menu == "Settings":
    st.title("Settings")
    
    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4 = st.tabs(["Scan Settings", "Validation Settings", "Notification Settings", "API Settings"])
    
    with tab1:
        st.subheader("Media Scan Settings")
        
        # Media directories
        media_dirs = db_manager.get_scan_directories()
        st.write("Configured Media Directories:")
        
        # Display current directories
        if media_dirs:
            for idx, directory in enumerate(media_dirs):
                st.code(directory['path'])
        else:
            st.info("No media directories configured")
        
        # Add new directory
        new_dir = st.text_input("Add New Directory", placeholder="/path/to/media")
        if st.button("Add Directory") and new_dir:
            if os.path.exists(new_dir):
                db_manager.add_scan_directory(new_dir)
                st.success(f"Added: {new_dir}")
                st.experimental_rerun()
            else:
                st.error("Directory does not exist!")
        
        # Scan frequency settings
        st.subheader("Scan Schedule")
        scan_freq = st.selectbox(
            "Scan Frequency",
            ["Manual Only", "Hourly", "Daily", "Weekly"]
        )
        
        if scan_freq != "Manual Only":
            st.info(f"Automatic scanning will run {scan_freq.lower()}")
            st.warning("Automatic scheduling will be available in a future update")
    
    with tab2:
        st.subheader("Validation Settings")
        
        # Duration validation settings
        st.write("Duration Validation Thresholds")
        
        col1, col2 = st.columns(2)
        with col1:
            min_video = st.number_input("Minimum Video Duration (seconds)", 
                                     min_value=1, value=60, step=1)
        with col2:
            min_audio = st.number_input("Minimum Audio Duration (seconds)",
                                     min_value=1, value=30, step=1)
        
        if st.button("Update Duration Settings"):
            validator.set_min_duration(
                video_duration_sec=min_video,
                audio_duration_sec=min_audio
            )
            st.success("Duration validation settings updated!")
            
    with tab3:
        st.subheader("Notification Settings")
        
        # Enable/disable notifications
        enable_windows = st.checkbox("Enable Windows Notifications", value=True)
        enable_discord = st.checkbox("Enable Discord Notifications", value=False)
        
        if enable_discord:
            discord_webhook = st.text_input("Discord Webhook URL", 
                                          placeholder="https://discord.com/api/webhooks/...")
            
        # Notification categories
        st.write("Choose which events trigger notifications:")
        notify_scan = st.checkbox("Scan Completions", value=True)
        notify_issues = st.checkbox("Critical Issues", value=True)
        notify_threshold = st.checkbox("Threshold Alerts", value=True)
        
        if st.button("Save Notification Settings"):
            # This would update notification settings in a future implementation
            st.success("Notification settings saved!")
            
    with tab4:
        st.subheader("API Integration Settings")
        
        # Sonarr/Radarr API settings
        st.write("Sonarr API")
        sonarr_url = st.text_input("Sonarr URL", placeholder="http://localhost:8989")
        sonarr_api = st.text_input("Sonarr API Key")
        
        st.write("Radarr API")
        radarr_url = st.text_input("Radarr URL", placeholder="http://localhost:7878")
        radarr_api = st.text_input("Radarr API Key")
        
        st.write("OMDB API")
        omdb_api = st.text_input("OMDB API Key")
        
        if st.button("Save API Settings"):
            # This would update API settings in a future implementation
            st.success("API settings saved!")

elif selected_menu == "Scan Now":
    st.title("Run Media Scan")
    
    st.write("Initiate a scan of your media directories to find new, modified, or deleted files.")
    
    scan_options = st.radio("Scan Type", ["Quick Scan", "Full Scan"])
    
    start_scan = st.button("Start Scan", type="primary")
    
    if start_scan:
        if scan_options == "Full Scan":
            scanner.force_full_scan = True
        else:
            scanner.force_full_scan = False
            
        scan_results = run_scan()
        
        # Show scan results
        st.subheader("Scan Results")
        st.write(f"Total Files Processed: {scan_results['total_files']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("New Files", len(scan_results['new_files']))
        with col2:
            st.metric("Modified Files", len(scan_results['modified_files']))
        with col3:
            st.metric("Deleted Files", len(scan_results['deleted_files']))
            
        # Show lists of affected files
        if scan_results['new_files']:
            with st.expander("New Files"):
                for file in scan_results['new_files'][:20]:  # Limit to 20 for display
                    st.text(file)
                if len(scan_results['new_files']) > 20:
                    st.text(f"... and {len(scan_results['new_files']) - 20} more")
                    
        if scan_results['modified_files']:
            with st.expander("Modified Files"):
                for file in scan_results['modified_files'][:20]:
                    st.text(file)
                if len(scan_results['modified_files']) > 20:
                    st.text(f"... and {len(scan_results['modified_files']) - 20} more")
                    
        if scan_results['deleted_files']:
            with st.expander("Deleted Files"):
                for file in scan_results['deleted_files'][:20]:
                    st.text(file)
                if len(scan_results['deleted_files']) > 20:
                    st.text(f"... and {len(scan_results['deleted_files']) - 20} more")

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: gray; font-size: 0.8em;'>"
    f"Media Manager Dashboard • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", 
    unsafe_allow_html=True
)
