#!/usr/bin/env python3
"""
Windows Notifier Module for Media Manager
Sends notifications to the Windows notification system
"""

import os
import logging
import platform
import threading

logger = logging.getLogger(__name__)

class WindowsNotifier:
    """Module for sending notifications to Windows notification system"""
    
    def __init__(self, config):
        """
        Initialize the Windows notifier
        
        Args:
            config (dict): Windows notifier configuration
        """
        self.config = config
        self.app_name = config.get('app_name', 'Media Manager')
        self.icon_path = config.get('icon_path')
        self.duration = config.get('duration', 5)  # Duration in seconds
        self.throttle = config.get('throttle', 3)  # Minimum seconds between notifications
        
        # Check if running on Windows
        self.is_windows = platform.system() == "Windows"
        
        if not self.is_windows:
            logger.warning("Windows notifier initialized but not running on Windows")
        
        # Initialize notifier
        self._initialize_notifier()
        
        # Last notification time for throttling
        self.last_notification_time = 0
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def _initialize_notifier(self):
        """Initialize the Windows notification library"""
        if not self.is_windows:
            self.notifier = None
            return
        
        try:
            # Try to import winotify first (preferred)
            from winotify import Notification
            self.notifier_type = 'winotify'
            logger.info("Using winotify for Windows notifications")
        except ImportError:
            try:
                # Fall back to win10toast
                from win10toast import ToastNotifier
                self.notifier = ToastNotifier()
                self.notifier_type = 'win10toast'
                logger.info("Using win10toast for Windows notifications")
            except ImportError:
                logger.error("Could not import Windows notification libraries (winotify or win10toast)")
                self.notifier = None
                self.notifier_type = None
    
    def send(self, notification):
        """
        Send a notification to the Windows notification system
        
        Args:
            notification (dict): Notification data
        """
        if not self.is_windows or not self.notifier_type:
            return
        
        # Get notification details
        title = notification['title']
        message = notification['message']
        level = notification['level']
        
        # Throttle notifications
        with self.lock:
            import time
            current_time = time.time()
            
            # Skip if throttled
            if (current_time - self.last_notification_time) < self.throttle:
                logger.debug("Throttled Windows notification")
                return
            
            self.last_notification_time = current_time
        
        # Send notification based on the library
        if self.notifier_type == 'winotify':
            self._send_winotify(title, message, level)
        elif self.notifier_type == 'win10toast':
            self._send_win10toast(title, message, level)
    
    def _send_winotify(self, title, message, level):
        """
        Send notification using winotify
        
        Args:
            title (str): Notification title
            message (str): Notification message
            level (str): Notification level
        """
        try:
            from winotify import Notification
            
            # Create notification
            notification = Notification(
                app_id=self.app_name,
                title=title,
                msg=message,
                duration="short" if self.duration <= 5 else "long"
            )
            
            # Set icon based on level
            if self.icon_path:
                icon_file = self._get_icon_for_level(level)
                if icon_file:
                    notification.set_image(icon_file)
            
            # Send notification
            notification.show()
            
        except Exception as e:
            logger.error(f"Failed to send Windows notification via winotify: {e}")
    
    def _send_win10toast(self, title, message, level):
        """
        Send notification using win10toast
        
        Args:
            title (str): Notification title
            message (str): Notification message
            level (str): Notification level
        """
        try:
            # Get icon based on level
            icon_path = None
            if self.icon_path:
                icon_file = self._get_icon_for_level(level)
                if icon_file:
                    icon_path = icon_file
            
            # Send notification
            self.notifier.show_toast(
                title=title,
                msg=message,
                icon_path=icon_path,
                duration=self.duration,
                threaded=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send Windows notification via win10toast: {e}")
    
    def _get_icon_for_level(self, level):
        """
        Get icon path based on notification level
        
        Args:
            level (str): Notification level
            
        Returns:
            str: Path to icon file
        """
        if not self.icon_path:
            return None
        
        # Map levels to icon files
        level_icons = {
            "INFO": "info.ico",
            "WARNING": "warning.ico",
            "ERROR": "error.ico",
            "CRITICAL": "critical.ico"
        }
        
        # Get icon file name
        icon_file = level_icons.get(level, "info.ico")
        
        # Build full path
        full_path = os.path.join(self.icon_path, icon_file)
        
        # Return icon path if file exists
        if os.path.isfile(full_path):
            return full_path
        
        # Fall back to default icon
        default_icon = os.path.join(self.icon_path, "app.ico")
        if os.path.isfile(default_icon):
            return default_icon
        
        return None
