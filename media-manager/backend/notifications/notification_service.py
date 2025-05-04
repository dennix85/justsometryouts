#!/usr/bin/env python3
"""
Notification Service for Media Manager
Provides a centralized notification system with multiple output channels
"""

import os
import logging
import json
import time
import threading
from datetime import datetime
from queue import Queue

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing and sending notifications through multiple channels"""
    
    def __init__(self, config, db_manager=None):
        """
        Initialize the notification service
        
        Args:
            config (dict): Notification configuration
            db_manager (DatabaseManager, optional): Database manager instance
        """
        self.config = config
        self.db_manager = db_manager
        self.notifiers = []
        self.notification_queue = Queue()
        self.quiet_hours = self._parse_quiet_hours()
        
        # Statistics
        self.stats = {
            'total_notifications': 0,
            'windows_notifications': 0,
            'discord_notifications': 0,
            'suppressed_notifications': 0,
            'errors': 0
        }
        
        # Initialize notifiers based on configuration
        self._initialize_notifiers()
        
        # Start queue processing thread
        self.queue_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.queue_thread.start()
        
        logger.info("Notification service initialized")
    
    def _parse_quiet_hours(self):
        """
        Parse quiet hours from configuration
        
        Returns:
            dict: Quiet hours configuration
        """
        quiet_config = self.config.get('quiet_hours', {})
        
        if not quiet_config.get('enabled', False):
            return None
        
        try:
            return {
                'enabled': True,
                'start_time': datetime.strptime(quiet_config.get('start_time', '22:00'), '%H:%M').time(),
                'end_time': datetime.strptime(quiet_config.get('end_time', '08:00'), '%H:%M').time(),
                'allow_critical': quiet_config.get('allow_critical', True)
            }
        except ValueError:
            logger.error("Invalid quiet hours format in configuration")
            return None
    
    def _initialize_notifiers(self):
        """Initialize notification channels based on configuration"""
        
        # Initialize Windows notifier if enabled
        if self.config.get('windows', {}).get('enabled', False):
            try:
                from .windows_notifier import WindowsNotifier
                windows_config = self.config.get('windows', {})
                self.notifiers.append(WindowsNotifier(windows_config))
                logger.info("Windows notifier initialized")
            except ImportError as e:
                logger.error(f"Failed to import Windows notifier: {e}")
        
        # Initialize Discord notifier if enabled
        if self.config.get('discord', {}).get('enabled', False):
            try:
                from .discord_notifier import DiscordNotifier
                discord_config = self.config.get('discord', {})
                self.notifiers.append(DiscordNotifier(discord_config))
                logger.info("Discord notifier initialized")
            except ImportError as e:
                logger.error(f"Failed to import Discord notifier: {e}")
    
    def send_notification(self, title, message, level="INFO", data=None):
        """
        Send a notification through all configured channels
        
        Args:
            title (str): Notification title
            message (str): Notification message
            level (str): Notification level (INFO, WARNING, ERROR, CRITICAL)
            data (dict, optional): Additional data to include with the notification
        """
        # Update statistics
        self.stats['total_notifications'] += 1
        
        # Create notification
        notification = {
            'title': title,
            'message': message,
            'level': level.upper(),
            'timestamp': datetime.now(),
            'data': data
        }
        
        # Add to queue for processing
        self.notification_queue.put(notification)
        
        # If it's a critical notification, also log it
        if level.upper() in ['ERROR', 'CRITICAL']:
            logger.error(f"{title}: {message}")
        else:
            logger.info(f"{title}: {message}")
        
        # Store in database if available
        if self.db_manager:
            try:
                self.db_manager.store_notification(notification)
            except Exception as e:
                logger.error(f"Failed to store notification in database: {e}")
    
    def _process_queue(self):
        """Process notifications in the queue"""
        while True:
            notification = self.notification_queue.get()
            
            # Check quiet hours
            if self._should_suppress_notification(notification):
                self.stats['suppressed_notifications'] += 1
                self.notification_queue.task_done()
                continue
            
            # Send to all notifiers
            for notifier in self.notifiers:
                try:
                    notifier.send(notification)
                    
                    # Update statistics based on notifier type
                    if notifier.__class__.__name__ == 'WindowsNotifier':
                        self.stats['windows_notifications'] += 1
                    elif notifier.__class__.__name__ == 'DiscordNotifier':
                        self.stats['discord_notifications'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send notification via {notifier.__class__.__name__}: {e}")
                    self.stats['errors'] += 1
            
            self.notification_queue.task_done()
    
    def _should_suppress_notification(self, notification):
        """
        Check if notification should be suppressed (e.g., during quiet hours)
        
        Args:
            notification (dict): Notification data
            
        Returns:
            bool: True if notification should be suppressed, False otherwise
        """
        if not self.quiet_hours or not self.quiet_hours['enabled']:
            return False
        
        current_time = datetime.now().time()
        start_time = self.quiet_hours['start_time']
        end_time = self.quiet_hours['end_time']
        
        # Check if current time is within quiet hours
        in_quiet_hours = False
        
        # Handle case where quiet hours span midnight
        if start_time > end_time:
            in_quiet_hours = current_time >= start_time or current_time <= end_time
        else:
            in_quiet_hours = start_time <= current_time <= end_time
        
        # Allow critical notifications during quiet hours if configured
        if in_quiet_hours and notification['level'] in ['ERROR', 'CRITICAL'] and self.quiet_hours['allow_critical']:
            return False
        
        return in_quiet_hours
    
    def get_stats(self):
        """
        Get notification statistics
        
        Returns:
            dict: Notification statistics
        """
        return self.stats
