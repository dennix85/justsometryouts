import os
import sys
import json
import time
import subprocess
import datetime
import threading
import queue
import re
from pathlib import Path
import requests
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import sqlite3
from datetime import datetime, timedelta

class MediaScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Scanner")
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Application data
        self.db_path = "media_scanner.db"
        self.settings = {
            "omdb_api_keys": ["", "", "", "", ""],  # 5 API keys
            "scan_folders": [],
            "refresh_interval": 12,  # in hours
            "verbose_logging": False
        }
        self.api_keys_status = {}  # To track API key usage and cooldown times
        self.scanning_active = False
            
    def scan_folders(self):
        """Scan folders for media files"""
        media_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v', '.mpg', '.mpeg', '.flv']
        all_media_files = []
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all known file paths
        cursor.execute("SELECT path FROM files")
        known_files = {row[0] for row in cursor.fetchall()}
        
        # Scan each folder
        for folder in self.settings["scan_folders"]:
            self.log(f"Scanning folder: {folder}")
            
            try:
                for root, _, files in os.walk(folder):
                    for file in files:
                        # Check if file has a media extension
                        if any(file.lower().endswith(ext) for ext in media_extensions):
                            file_path = os.path.join(root, file)
                            
                            # Skip if already in database and not "queued" status
                            if file_path in known_files:
                                # Get status
                                cursor.execute("SELECT status FROM files WHERE path = ?", (file_path,))
                                status = cursor.fetchone()[0]
                                
                                # Skip "good" or "suspicious" files
                                if status in ["good", "suspicious"]:
                                    if self.settings["verbose_logging"]:
                                        self.log(f"Skipping known file: {file_path}")
                                    continue
                            
                            all_media_files.append(file_path)
                            
                            # Add new file to database with "queued" status if not exists
                            if file_path not in known_files:
                                file_size = os.path.getsize(file_path)
                                directory = os.path.dirname(file_path)
                                cursor.execute(
                                    "INSERT OR IGNORE INTO files (path, filename, directory, size, status, last_checked) VALUES (?, ?, ?, ?, ?, ?)",
                                    (file_path, file, directory, file_size, "queued", datetime.now().isoformat())
                                )
            except Exception as e:
                self.log(f"Error scanning folder {folder}: {e}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        return all_media_files
        
    def process_media_files(self, media_files):
        """Process media files to collect information"""
        count = 0
        total = len(media_files)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for file_path in media_files:
            count += 1
            self.log(f"Processing file {count}/{total}: {os.path.basename(file_path)}")
            
            try:
                # Check if media info already exists
                cursor.execute("SELECT duration FROM files WHERE path = ? AND duration IS NOT NULL", (file_path,))
                if cursor.fetchone():
                    if self.settings["verbose_logging"]:
                        self.log(f"Media info already exists for {file_path}")
                    
                    # Update status to awaiting_omdb if needed
                    cursor.execute("UPDATE files SET status = 'awaiting_omdb' WHERE path = ? AND status = 'queued'", (file_path,))
                    continue
                
                # Get media info using ffprobe
                media_info = self.get_media_info(file_path)
                
                if media_info:
                    # Update database with media info
                    cursor.execute(
                        """UPDATE files SET 
                        duration = ?, video_codec = ?, hdr_type = ?, 
                        audio_streams = ?, subtitles = ?, status = 'awaiting_omdb'
                        WHERE path = ?""",
                        (
                            media_info["duration"],
                            media_info["video_codec"],
                            media_info["hdr_type"],
                            media_info["audio_streams"],
                            media_info["subtitles"],
                            file_path
                        )
                    )
                    
                    # Commit each file to avoid losing data on error
                    conn.commit()
                else:
                    self.log(f"Failed to get media info for {file_path}")
            except Exception as e:
                self.log(f"Error processing file {file_path}: {e}")
        
        conn.close()
    
    def get_media_info(self, file_path):
        """Get media info using ffprobe"""
        try:
            # Run ffprobe to get JSON output
            ffprobe_cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]
            
            if self.settings["verbose_logging"]:
                self.ffprobe_log(f"Running command: {' '.join(ffprobe_cmd)}")
            
            # Use subprocess to capture output
            process = subprocess.Popen(
                ffprobe_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if stderr:
                self.ffprobe_log(f"ffprobe stderr: {stderr}")
            
            if not stdout:
                self.ffprobe_log(f"No output from ffprobe for {file_path}")
                return None
            
            # Parse JSON output
            data = json.loads(stdout)
            
            # Extract information
            media_info = {
                "duration": float(data["format"]["duration"]) if "duration" in data["format"] else None,
                "video_codec": None,
                "hdr_type": "Unknown",
                "audio_streams": [],
                "subtitles": []
            }
            
            # Process streams
            for stream in data["streams"]:
                codec_type = stream.get("codec_type", "")
                
                if codec_type == "video":
                    media_info["video_codec"] = stream.get("codec_name", "Unknown")
                    
                    # Try to determine HDR type
                    color_space = stream.get("color_space", "")
                    color_transfer = stream.get("color_transfer", "")
                    
                    if "bt2020" in color_space.lower():
                        if "smpte2084" in color_transfer.lower():
                            media_info["hdr_type"] = "HDR10"
                        elif "arib-std-b67" in color_transfer.lower():
                            media_info["hdr_type"] = "HLG"
                    elif media_info["hdr_type"] == "Unknown":
                        media_info["hdr_type"] = "SDR"
                    
                elif codec_type == "audio":
                    codec = stream.get("codec_name", "Unknown")
                    lang = stream.get("tags", {}).get("language", "Unknown")
                    media_info["audio_streams"].append(f"{codec}:{lang}")
                
                elif codec_type == "subtitle":
                    lang = stream.get("tags", {}).get("language", "Unknown")
                    media_info["subtitles"].append(lang)
            
            # Format as strings for database
            media_info["audio_streams"] = ", ".join(media_info["audio_streams"])
            media_info["subtitles"] = ", ".join(media_info["subtitles"])
            
            if self.settings["verbose_logging"]:
                self.ffprobe_log(f"Media info for {file_path}: {media_info}")
            
            return media_info
        
        except Exception as e:
            self.ffprobe_log(f"Error getting media info: {e}")
            return None
            
    def process_omdb_queue(self):
        """Process files in OMDB queue"""
        # Check if we have active API keys
        active_keys = [key for key, status in self.api_keys_status.items() 
                      if key and not status["blocked"]]
        
        if not active_keys:
            self.log("No active OMDB API keys available")
            return
        
        # Get files waiting for OMDB processing
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, path, filename FROM files WHERE status = 'awaiting_omdb'")
        files = cursor.fetchall()
        
        if not files:
            self.log("No files waiting for OMDB processing")
            conn.close()
            return
        
        self.log(f"Processing {len(files)} files with OMDB")
        
        # Process each file
        for file_id, file_path, filename in files:
            # Get a clean title from filename
            title = self.extract_title_from_filename(filename)
            
            if not title:
                self.log(f"Could not extract title from: {filename}")
                continue
                
            # Try to get OMDB info
            omdb_info = self.get_omdb_info(title)
            
            if not omdb_info:
                self.log(f"Could not get OMDB info for: {title}")
                continue
            
            # Update database with OMDB info
            cursor.execute(
                "UPDATE files SET omdb_id = ?, omdb_duration = ? WHERE id = ?",
                (omdb_info["imdbID"], omdb_info["Runtime"], file_id)
            )
            
            # Check if duration is suspicious
            if self.is_duration_suspicious(file_path, omdb_info["Runtime"]):
                cursor.execute("UPDATE files SET status = 'suspicious' WHERE id = ?", (file_id,))
                self.log(f"Marked as suspicious: {filename}")
            else:
                cursor.execute("UPDATE files SET status = 'good' WHERE id = ?", (file_id,))
                self.log(f"Marked as good: {filename}")
            
            # Commit after each file
            conn.commit()
            
            # Check if all API keys are blocked
            active_keys = [key for key, status in self.api_keys_status.items() 
                          if key and not status["blocked"]]
            
            if not active_keys:
                self.log("All API keys blocked, stopping OMDB processing")
                break
        
        conn.close()
        
    def extract_title_from_filename(self, filename):
        """Extract movie/show title from filename"""
        # Remove file extension
        name = os.path.splitext(filename)[0]
        
        # Remove common patterns like year, quality, resolution, codecs
        # Remove anything in brackets or parentheses
        name = re.sub(r'\[[^\]]*\]|\([^)]*\)|\{[^}]*\}', '', name)
        
        # Remove resolution patterns
        name = re.sub(r'\b\d{3,4}p\b|\bHD\b|\bFHD\b|\bUHD\b|\b4K\b|\b8K\b', '', name, flags=re.IGNORECASE)
        
        # Remove codec/quality identifiers
        name = re.sub(r'\bx264\b|\bx265\b|\bHEVC\b|\bXVID\b|\bDivX\b|\bBluRay\b|\bWEB-DL\b|\bHDTV\b', '', name, flags=re.IGNORECASE)
        
        # Remove season/episode patterns
        name = re.sub(r'S\d{1,2}E\d{1,2}|\bd{1,2}x\d{1,2}', '', name, flags=re.IGNORECASE)
        
        # Remove years
        name = re.sub(r'\b(19|20)\d{2}\b', '', name)
        
        # Remove dots, underscores, hyphens
        name = re.sub(r'[._-]', ' ', name)
        
        # Clean up extra spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name if name else None
    
    def get_omdb_info(self, title):
        """Get movie/show info from OMDB API"""
        # Get an active API key
        active_keys = [key for key, status in self.api_keys_status.items() 
                      if key and not status["blocked"]]
        
        if not active_keys:
            self.log("No active OMDB API keys available")
            return None
        
        api_key = active_keys[0]
        
        try:
            # Make OMDB API request
            url = f"http://www.omdbapi.com/?apikey={api_key}&t={title}&r=json"
            response = requests.get(url, timeout=10)
            
            # Update API key usage counter
            self.api_keys_status[api_key]["daily_calls"] += 1
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE api_keys SET daily_calls = ? WHERE key = ?",
                (self.api_keys_status[api_key]["daily_calls"], api_key)
            )
            conn.commit()
            conn.close()
            
            # Check if we've hit the limit
            if self.api_keys_status[api_key]["daily_calls"] >= 1000:
                self.log(f"API key {api_key[:5]}... has reached the daily limit")
                self.block_api_key(api_key)
            
            # Process response
            if response.status_code == 200:
                data = response.json()
                
                if data.get("Response") == "True":
                    return data
                else:
                    self.log(f"OMDB error for {title}: {data.get('Error', 'Unknown error')}")
                    return None
            else:
                self.log(f"HTTP error {response.status_code} for {title}")
                
                # Check if it's a 401/403 error, which might indicate API key issue
                if response.status_code in [401, 403]:
                    self.log(f"API key {api_key[:5]}... might be invalid or expired")
                    self.block_api_key(api_key)
                
                return None
                
        except Exception as e:
            self.log(f"Error getting OMDB info for {title}: {e}")
            return None
            
    def block_api_key(self, api_key):
        """Block an API key for 24 hours"""
        cooldown_time = datetime.now() + timedelta(hours=24)
        
        self.api_keys_status[api_key] = {
            "blocked": True,
            "cooldown_until": cooldown_time.isoformat(),
            "daily_calls": 1000
        }
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO api_keys VALUES (?, ?, ?, ?)",
            (api_key, 1, cooldown_time.isoformat(), 1000)
        )
        conn.commit()
        conn.close()
        
        self.log(f"API key {api_key[:5]}... blocked until {cooldown_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def is_duration_suspicious(self, file_path, omdb_duration):
        """Check if file duration is suspiciously different from OMDB duration"""
        # Get file duration from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT duration FROM files WHERE path = ?", (file_path,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0] or not omdb_duration:
            return False
            
        file_duration = result[0]
        
        # Convert file duration to minutes
        file_minutes = file_duration / 60
        
        # Parse OMDB duration (format: "X h Y min" or "Y min")
        omdb_minutes = 0
        hours_match = re.search(r'(\d+)\s*h', omdb_duration)
        minutes_match = re.search(r'(\d+)\s*min', omdb_duration)
        
        hours = int(hours_match.group(1)) if hours_match else 0
        minutes = int(minutes_match.group(1)) if minutes_match else 0
        
        omdb_minutes = hours * 60 + minutes
        
        # Allow for some variation (10% or 5 minutes, whichever is greater)
        threshold = max(omdb_minutes * 0.1, 5)
        difference = abs(file_minutes - omdb_minutes)
        
        return difference > threshold
        
    def refresh_all_views(self):
        """Refresh all views"""
        self.refresh_queued_files()
        self.refresh_omdb_queue()
        self.refresh_suspicious_files()
        self.refresh_good_files()
            
    def on_closing(self):
        """Handle window closing"""
        if self.scanning_active:
            if tk.messagebox.askokcancel("Quit", "A scan is in progress. Are you sure you want to quit?"):
                self.root.destroy()
        else:
            self.root.destroy()
        self.scan_thread = None
        self.log_queue = queue.Queue()
        self.ffprobe_queue = queue.Queue()
        
        # Create database and tables if they don't exist
        self.setup_database()
        
        # Load settings if they exist
        self.load_settings()
        
        # Initialize API key status
        for key in self.settings["omdb_api_keys"]:
            if key:
                self.api_keys_status[key] = {
                    "blocked": False,
                    "cooldown_until": None,
                    "daily_calls": 0
                }
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create the six tabs
        self.setup_settings_tab()
        self.setup_log_tab()
        self.setup_ffprobe_tab()
        self.setup_queued_files_tab()
        self.setup_omdb_queue_tab()
        self.setup_suspicious_files_tab()
        self.setup_good_files_tab()
        
        # Start the logging update threads
        threading.Thread(target=self.update_log, daemon=True).start()
        threading.Thread(target=self.update_ffprobe_log, daemon=True).start()
        
        # Start the scheduled scanner
        self.schedule_scan()
        
        # Log application start
        self.log("Application started")

    def setup_database(self):
        """Create database and tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create files table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE,
            filename TEXT,
            directory TEXT,
            size INTEGER,
            duration REAL,
            video_codec TEXT,
            hdr_type TEXT,
            audio_streams TEXT,
            subtitles TEXT,
            omdb_id TEXT,
            omdb_duration TEXT,
            status TEXT,
            last_checked TIMESTAMP
        )
        ''')
        
        # Create api_keys table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            blocked INTEGER,
            cooldown_until TIMESTAMP,
            daily_calls INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()

    def load_settings(self):
        """Load settings from JSON file"""
        try:
            with open('settings.json', 'r') as f:
                self.settings = json.load(f)
                self.log("Settings loaded successfully")
        except FileNotFoundError:
            self.log("No settings file found, using defaults")
        except json.JSONDecodeError:
            self.log("Error parsing settings file, using defaults")

    def save_settings(self):
        """Save settings to JSON file"""
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
        self.log("Settings saved")
        
        # Update API keys status in the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear old keys and insert current ones
        cursor.execute("DELETE FROM api_keys")
        
        for key, status in self.api_keys_status.items():
            if key:  # Skip empty keys
                cursor.execute(
                    "INSERT INTO api_keys VALUES (?, ?, ?, ?)",
                    (key, 1 if status["blocked"] else 0, 
                     status["cooldown_until"] if status["cooldown_until"] else None,
                     status["daily_calls"])
                )
        
        conn.commit()
        conn.close()

    def setup_settings_tab(self):
        """Setup the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # API Keys section
        ttk.Label(settings_frame, text="OMDB API Keys:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.api_key_entries = []
        for i in range(5):
            api_key_var = tk.StringVar(value=self.settings["omdb_api_keys"][i] if i < len(self.settings["omdb_api_keys"]) else "")
            api_key_entry = ttk.Entry(settings_frame, textvariable=api_key_var, width=40)
            api_key_entry.grid(row=i+1, column=0, padx=20, pady=2, sticky="w")
            self.api_key_entries.append(api_key_var)
            
            # Show API key status
            status_text = "Not used yet" if api_key_var.get() else "No key entered"
            status_label = ttk.Label(settings_frame, text=status_text)
            status_label.grid(row=i+1, column=1, padx=10, pady=2, sticky="w")
            
        # Folder section
        ttk.Label(settings_frame, text="Scan Folders:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        
        # Create a frame for the folders list
        folders_frame = ttk.Frame(settings_frame)
        folders_frame.grid(row=7, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        # Create a listbox for folders
        self.folders_listbox = tk.Listbox(folders_frame, width=60, height=5)
        self.folders_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        
        # Add scrollbar to the listbox
        scrollbar = ttk.Scrollbar(folders_frame, orient="vertical", command=self.folders_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.folders_listbox.config(yscrollcommand=scrollbar.set)
        
        # Add folders to the listbox
        for folder in self.settings["scan_folders"]:
            self.folders_listbox.insert(tk.END, folder)
        
        # Buttons for folder management
        folder_buttons_frame = ttk.Frame(settings_frame)
        folder_buttons_frame.grid(row=8, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        ttk.Button(folder_buttons_frame, text="Add Folder", command=self.add_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(folder_buttons_frame, text="Remove Selected", command=self.remove_folder).pack(side=tk.LEFT, padx=5)
        
        # Refresh interval
        ttk.Label(settings_frame, text="Refresh Interval (hours):").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        self.refresh_interval_var = tk.IntVar(value=self.settings["refresh_interval"])
        ttk.Spinbox(settings_frame, from_=1, to=168, textvariable=self.refresh_interval_var, width=5).grid(row=9, column=1, sticky="w", padx=10, pady=5)
        
        # Verbose logging
        self.verbose_logging_var = tk.BooleanVar(value=self.settings["verbose_logging"])
        ttk.Checkbutton(settings_frame, text="Verbose Logging", variable=self.verbose_logging_var).grid(row=10, column=0, sticky="w", padx=10, pady=5)
        
        # Save button
        ttk.Button(settings_frame, text="Save Settings", command=self.save_settings_from_gui).grid(row=11, column=0, padx=10, pady=10, sticky="w")
        
        # Scan button
        ttk.Button(settings_frame, text="Start Manual Scan", command=self.start_scan).grid(row=11, column=1, padx=10, pady=10, sticky="w")

    def setup_log_tab(self):
        """Setup the log tab"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Log")
        
        # Log text widget
        self.log_text = scrolledtext.ScrolledText(log_frame, width=100, height=30)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(pady=5)

    def setup_ffprobe_tab(self):
        """Setup the ffprobe log tab"""
        ffprobe_frame = ttk.Frame(self.notebook)
        self.notebook.add(ffprobe_frame, text="FFProbe Log")
        
        # FFProbe log text widget
        self.ffprobe_text = scrolledtext.ScrolledText(ffprobe_frame, width=100, height=30)
        self.ffprobe_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.ffprobe_text.config(state=tk.DISABLED)
        
        # Clear ffprobe log button
        ttk.Button(ffprobe_frame, text="Clear FFProbe Log", command=self.clear_ffprobe_log).pack(pady=5)

    def setup_queued_files_tab(self):
        """Setup the queued files tab"""
        queued_frame = ttk.Frame(self.notebook)
        self.notebook.add(queued_frame, text="Queued Files")
        
        # Create a treeview for the queued files
        columns = ("path", "size", "status")
        self.queued_tree = ttk.Treeview(queued_frame, columns=columns, show='headings')
        
        # Define headings
        self.queued_tree.heading("path", text="File Path")
        self.queued_tree.heading("size", text="Size")
        self.queued_tree.heading("status", text="Status")
        
        # Define columns
        self.queued_tree.column("path", width=500)
        self.queued_tree.column("size", width=100)
        self.queued_tree.column("status", width=150)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(queued_frame, orient=tk.VERTICAL, command=self.queued_tree.yview)
        self.queued_tree.configure(yscroll=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.queued_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=10)
        
        # Button to refresh the list
        ttk.Button(queued_frame, text="Refresh List", command=self.refresh_queued_files).pack(pady=5)

    def setup_omdb_queue_tab(self):
        """Setup the OMDB queue tab"""
        omdb_frame = ttk.Frame(self.notebook)
        self.notebook.add(omdb_frame, text="OMDB Queue")
        
        # Create a treeview for the OMDB queue
        columns = ("path", "status")
        self.omdb_tree = ttk.Treeview(omdb_frame, columns=columns, show='headings')
        
        # Define headings
        self.omdb_tree.heading("path", text="File Path")
        self.omdb_tree.heading("status", text="Status")
        
        # Define columns
        self.omdb_tree.column("path", width=650)
        self.omdb_tree.column("status", width=150)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(omdb_frame, orient=tk.VERTICAL, command=self.omdb_tree.yview)
        self.omdb_tree.configure(yscroll=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.omdb_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=10)
        
        # Button to refresh the list
        ttk.Button(omdb_frame, text="Refresh List", command=self.refresh_omdb_queue).pack(pady=5)

    def setup_suspicious_files_tab(self):
        """Setup the suspicious files tab"""
        suspicious_frame = ttk.Frame(self.notebook)
        self.notebook.add(suspicious_frame, text="Suspicious Files")
        
        # Create a treeview for suspicious files
        columns = ("path", "file_duration", "omdb_duration", "difference")
        self.suspicious_tree = ttk.Treeview(suspicious_frame, columns=columns, show='headings')
        
        # Define headings
        self.suspicious_tree.heading("path", text="File Path")
        self.suspicious_tree.heading("file_duration", text="File Duration")
        self.suspicious_tree.heading("omdb_duration", text="OMDB Duration")
        self.suspicious_tree.heading("difference", text="Difference")
        
        # Define columns
        self.suspicious_tree.column("path", width=500)
        self.suspicious_tree.column("file_duration", width=100)
        self.suspicious_tree.column("omdb_duration", width=100)
        self.suspicious_tree.column("difference", width=100)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(suspicious_frame, orient=tk.VERTICAL, command=self.suspicious_tree.yview)
        self.suspicious_tree.configure(yscroll=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.suspicious_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=10)
        
        # Button frame
        button_frame = ttk.Frame(suspicious_frame)
        button_frame.pack(pady=5)
        
        # Buttons
        ttk.Button(button_frame, text="Mark as Good", command=self.mark_suspicious_as_good).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh List", command=self.refresh_suspicious_files).pack(side=tk.LEFT, padx=5)

    def setup_good_files_tab(self):
        """Setup the good files tab"""
        good_frame = ttk.Frame(self.notebook)
        self.notebook.add(good_frame, text="Good Files")
        
        # Create a treeview for good files
        columns = ("path", "size", "duration", "video_codec", "hdr_type", "audio", "subtitles")
        self.good_tree = ttk.Treeview(good_frame, columns=columns, show='headings')
        
        # Define headings
        self.good_tree.heading("path", text="File Path")
        self.good_tree.heading("size", text="Size")
        self.good_tree.heading("duration", text="Duration")
        self.good_tree.heading("video_codec", text="Video Codec")
        self.good_tree.heading("hdr_type", text="HDR Type")
        self.good_tree.heading("audio", text="Audio")
        self.good_tree.heading("subtitles", text="Subtitles")
        
        # Define columns
        self.good_tree.column("path", width=300)
        self.good_tree.column("size", width=80)
        self.good_tree.column("duration", width=80)
        self.good_tree.column("video_codec", width=100)
        self.good_tree.column("hdr_type", width=80)
        self.good_tree.column("audio", width=150)
        self.good_tree.column("subtitles", width=150)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(good_frame, orient=tk.VERTICAL, command=self.good_tree.yview)
        self.good_tree.configure(yscroll=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.good_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=10)
        
        # Button to refresh the list
        ttk.Button(good_frame, text="Refresh List", command=self.refresh_good_files).pack(pady=5)

    def add_folder(self):
        """Add a folder to scan"""
        folder = filedialog.askdirectory()
        if folder:
            # Check if folder is already in the list
            if folder not in self.settings["scan_folders"]:
                self.settings["scan_folders"].append(folder)
                self.folders_listbox.insert(tk.END, folder)
                self.log(f"Added folder: {folder}")

    def remove_folder(self):
        """Remove selected folder from the list"""
        selection = self.folders_listbox.curselection()
        if selection:
            index = selection[0]
            folder = self.folders_listbox.get(index)
            self.settings["scan_folders"].remove(folder)
            self.folders_listbox.delete(index)
            self.log(f"Removed folder: {folder}")

    def save_settings_from_gui(self):
        """Save settings from GUI to settings object and file"""
        # Update API keys
        self.settings["omdb_api_keys"] = [entry_var.get() for entry_var in self.api_key_entries]
        
        # Update API keys status dictionary
        for key in self.settings["omdb_api_keys"]:
            if key and key not in self.api_keys_status:
                self.api_keys_status[key] = {
                    "blocked": False,
                    "cooldown_until": None,
                    "daily_calls": 0
                }
        
        # Update refresh interval
        self.settings["refresh_interval"] = self.refresh_interval_var.get()
        
        # Update verbose logging
        self.settings["verbose_logging"] = self.verbose_logging_var.get()
        
        # Save settings to file
        self.save_settings()
        
        # Log
        self.log("Settings saved")

    def log(self, message):
        """Add a message to the log queue"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")

    def ffprobe_log(self, message):
        """Add a message to the ffprobe log queue"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ffprobe_queue.put(f"[{timestamp}] {message}")

    def update_log(self):
        """Update the log text widget from the queue"""
        while True:
            try:
                message = self.log_queue.get(timeout=0.1)
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                print(f"Error updating log: {e}")

    def update_ffprobe_log(self):
        """Update the ffprobe log text widget from the queue"""
        while True:
            try:
                message = self.ffprobe_queue.get(timeout=0.1)
                self.ffprobe_text.config(state=tk.NORMAL)
                self.ffprobe_text.insert(tk.END, message + "\n")
                self.ffprobe_text.see(tk.END)
                self.ffprobe_text.config(state=tk.DISABLED)
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                print(f"Error updating ffprobe log: {e}")

    def clear_log(self):
        """Clear the log text widget"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log("Log cleared")

    def clear_ffprobe_log(self):
        """Clear the ffprobe log text widget"""
        self.ffprobe_text.config(state=tk.NORMAL)
        self.ffprobe_text.delete(1.0, tk.END)
        self.ffprobe_text.config(state=tk.DISABLED)
        self.ffprobe_log("FFProbe log cleared")

    def refresh_queued_files(self):
        """Refresh the queued files list"""
        # Clear the treeview
        for item in self.queued_tree.get_children():
            self.queued_tree.delete(item)
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get files with status "queued"
        cursor.execute("SELECT path, size, status FROM files WHERE status = 'queued'")
        files = cursor.fetchall()
        
        # Add files to the treeview
        for file in files:
            path, size, status = file
            size_mb = f"{size / (1024 * 1024):.2f} MB"
            self.queued_tree.insert("", tk.END, values=(path, size_mb, status))
        
        conn.close()
        self.log("Queued files list refreshed")

    def refresh_omdb_queue(self):
        """Refresh the OMDB queue list"""
        # Clear the treeview
        for item in self.omdb_tree.get_children():
            self.omdb_tree.delete(item)
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get files with status "awaiting_omdb"
        cursor.execute("SELECT path, status FROM files WHERE status = 'awaiting_omdb'")
        files = cursor.fetchall()
        
        # Add files to the treeview
        for file in files:
            path, status = file
            self.omdb_tree.insert("", tk.END, values=(path, status))
        
        conn.close()
        self.log("OMDB queue list refreshed")

    def refresh_suspicious_files(self):
        """Refresh the suspicious files list"""
        # Clear the treeview
        for item in self.suspicious_tree.get_children():
            self.suspicious_tree.delete(item)
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get files with status "suspicious"
        cursor.execute("SELECT path, duration, omdb_duration FROM files WHERE status = 'suspicious'")
        files = cursor.fetchall()
        
        # Add files to the treeview
        for file in files:
            path, duration, omdb_duration = file
            
            # Convert duration strings to minutes for comparison
            file_minutes = duration / 60 if duration else 0
            
            # Parse OMDB duration (format: "X h Y min" or "Y min")
            omdb_minutes = 0
            if omdb_duration:
                # Extract hours and minutes
                hours_match = re.search(r'(\d+)\s*h', omdb_duration)
                minutes_match = re.search(r'(\d+)\s*min', omdb_duration)
                
                hours = int(hours_match.group(1)) if hours_match else 0
                minutes = int(minutes_match.group(1)) if minutes_match else 0
                
                omdb_minutes = hours * 60 + minutes
            
            # Calculate difference
            difference = abs(file_minutes - omdb_minutes)
            
            # Format for display
            file_duration_str = f"{int(file_minutes // 60)}h {int(file_minutes % 60)}min" if file_minutes else "Unknown"
            difference_str = f"{int(difference)}min" if difference else "None"
            
            self.suspicious_tree.insert("", tk.END, values=(path, file_duration_str, omdb_duration, difference_str))
        
        conn.close()
        self.log("Suspicious files list refreshed")

    def refresh_good_files(self):
        """Refresh the good files list"""
        # Clear the treeview
        for item in self.good_tree.get_children():
            self.good_tree.delete(item)
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get files with status "good"
        cursor.execute("""
            SELECT path, size, duration, video_codec, hdr_type, audio_streams, subtitles
            FROM files WHERE status = 'good'
        """)
        files = cursor.fetchall()
        
        # Add files to the treeview
        for file in files:
            path, size, duration, video_codec, hdr_type, audio_streams, subtitles = file
            
            # Format size
            size_mb = f"{size / (1024 * 1024):.2f} MB" if size else "Unknown"
            
            # Format duration
            if duration:
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                seconds = int(duration % 60)
                duration_str = f"{hours}h {minutes}m {seconds}s"
            else:
                duration_str = "Unknown"
            
            self.good_tree.insert("", tk.END, values=(path, size_mb, duration_str, video_codec, hdr_type, audio_streams, subtitles))
        
        conn.close()
        self.log("Good files list refreshed")

    def mark_suspicious_as_good(self):
        """Mark selected suspicious file as good"""
        selection = self.suspicious_tree.selection()
        if not selection:
            self.log("No file selected")
            return
        
        # Get the path of the selected file
        item = self.suspicious_tree.item(selection[0])
        path = item['values'][0]
        
        # Update the status in the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE files SET status = 'good' WHERE path = ?", (path,))
        conn.commit()
        conn.close()
        
        # Remove from suspicious list and refresh lists
        self.suspicious_tree.delete(selection[0])
        self.refresh_good_files()
        self.log(f"Marked as good: {path}")

    def schedule_scan(self):
        """Schedule the scan to run at the specified interval"""
        interval_hours = self.settings["refresh_interval"]
        self.log(f"Scheduling scan to run every {interval_hours} hours")
        
        # Schedule the first scan immediately
        self.root.after(1000, self.start_scan)
        
        # Schedule subsequent scans
        def reschedule():
            self.start_scan()
            self.root.after(interval_hours * 60 * 60 * 1000, reschedule)
        
        self.root.after(interval_hours * 60 * 60 * 1000, reschedule)

    def start_scan(self):
        """Start the scanning process in a separate thread"""
        if self.scanning_active:
            self.log("Scan already in progress")
            return
        
        if not self.settings["scan_folders"]:
            self.log("No folders to scan")
            return
        
        # Update API key status from database
        self.update_api_key_status()
        
        # Check if all API keys are blocked
        active_keys = [key for key, status in self.api_keys_status.items() 
                      if key and not status["blocked"]]
        
        if not active_keys and any(self.settings["omdb_api_keys"]):
            self.log("All API keys are currently blocked, waiting for cooldown")
            return
        
        # Start the scan in a new thread
        self.scanning_active = True
        self.scan_thread = threading.Thread(target=self.run_scan)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        self.log("Scan started")

    def update_api_key_status(self):
        """Update API key status from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all API keys
        cursor.execute("SELECT key, blocked, cooldown_until, daily_calls FROM api_keys")
        keys = cursor.fetchall()
        
        for key, blocked, cooldown_until, daily_calls in keys:
            if key in self.api_keys_status:
                # Reset key if cooldown has passed
                if cooldown_until and datetime.now() > datetime.fromisoformat(cooldown_until):
                    self.api_keys_status[key] = {
                        "blocked": bool(blocked),
                        "cooldown_until": cooldown_until,
                        "daily_calls": daily_calls
                        "cooldown_until": None,
                        "daily_calls": 0
                    }
                    cursor.execute(
                        "UPDATE api_keys SET blocked = 0, cooldown_until = NULL, daily_calls = 0 WHERE key = ?",
                        (key,)
                    )
                else:
                    self.api_keys_status[key] = {
                        "blocked": bool(blocked),
                         "cooldown_until": cooldown_until,
                         "daily_calls": daily_calls
                    }
