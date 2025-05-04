#!/usr/bin/env python3
"""
Media Manager - Main Application Entry Point
This script initializes and runs the media management system.
"""

import os
import logging
import argparse
import yaml
from pathlib import Path

# Internal imports
from backend.database.db_manager import DatabaseManager
from backend.scanner.scanner import MediaScanner
from backend.analyzer.analyzer import MediaAnalyzer
from backend.api_integration.api_service import APIService
from backend.validators.duration_validator import DurationValidator
from backend.notification.notification_service import NotificationService
from frontend.dashboard import start_dashboard

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("media_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def create_default_config(config_path):
    """Create default configuration if none exists."""
    default_config = {
        'media_directories': [],
        'database': {
            'path': 'media_manager.db'
        },
        'api': {
            'sonarr_instances': [],
            'radarr_instances': [],
            'omdb_api_keys': []
        },
        'notifications': {
            'windows': {
                'enabled': True
            },
            'discord': {
                'enabled': False,
                'webhook_url': ''
            }
        },
        'dashboard': {
            'port': 8501
        }
    }
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as file:
        yaml.dump(default_config, file, default_flow_style=False)
    
    logger.info(f"Created default configuration at {config_path}")
    return default_config

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='Media Manager')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--scan', action='store_true',
                        help='Run a media scan')
    parser.add_argument('--dashboard', action='store_true',
                        help='Start the dashboard')
    args = parser.parse_args()
    
    # Load or create configuration
    config_path = Path(args.config)
    if not config_path.exists():
        config = create_default_config(config_path)
        logger.info("Please configure the application by editing the config file.")
        return
    else:
        config = load_config(config_path)
    
    # Initialize components
    db_manager = DatabaseManager(config['database']['path'])
    notification_service = NotificationService(config['notifications'])
    api_service = APIService(config['api'], notification_service)
    
    # Notify application start
    notification_service.send_notification(
        "Media Manager", 
        "Application started",
        "INFO"
    )
    
    # Run requested operations
    if args.scan:
        scanner = MediaScanner(config['media_directories'], db_manager, notification_service)
        analyzer = MediaAnalyzer(db_manager, notification_service)
        validator = DurationValidator(db_manager, api_service, notification_service)
        
        # Run the media scanning process
        scanner.scan()
        analyzer.analyze_new_files()
        validator.validate()
        
        logger.info("Scan completed")
        notification_service.send_notification(
            "Media Manager", 
            "Scan completed",
            "INFO"
        )
    
    # Start dashboard if requested or if no other action specified
    if args.dashboard or (not args.scan):
        try:
            notification_service.send_notification(
                "Media Manager", 
                "Dashboard starting on port " + str(config['dashboard']['port']),
                "INFO"
            )
            start_dashboard(db_manager, api_service, notification_service, config)
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
            notification_service.send_notification(
                "Media Manager", 
                "Dashboard stopped",
                "INFO"
            )

if __name__ == "__main__":
    main()
