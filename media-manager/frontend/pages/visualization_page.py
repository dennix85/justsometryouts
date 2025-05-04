import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.database.db_manager import DatabaseManager

# Initialize database connection
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'media_db.sqlite')
db_manager = DatabaseManager(DB_PATH)

# Set page configuration
st.set_page_config(
    page_title="Media Statistics - Media Manager",
    page_icon="📊",
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
    .chart-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
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
    if seconds is None or seconds <= 0:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

# Title
st.title("Media Library Statistics & Visualizations")

# Get data for visualizations
all_files = db_manager.get_all_files()
if not all_files:
    st.warning("No media files found in the database. Run a scan to collect data.")
    st.stop()

# Convert to DataFrame for easier manipulation
df = pd.DataFrame(all_files)

# Preprocess data
if 'added_date' in df.columns:
    df['added_date'] = pd.to_datetime(df['added_date'])
    df['date'] = df['added_date'].dt.date

if 'path' in df.columns:
    # Extract file extension
    df['extension'] = df['path'].apply(lambda x: os.path.splitext(x)[1].lower().replace('.', '') if isinstance(x, str) else 'unknown')
    
    # Extract directory
    df['directory'] = df['path'].apply(lambda x: os.path.dirname(x) if isinstance(x, str) else 'unknown')
    df['directory'] = df['directory'].apply(lambda x: os.path.basename(x))

# Main tabs
tab1, tab2, tab3 = st.tabs(["File Statistics", "Storage Analysis", "Time Analysis"])

with tab1:
    st.header("File Statistics")
    
    # File types chart
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("File Type Distribution")
    
    if 'extension' in df.columns:
        file_types = df['extension'].value_counts().reset_index()
        file_types.columns = ['File Type', 'Count']
        
        fig = px.pie(
            file_types,
            values='Count',
            names='File Type',
            title='File Types Distribution',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("File type information not available")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Duration distribution
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Duration Distribution")
    
    if 'duration' in df.columns:
        # Filter out invalid durations
        duration_df = df[df['duration'] > 0]
        
        if not duration_df.empty:
            # Create duration ranges
            duration_bins = [0, 60, 300, 600, 1800, 3600, 7200, float('inf')]
            duration_labels = ['<1m', '1-5m', '5-10m', '10-30m', '30m-1h', '1-2h', '>2h']
            
            duration_df['duration_range'] = pd.cut(
                duration_df['duration'],
                bins=duration_bins,
                labels=duration_labels,
                right=False
            )
            
            duration_counts = duration_df['duration_range'].value_counts().reset_index()
            duration_counts.columns = ['Duration Range', 'Count']
            duration_counts = duration_counts.sort_values('Duration Range')
            
            fig = px.bar(
                duration_counts,
                x='Duration Range',
                y='Count',
                title='Media Duration Distribution',
                color='Count',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No valid duration data available")
    else:
        st.warning("Duration information not available")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Issues breakdown
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Media Issues Breakdown")
    
    if 'duration_status' in df.columns:
        status_counts = df['duration_status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        # Map status names to more readable versions
        status_map = {
            'valid': 'Valid',
            'too_short': 'Too Short',
            'corrupted': 'Corrupted',
            'unknown': 'Unknown'
        }
        
        status_counts['Status'] = status_counts['Status'].map(lambda x: status_map.get(x, x))
        
        fig = px.bar(
            status_counts,
            x='Status',
            y='Count',
            title='Media File Status',
            color='Status',
            color_discrete_map={
                'Valid': 'green',
                'Too Short': 'orange',
                'Corrupted': 'red',
                'Unknown': 'gray'
            }
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Status information not available")
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.header("Storage Analysis")
    
    # Storage by file type
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Storage by File Type")
    
    if 'extension' in df.columns and 'size' in df.columns:
        # Group by file type and calculate total size
        storage_by_type = df.groupby('extension')['size'].sum().reset_index()
        storage_by_type.columns = ['File Type', 'Total Size (bytes)']
        
        # Add human-readable size
        storage_by_type['Size Formatted'] = storage_by_type['Total Size (bytes)'].apply(format_size)
        
        # Sort by size
        storage_by_type = storage_by_type.sort_values('Total Size (bytes)', ascending=False)
        
        # Create treemap
        fig = px.treemap(
            storage_by_type,
            path=['File Type'],
            values='Total Size (bytes)',
            title='Storage Usage by File Type',
            hover_data=['Size Formatted'],
            color='Total Size (bytes)',
            color_continuous_scale=px.colors.sequential.Blues
        )
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Also show as a table
        st.subheader("Storage by File Type (Table)")
        st.dataframe(
            storage_by_type[['File Type', 'Size Formatted']],
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("File type or size information not available")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Storage by directory
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Storage by Directory")
    
    if 'directory' in df.columns and 'size' in df.columns:
        # Group by directory and calculate total size
        storage_by_dir = df.groupby('directory')['size'].sum().reset_index()
        storage_by_dir.columns = ['Directory', 'Total Size (bytes)']
        
        # Add human-readable size
        storage_by_dir['Size Formatted'] = storage_by_dir['Total Size (bytes)'].apply(format_size)
        
        # Sort by size
        storage_by_dir = storage_by_dir.sort_values('Total Size (bytes)', ascending=False)
        
        # Create bar chart
        fig = px.bar(
            storage_by_dir.head(15),  # Top 15 directories
            x='Directory',
            y='Total Size (bytes)',
            title='Top 15 Directories by Storage Usage',
            color='Total Size (bytes)',
            text='Size Formatted',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        fig.update_traces(textposition='outside')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Directory or size information not available")
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.header("Time Analysis")
    
    # Files added over time
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Files Added Over Time")
    
    if 'added_date' in df.columns:
        # Group by date
        files_by_date = df.groupby(df['added_date'].dt.date).size().reset_index()
        files_by_date.columns = ['Date', 'Files Added']
        
        # Ensure all dates are included
        if len(files_by_date) > 1:
            date_range = pd.date_range(files_by_date['Date'].min(), files_by_date['Date'].max(), freq='D')
            date_df = pd.DataFrame({'Date': date_range})
            date_df['Date'] = date_df['Date'].dt.date
            files_by_date = pd.merge(date_df, files_by_date, on='Date', how='left')
            files_by_date['Files Added'] = files_by_date['Files Added'].fillna(0)
        
        # Create line chart
        fig = px.line(
            files_by_date,
            x='Date',
            y='Files Added',
            title='Files Added Over Time',
            markers=True
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Also show cumulative
        files_by_date['Cumulative Files'] = files_by_date['Files Added'].cumsum()
        
        fig2 = px.line(
            files_by_date,
            x='Date',
            y='Cumulative Files',
            title='Total Media Files Over Time',
            line_shape='hv'
        )
        
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Date information not available")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Storage growth over time
    if 'added_date' in df.columns and 'size' in df.columns:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("Storage Growth Over Time")
        
        # Group by date and calculate size
        storage_by_date = df.groupby(df['added_date'].dt.date)['size'].sum().reset_index()
        storage_by_date.columns = ['Date', 'Storage Added (bytes)']
        
        # Ensure all dates are included
        if len(storage_by_date) > 1:
            date_range = pd.date_range(storage_by_date['Date'].min(), storage_by_date['Date'].max(), freq='D')
            date_df = pd.DataFrame({'Date': date_range})
            date_df['Date'] = date_df['Date'].dt.date
            storage_by_date = pd.merge(date_df, storage_by_date, on='Date', how='left')
            storage_by_date['Storage Added (bytes)'] = storage_by_date['Storage Added (bytes)'].fillna(0)
        
        # Calculate cumulative storage
        storage_by_date['Cumulative Storage (bytes)'] = storage_by_date['Storage Added (bytes)'].cumsum()
        
        # Add human-readable sizes
        storage_by_date['Cumulative Storage'] = storage_by_date['Cumulative Storage (bytes)'].apply(format_size)
        
        # Create area chart
        fig = px.area(
            storage_by_date,
            x='Date',
            y='Cumulative Storage (bytes)',
            title='Total Storage Used Over Time',
            hover_data=['Cumulative Storage']
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: gray; font-size: 0.8em;'>"
    f"Media Manager Dashboard • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", 
    unsafe_allow_html=True
)
