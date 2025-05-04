#!/usr/bin/env python3
"""
Discord Notifier Module for Media Manager
Sends notifications to Discord via webhooks
"""

import os
import logging
import json
import time
import threading
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """Module for sending notifications to Discord via webhooks"""
    
    def __init__(self, config):
        """
        Initialize the Discord notifier
        
        Args:
            config (dict): Discord notifier configuration
        """
        self.config = config
        self.webhook_url = config.get('webhook_url')
        self.username = config.get('username', 'Media Manager')
        self.avatar_url = config.get('avatar_url')
        self.throttle = config.get('throttle', 5)  # Minimum seconds between notifications
        self.dashboard_url = config.get('dashboard_url')
        self.level_colors = {
            'INFO': 0x3498db,      # Blue
            'WARNING': 0xf1c40f,   # Yellow
            'ERROR': 0xe74c3c,     # Red
            'CRITICAL': 0x9b59b6   # Purple
        }
        
        # Last notification time for throttling
        self.last_notification_time = 0
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        if not self.webhook_url:
            logger.error("Discord webhook URL is not configured")
    
    def send(self, notification):
        """
        Send a notification to Discord
        
        Args:
            notification (dict): Notification data
        """
        if not self.webhook_url:
            return
        
        # Get notification details
        title = notification['title']
        message = notification['message']
        level = notification['level']
        timestamp = notification['timestamp']
        data = notification.get('data', {})
        
        # Throttle notifications
        with self.lock:
            current_time = time.time()
            
            # Skip if throttled
            if (current_time - self.last_notification_time) < self.throttle:
                logger.debug("Throttled Discord notification")
                return
            
            self.last_notification_time = current_time
        
        # Create embed
        embed = self._create_embed(title, message, level, timestamp, data)
        
        # Send webhook
        self._send_webhook(embed)
    
    def _create_embed(self, title, message, level, timestamp, data):
        """
        Create Discord embed object
        
        Args:
            title (str): Notification title
            message (str): Notification message
            level (str): Notification level
            timestamp (datetime): Notification timestamp
            data (dict): Additional data
            
        Returns:
            dict: Discord embed object
        """
        # Create basic embed
        embed = {
            'title': title,
            'description': message,
            'color': self.level_colors.get(level, 0x95a5a6),  # Default gray
            'timestamp': timestamp.isoformat(),
            'footer': {
                'text': f'Media Manager | {level}'
            },
            'fields': []
        }
        
        # Add dashboard link if available
        if self.dashboard_url:
            embed['url'] = self.dashboard_url
        
        # Add additional fields based on data
        if data:
            # Add file info if available
            if 'file_name' in data:
                embed['fields'].append({
                    'name': 'File',
                    'value': data['file_name'],
                    'inline': True
                })
            
            # Add duration info if available
            if 'duration' in data and 'expected_duration' in data:
                embed['fields'].append({
                    'name': 'Duration',
                    'value': f"Actual: {self._format_duration(data['duration'])}\nExpected: {self._format_duration(data['expected_duration'])}",
                    'inline': True
                })
            
            # Add API info if available
            if 'api' in data:
                embed['fields'].append({
                    'name': 'API',
                    'value': data['api'],
                    'inline': True
                })
            
            # Add scan info if available
            if 'total_files' in data:
                scan_info = f"Total: {data['total_files']}"
                if 'issues_found' in data:
                    scan_info += f"\nIssues: {data['issues_found']}"
                embed['fields'].append({
                    'name': 'Scan Results',
                    'value': scan_info,
                    'inline': True
                })
        
        return embed
    
    def _send_webhook(self, embed):
        """
        Send webhook to Discord
        
        Args:
            embed (dict): Discord embed object
        """
        # Create payload
        payload = {
            'username': self.username,
            'embeds': [embed]
        }
        
        # Add avatar if configured
        if self.avatar_url:
            payload['avatar_url'] = self.avatar_url
        
        try:
            # Send webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            # Check response
            if response.status_code != 204:
                logger.error(f"Failed to send Discord webhook: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Exception sending Discord webhook: {e}")
    
    def _format_duration(self, duration_ms):
        """
        Format duration in milliseconds to human-readable string
        
        Args:
            duration_ms (int): Duration in milliseconds
            
        Returns:
            str: Formatted duration string
        """
        if not duration_ms:
            return 'Unknown'
        
        # Convert to seconds
        duration_sec = duration_ms / 1000
        
        # Format as hours:minutes:seconds
        hours = int(duration_sec // 3600)
        minutes = int((duration_sec % 3600) // 60)
        seconds = int(duration_sec % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
