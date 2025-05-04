import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
from pathlib import Path
from pymediainfo import MediaInfo
import json

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.database.db_manager import DatabaseManager
from backend.validators.duration_validator import DurationValidator

# Initialize database connection
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'media_db.sqlite')
db_manager = DatabaseManager(DB_PATH)
validator = DurationValidator(db_manager)

# Set page configuration
st.set_page_config(
    page_title="File Details - Media Manager",
    page_icon="🎬",
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
    .detail-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .status-valid {
        color: green;
        font-weight: bold;
    }
    .status-warning {
        color: orange;
        font-weight: bold;
    }
    .status-error {
        color: red;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper functions
def format_size(size_bytes):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def format_duration(seconds):
    """Format seconds to HH:MM:SS"""
    if seconds is None:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def get_status_class(status):
    """Return CSS class based on status"""
    if status == "valid":
        return "status-valid"
    elif status in ["too_short", "unknown"]:
        return "status-warning"
    elif status == "corrupted":
        return "status-error"
    return ""

# Get file ID from URL query parameter
query_params = st.experimental_get_query_params()
file_id = query_params.get("id", [None])[0]

if not file_id:
    st.error("No file ID provided. Please select a file from the media library.")
    st.stop()

# Fetch file details from database
file_details = db_manager.get_file_by_id(file_id)

if not file_details:
    st.error(f"File with ID {file_id} not found in the database.")
    st.stop()

# Display file details
st.title("File Details")

# Back button
if st.button("← Back to Media Library"):
    st.experimental_set_query_params()
    st.experimental_rerun()

# File path and basic info
st.markdown(f"<div class='detail-card'>", unsafe_allow_html=True)
st.subheader(Path(file_details['path']).name)
st.markdown(f"**Path:** {file_details['path']}")

# Display file status with appropriate styling
status = file_details.get('duration_status', 'unknown')
st.markdown(
    f"**Status:** <span class='{get_status_class(status)}'>{status.replace('_', ' ').title()}</span>", 
    unsafe_allow_html=True
)

# Basic file info
col1, col2, col3 = st.columns(3)

with col1:
    size = file_details.get('size', 0)
    st.metric("File Size", format_size(size))
    
with col2:
    duration = file_details.get('duration', 0)
    st.metric("Duration", format_duration(duration))
    
with col3:
    added_date = file_details.get('added_date', 'Unknown')
    st.metric("Added", added_date.split()[0] if added_date else "Unknown")

st.markdown("</div>", unsafe_allow_html=True)

# Media information
st.markdown("<div class='detail-card'>", unsafe_allow_html=True)
st.subheader("Media Information")

# Try to get media info
file_path = file_details['path']
if os.path.exists(file_path):
    try:
        media_info = MediaInfo.parse(file_path)
        
        # Create tabs for different track types
        track_types = []
        for track in media_info.tracks:
            if track.track_type not in track_types:
                track_types.append(track.track_type)
        
        if track_types:
            tabs = st.tabs(track_types)
            
            for i, track_type in enumerate(track_types):
                with tabs[i]:
                    for track in media_info.tracks:
                        if track.track_type == track_type:
                            # Convert track to dict and display relevant info
                            track_dict = track.to_data()
                            
                            # Filter out most relevant properties based on track type
                            if track_type == "General":
                                relevant_props = {
                                    "format": "Format",
                                    "file_size": "File Size",
                                    "duration": "Duration",
                                    "overall_bit_rate": "Bit Rate",
                                    "encoded_date": "Encoded Date",
                                    "writing_application": "Writing Application",
                                    "writing_library": "Writing Library"
                                }
                            elif track_type == "Video":
                                relevant_props = {
                                    "format": "Format",
                                    "width": "Width",
                                    "height": "Height",
                                    "frame_rate": "Frame Rate",
                                    "bit_depth": "Bit Depth",
                                    "codec_id": "Codec ID",
                                    "bit_rate": "Bit Rate",
                                    "duration": "Duration"
                                }
                            elif track_type == "Audio":
                                relevant_props = {
                                    "format": "Format",
                                    "channel_s": "Channels",
                                    "sampling_rate": "Sampling Rate",
                                    "bit_depth": "Bit Depth",
                                    "bit_rate": "Bit Rate",
                                    "duration": "Duration",
                                    "language": "Language"
                                }
                            elif track_type == "Text":
                                relevant_props = {
                                    "format": "Format",
                                    "language": "Language",
                                    "title": "Title",
                                    "default": "Default",
                                    "forced": "Forced"
                                }
                            else:
                                relevant_props = {}
                            
                            # Create a filtered dictionary of relevant properties
                            display_info = {}
                            for prop, label in relevant_props.items():
                                if prop in track_dict:
                                    display_info[label] = track_dict[prop]
                            
                            # Display as a table
                            if display_info:
                                st.table(pd.DataFrame(list(display_info.items()), 
                                                     columns=["Property", "Value"]))
                            else:
                                st.info(f"No detailed information available for {track_type} track.")
        else:
            st.warning("No media tracks found.")
    except Exception as e:
        st.error(f"Error parsing media info: {str(e)}")
else:
    st.warning("File not found on disk. Information may be outdated.")

st.markdown("</div>", unsafe_allow_html=True)

# Actions
st.markdown("<div class='detail-card'>", unsafe_allow_html=True)
st.subheader("Actions")

col1, col2 = st.columns(2)

with col1:
    if st.button("Re-validate File"):
        with st.spinner("Validating file..."):
            result, duration = validator.validate_file_duration(file_path)
            file_info = {
                'duration': duration,
                'duration_status': result.value
            }
            db_manager.update_file_info(file_path, file_info)
            st.success(f"File re-validated. Status: {result.value}")
            st.experimental_rerun()

with col2:
    if st.button("Delete from Database"):
        if st.checkbox("I understand this will only remove the file from the database, not from disk"):
            db_manager.delete_file(file_id)
            st.success("File removed from database")
            st.experimental_set_query_params()
            st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Raw JSON data (expandable)
with st.expander("Raw Database Entry"):
    st.json(file_details)
