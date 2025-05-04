import streamlit as st
import os
import sys
import json
from pathlib import Path

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.notification.notification_service import NotificationService
from backend.database.db_manager import DatabaseManager

# Initialize database connection
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'media_db.sqlite')
db_manager = DatabaseManager(DB_PATH)

# Config file path
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
NOTIFICATION_CONFIG_PATH = os.path.join(CONFIG_DIR, 'notification_config.json')

# Set page configuration
st.set_page_config(
    page_title="Notification Settings - Media Manager",
    page_icon="🔔",
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
    .settings-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .status-enabled {
        color: green;
        font-weight: bold;
    }
    .status-disabled {
        color: gray;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper functions
def load_notification_config():
    """Load notification configuration from file"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        
    if os.path.exists(NOTIFICATION_CONFIG_PATH):
        try:
            with open(NOTIFICATION_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading notification config: {str(e)}")
            return get_default_config()
    else:
        return get_default_config()

def save_notification_config(config):
    """Save notification configuration to file"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        
    try:
        with open(NOTIFICATION_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving notification config: {str(e)}")
        return False

def get_default_config():
    """Return default notification configuration"""
    return {
        "windows": {
            "enabled": True,
            "timeout": 5
        },
        "discord": {
            "enabled": False,
            "webhook_url": "",
            "username": "Media Manager"
        },
        "events": {
            "scan_complete": True,
            "critical_issues": True,
            "threshold_alerts": True,
            "system_status": False
        },
        "quiet_hours": {
            "enabled": False,
            "start_time": "22:00",
            "end_time": "08:00"
        }
    }

def test_notification(service_type):
    """Test notification service"""
    notification_service = NotificationService(db_manager)
    
    if service_type == "windows":
        notification_service.send_windows_notification(
            "Test Notification",
            "This is a test notification from Media Manager.",
            timeout=5
        )
        return True
    elif service_type == "discord":
        discord_webhook = config["discord"]["webhook_url"]
        if not discord_webhook:
            st.error("Discord webhook URL is not configured.")
            return False
            
        notification_service.send_discord_notification(
            "Test Notification",
            "This is a test notification from Media Manager.",
            webhook_url=discord_webhook,
            username=config["discord"]["username"]
        )
        return True
    
    return False

# Load current config
config = load_notification_config()

# Title
st.title("Notification Settings")
st.write("Configure how and when you receive notifications about your media library.")

# Windows notifications settings
st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
st.subheader("Windows Notifications")

windows_enabled = st.checkbox(
    "Enable Windows Notifications", 
    value=config["windows"]["enabled"],
    help="Show desktop notifications in Windows"
)

if windows_enabled:
    win_timeout = st.slider(
        "Notification Timeout (seconds)",
        min_value=1,
        max_value=60,
        value=config["windows"]["timeout"],
        help="How long notifications stay visible"
    )
    
    if st.button("Test Windows Notification"):
        if test_notification("windows"):
            st.success("Test notification sent!")
        else:
            st.error("Failed to send test notification")
else:
    win_timeout = config["windows"]["timeout"]

# Update config
config["windows"]["enabled"] = windows_enabled
config["windows"]["timeout"] = win_timeout

st.markdown("</div>", unsafe_allow_html=True)

# Discord notifications settings
st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
st.subheader("Discord Notifications")

discord_enabled = st.checkbox(
    "Enable Discord Notifications", 
    value=config["discord"]["enabled"],
    help="Send notifications to a Discord channel via webhook"
)

if discord_enabled:
    discord_webhook = st.text_input(
        "Discord Webhook URL",
        value=config["discord"]["webhook_url"],
        placeholder="https://discord.com/api/webhooks/...",
        help="Create a webhook URL in your Discord server settings"
    )
    
    discord_username = st.text_input(
        "Discord Bot Username",
        value=config["discord"]["username"],
        help="Name that will appear for webhook messages"
    )
    
    if st.button("Test Discord Notification"):
        if discord_webhook:
            if test_notification("discord"):
                st.success("Test notification sent to Discord!")
            else:
                st.error("Failed to send Discord notification")
        else:
            st.error("Please enter a webhook URL first")
else:
    discord_webhook = config["discord"]["webhook_url"]
    discord_username = config["discord"]["username"]

# Update config
config["discord"]["enabled"] = discord_enabled
config["discord"]["webhook_url"] = discord_webhook
config["discord"]["username"] = discord_username

st.markdown("</div>", unsafe_allow_html=True)

# Notification events settings
st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
st.subheader("Notification Events")
st.write("Choose which events trigger notifications:")

col1, col2 = st.columns(2)

with col1:
    scan_complete = st.checkbox(
        "Scan Completions",
        value=config["events"]["scan_complete"],
        help="Notify when media scans complete"
    )
    
    critical_issues = st.checkbox(
        "Critical Issues",
        value=config["events"]["critical_issues"],
        help="Notify about corrupted files and other critical problems"
    )

with col2:
    threshold_alerts = st.checkbox(
        "Threshold Alerts",
        value=config["events"]["threshold_alerts"],
        help="Notify when storage space is running low"
    )
    
    system_status = st.checkbox(
        "System Status",
        value=config["events"]["system_status"],
        help="Notify about application start/stop and system events"
    )

# Update config
config["events"]["scan_complete"] = scan_complete
config["events"]["critical_issues"] = critical_issues
config["events"]["threshold_alerts"] = threshold_alerts
config["events"]["system_status"] = system_status

st.markdown("</div>", unsafe_allow_html=True)

# Quiet hours settings
st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
st.subheader("Quiet Hours")
st.write("Disable non-critical notifications during specific hours")

quiet_hours_enabled = st.checkbox(
    "Enable Quiet Hours",
    value=config["quiet_hours"]["enabled"],
    help="Only critical notifications will be sent during quiet hours"
)

if quiet_hours_enabled:
    col1, col2 = st.columns(2)
    
    with col1:
        start_time = st.time_input(
            "Start Time",
            value=config["quiet_hours"].get("start_time", "22:00")
        )
    
    with col2:
        end_time = st.time_input(
            "End Time",
            value=config["quiet_hours"].get("end_time", "08:00")
        )
    
    # Update config with time values
    config["quiet_hours"]["start_time"] = start_time.strftime("%H:%M")
    config["quiet_hours"]["end_time"] = end_time.strftime("%H:%M")

# Update config
config["quiet_hours"]["enabled"] = quiet_hours_enabled

st.markdown("</div>", unsafe_allow_html=True)

# Save settings
st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
if st.button("Save Notification Settings", type="primary"):
    if save_notification_config(config):
        st.success("Notification settings saved successfully!")
    else:
        st.error("Failed to save notification settings")

st.markdown("</div>", unsafe_allow_html=True)
