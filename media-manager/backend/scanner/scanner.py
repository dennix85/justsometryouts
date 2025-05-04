#!/usr/bin/env python3
"""
Media Scanner for Media Manager
Scans directories for media files and adds them to the database
"""

import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class MediaScanner:
    """Scans directories for media files"""
    
    # Extensions to consider as media files
    MEDIA_EXTENSIONS = {
        'video': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v', '.mpg', '.mpeg', '.flv', '.webm'],
        'subtitle': ['.srt', '.ass', '.ssa', '.sub', '.idx', '.vtt']
    }
    
    def __init__(self, media_dirs, db_manager, notification_service):
        """
        Initialize the media scanner
        
        Args:
            media_dirs (list): List of directories to scan
            db_manager (DatabaseManager): Database manager instance
            notification_service (NotificationService): Notification service instance
        """
        self.media_dirs = media_dirs
        self.db_manager = db_manager
        self.notification_service = notification_service
        
        # Statistics
        self.stats = {
            'total_scanned': 0,
            'new_files': 0,
            'updated_files': 0,
            'errors': 0
        }
    
    def scan(self):
        """
        Scan all configured media directories
        
        Returns:
            dict: Scan statistics
        """
        logger.info(f"Starting media scan of {len(self.media_dirs)} directories")
        
        if not self.media_dirs:
            logger.warning("No media directories configured for scanning")
            self.notification_service.send_notification(
                "Media Scanner", 
                "No media directories configured for scanning",
                "WARNING"
            )
            return self.stats
        
        for media_dir in self.media_dirs:
            try:
                self._scan_directory(media_dir)
            except Exception as e:
                logger.error(f"Error scanning directory {media_dir}: {e}")
                self.stats['errors'] += 1
        
        # Send notification with scan results
        message = (
            f"Scan completed: {self.stats['total_scanned']} files scanned, "
            f"{self.stats['new_files']} new, {self.stats['updated_files']} updated, "
            f"{self.stats['errors']} errors"
        )
        
        logger.info(message)
        self.notification_service.send_notification("Media Scanner", message, "INFO")
        
        return self.stats
    
    def _scan_directory(self, directory):
        """
        Recursively scan a directory for media files
        
        Args: