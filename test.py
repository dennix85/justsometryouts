import sys
import os
import json
import time
import sqlite3
import subprocess
import datetime
from threading import Thread, Event
from queue import Queue
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QFileDialog,
    QTextEdit, QListWidget, QListWidgetItem, QCheckBox, QGroupBox, QSpinBox,
    QHeaderView, QSplitter, QComboBox, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MediaInfoExtractor:
    def __init__(self, db_path):
        self.db_path = db_path
        self.setup_database()
        
    def setup_database(self):
        # Create database if it doesn't exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create main media files table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            file_name TEXT,
            file_size INTEGER,
            duration REAL,
            file_type TEXT,
            last_modified TEXT,
            indexed_date TEXT
        )
        ''')
        
        # Create video streams table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER,
            codec TEXT,
            width INTEGER,
            height INTEGER,
            frame_rate TEXT,
            bit_rate INTEGER,
            FOREIGN KEY (media_id) REFERENCES media_files (id)
        )
        ''')
        
        # Create audio streams table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio_streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER,
            codec TEXT,
            channels INTEGER,
            sample_rate INTEGER,
            bit_rate INTEGER,
            FOREIGN KEY (media_id) REFERENCES media_files (id)
        )
        ''')
        
        # Create subtitle streams table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subtitle_streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER,
            codec TEXT,
            language TEXT,
            FOREIGN KEY (media_id) REFERENCES media_files (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def extract_media_info(self, file_path):
        try:
            # Run mediainfo in JSON format
            cmd = ['mediainfo', '--Output=JSON', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the JSON output
            media_info = json.loads(result.stdout)
            
            if 'media' not in media_info:
                return None
                
            # Extract basic file information
            file_info = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'file_type': None,
                'duration': None,
                'last_modified': datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                'indexed_date': datetime.datetime.now().isoformat(),
                'video_streams': [],
                'audio_streams': [],
                'subtitle_streams': []
            }
            
            # Process all tracks
            for track in media_info['media']['track']:
                track_type = track.get('@type', '').lower()
                
                if track_type == 'general':
                    file_info['file_type'] = track.get('FileExtension', None)
                    if 'Duration' in track:
                        file_info['duration'] = float(track['Duration'])
                        
                elif track_type == 'video':
                    video_stream = {
                        'codec': track.get('Format', None),
                        'width': int(track.get('Width', 0)) if 'Width' in track else None,
                        'height': int(track.get('Height', 0)) if 'Height' in track else None,
                        'frame_rate': track.get('FrameRate', None),
                        'bit_rate': int(track.get('BitRate', 0)) if 'BitRate' in track else None
                    }
                    file_info['video_streams'].append(video_stream)
                    
                elif track_type == 'audio':
                    audio_stream = {
                        'codec': track.get('Format', None),
                        'channels': int(track.get('Channels', 0)) if 'Channels' in track else None,
                        'sample_rate': int(track.get('SamplingRate', 0)) if 'SamplingRate' in track else None,
                        'bit_rate': int(track.get('BitRate', 0)) if 'BitRate' in track else None
                    }
                    file_info['audio_streams'].append(audio_stream)
                    
                elif track_type == 'text':
                    subtitle_stream = {
                        'codec': track.get('Format', None),
                        'language': track.get('Language', None)
                    }
                    file_info['subtitle_streams'].append(subtitle_stream)
                    
            return file_info
        except Exception as e:
            print(f"Error extracting media info from {file_path}: {str(e)}")
            return None
    
    def save_to_database(self, media_info):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert into media_files table
            cursor.execute('''
            INSERT OR REPLACE INTO media_files 
            (file_path, file_name, file_size, duration, file_type, last_modified, indexed_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                media_info['file_path'],
                media_info['file_name'],
                media_info['file_size'],
                media_info['duration'],
                media_info['file_type'],
                media_info['last_modified'],
                media_info['indexed_date']
            ))
            
            # Get the ID of the inserted media file
            if cursor.lastrowid:
                media_id = cursor.lastrowid
            else:
                # If the file already existed, get its ID
                cursor.execute('SELECT id FROM media_files WHERE file_path = ?', (media_info['file_path'],))
                media_id = cursor.fetchone()[0]
                
                # Delete existing stream records for this media
                cursor.execute('DELETE FROM video_streams WHERE media_id = ?', (media_id,))
                cursor.execute('DELETE FROM audio_streams WHERE media_id = ?', (media_id,))
                cursor.execute('DELETE FROM subtitle_streams WHERE media_id = ?', (media_id,))
            
            # Insert video streams
            for video in media_info['video_streams']:
                cursor.execute('''
                INSERT INTO video_streams (media_id, codec, width, height, frame_rate, bit_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    media_id,
                    video['codec'],
                    video['width'],
                    video['height'],
                    video['frame_rate'],
                    video['bit_rate']
                ))
            
            # Insert audio streams
            for audio in media_info['audio_streams']:
                cursor.execute('''
                INSERT INTO audio_streams (media_id, codec, channels, sample_rate, bit_rate)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    media_id,
                    audio['codec'],
                    audio['channels'],
                    audio['sample_rate'],
                    audio['bit_rate']
                ))
            
            # Insert subtitle streams
            for subtitle in media_info['subtitle_streams']:
                cursor.execute('''
                INSERT INTO subtitle_streams (media_id, codec, language)
                VALUES (?, ?, ?)
                ''', (
                    media_id,
                    subtitle['codec'],
                    subtitle['language']
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving media info to database: {str(e)}")
            return False

    def export_to_json(self, file_path, output_folder):
        try:
            # Get the media info from the database
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the main media file info
            cursor.execute('''
            SELECT * FROM media_files WHERE file_path = ?
            ''', (file_path,))
            media_file = cursor.fetchone()
            
            if not media_file:
                conn.close()
                return False
                
            media_id = media_file['id']
            media_info = dict(media_file)
            
            # Get video streams
            cursor.execute('SELECT * FROM video_streams WHERE media_id = ?', (media_id,))
            media_info['video_streams'] = [dict(row) for row in cursor.fetchall()]
            
            # Get audio streams
            cursor.execute('SELECT * FROM audio_streams WHERE media_id = ?', (media_id,))
            media_info['audio_streams'] = [dict(row) for row in cursor.fetchall()]
            
            # Get subtitle streams
            cursor.execute('SELECT * FROM subtitle_streams WHERE media_id = ?', (media_id,))
            media_info['subtitle_streams'] = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            # Create output path
            output_file = os.path.join(output_folder, f"{os.path.splitext(media_info['file_name'])[0]}.json")
            
            # Save to JSON file
            with open(output_file, 'w') as f:
                json.dump(media_info, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {str(e)}")
            return False

    def get_all_media_files(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT mf.*, 
                   COUNT(DISTINCT vs.id) as video_count, 
                   COUNT(DISTINCT as_id) as audio_count,
                   COUNT(DISTINCT ss.id) as subtitle_count
            FROM media_files mf
            LEFT JOIN video_streams vs ON mf.id = vs.media_id
            LEFT JOIN audio_streams as_id ON mf.id = as_id.media_id
            LEFT JOIN subtitle_streams ss ON mf.id = ss.media_id
            GROUP BY mf.id
            ORDER BY mf.file_name
            ''')
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            print(f"Error getting media files: {str(e)}")
            return []
            
    def get_stats(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            stats = {}
            
            # Get total media files count
            cursor.execute('SELECT COUNT(*) as count FROM media_files')
            stats['total_files'] = cursor.fetchone()['count']
            
            # Get video codec distribution
            cursor.execute('''
            SELECT codec, COUNT(*) as count 
            FROM video_streams 
            GROUP BY codec 
            ORDER BY count DESC
            ''')
            stats['video_codecs'] = [dict(row) for row in cursor.fetchall()]
            
            # Get audio codec distribution
            cursor.execute('''
            SELECT codec, COUNT(*) as count 
            FROM audio_streams 
            GROUP BY codec 
            ORDER BY count DESC
            ''')
            stats['audio_codecs'] = [dict(row) for row in cursor.fetchall()]
            
            # Get resolution distribution
            cursor.execute('''
            SELECT width || 'x' || height as resolution, COUNT(*) as count 
            FROM video_streams 
            GROUP BY resolution 
            ORDER BY count DESC
            ''')
            stats['resolutions'] = [dict(row) for row in cursor.fetchall()]
            
            # Get total size of all media
            cursor.execute('SELECT SUM(file_size) as total_size FROM media_files')
            total_bytes = cursor.fetchone()['total_size'] or 0
            stats['total_size'] = total_bytes
            
            conn.close()
            return stats
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return {}

class SignalEmitter(QObject):
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int, int)
    file_processed_signal = pyqtSignal(str)
    scan_complete_signal = pyqtSignal()

class MediaFileHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor
        
    def on_created(self, event):
        if not event.is_directory and self._is_media_file(event.src_path):
            self.monitor.queue_file(event.src_path)
            
    def on_modified(self, event):
        if not event.is_directory and self._is_media_file(event.src_path):
            self.monitor.queue_file(event.src_path)
    
    def _is_media_file(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()
        media_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', 
                            '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a']
        return extension in media_extensions

class MediaMonitor:
    def __init__(self, db_path, signal_emitter):
        self.db_path = db_path
        self.signals = signal_emitter
        self.extractor = MediaInfoExtractor(db_path)
        self.file_queue = Queue()
        self.processing_thread = None
        self.stop_event = Event()
        self.observers = []
        self.watch_roots = []
        self.exclude_dirs = []
        self.output_folder = ""
        self.use_realtime = True
        self.scan_interval = 3600  # Default 1 hour
        self.interval_timer = None
        
    def set_watch_roots(self, roots):
        self.watch_roots = roots
        
    def set_exclude_dirs(self, dirs):
        self.exclude_dirs = dirs
        
    def set_output_folder(self, folder):
        self.output_folder = folder
        
    def set_use_realtime(self, use_realtime):
        self.use_realtime = use_realtime
        
    def set_scan_interval(self, interval):
        self.scan_interval = interval
        
    def start_monitoring(self):
        self.stop_event.clear()
        
        # Start processing thread
        self.processing_thread = Thread(target=self._process_queue)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        if self.use_realtime:
            self._start_realtime_monitoring()
        else:
            self._start_interval_scanning()
        
        self.signals.log_signal.emit("INFO", "Media monitoring started")
            
    def stop_monitoring(self):
        self.stop_event.set()
        
        if self.interval_timer:
            self.interval_timer.stop()
            self.interval_timer = None
            
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers = []
        
        self.signals.log_signal.emit("INFO", "Media monitoring stopped")
        
    def pause_monitoring(self):
        if self.use_realtime:
            for observer in self.observers:
                observer.unschedule_all()
            self.observers = []
        elif self.interval_timer:
            self.interval_timer.stop()
            
        self.signals.log_signal.emit("INFO", "Media monitoring paused")
        
    def resume_monitoring(self):
        if self.use_realtime:
            self._start_realtime_monitoring()
        else:
            self._start_interval_scanning()
            
        self.signals.log_signal.emit("INFO", "Media monitoring resumed")
        
    def queue_file(self, file_path):
        # Check if file is in excluded directory
        for exclude_dir in self.exclude_dirs:
            if file_path.startswith(exclude_dir):
                return
                
        self.file_queue.put(file_path)
        
    def _start_realtime_monitoring(self):
        self.signals.log_signal.emit("INFO", "Starting real-time monitoring")
        
        for root in self.watch_roots:
            try:
                event_handler = MediaFileHandler(self)
                observer = Observer()
                observer.schedule(event_handler, root, recursive=True)
                observer.start()
                self.observers.append(observer)
                self.signals.log_signal.emit("INFO", f"Watching directory: {root}")
            except Exception as e:
                self.signals.log_signal.emit("ERROR", f"Failed to watch directory {root}: {str(e)}")
                
        # Also do an initial scan
        self._scan_directories()
        
    def _start_interval_scanning(self):
        self.signals.log_signal.emit("INFO", f"Starting interval scanning (every {self.scan_interval} seconds)")
        
        # Do an initial scan
        self._scan_directories()
        
        # Set up timer for future scans
        self.interval_timer = QTimer()
        self.interval_timer.timeout.connect(self._scan_directories)
        self.interval_timer.start(self.scan_interval * 1000)  # Convert to milliseconds
        
    def _scan_directories(self):
        self.signals.log_signal.emit("INFO", "Starting directory scan")
        Thread(target=self._scan_thread).start()
        
    def _scan_thread(self):
        file_count = 0
        for root_dir in self.watch_roots:
            try:
                for root, dirs, files in os.walk(root_dir):
                    # Check if this directory should be excluded
                    skip_dir = False
                    for exclude_dir in self.exclude_dirs:
                        if root.startswith(exclude_dir):
                            skip_dir = True
                            break
                            
                    if skip_dir:
                        continue
                        
                    for filename in files:
                        if self.stop_event.is_set():
                            return
                            
                        file_path = os.path.join(root, filename)
                        extension = os.path.splitext(filename)[1].lower()
                        
                        # Check if it's a media file
                        media_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', 
                                           '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a']
                        if extension in media_extensions:
                            self.queue_file(file_path)
                            file_count += 1
            except Exception as e:
                self.signals.log_signal.emit("ERROR", f"Error scanning directory {root_dir}: {str(e)}")
                
        self.signals.log_signal.emit("INFO", f"Scan complete. {file_count} media files found")
        
    def _process_queue(self):
        while not self.stop_event.is_set():
            try:
                # Get a file from the queue with a timeout
                try:
                    file_path = self.file_queue.get(timeout=1)
                except:
                    continue
                    
                # Process the file
                self.signals.log_signal.emit("INFO", f"Processing file: {file_path}")
                
                # Extract media info
                media_info = self.extractor.extract_media_info(file_path)
                if not media_info:
                    self.signals.log_signal.emit("ERROR", f"Failed to extract media info from: {file_path}")
                    self.file_queue.task_done()
                    continue
                    
                # Save to database
                if self.extractor.save_to_database(media_info):
                    self.signals.log_signal.emit("INFO", f"Saved media info to database: {file_path}")
                else:
                    self.signals.log_signal.emit("ERROR", f"Failed to save media info to database: {file_path}")
                    
                # Export to JSON if output folder is set
                if self.output_folder:
                    if self.extractor.export_to_json(file_path, self.output_folder):
                        self.signals.log_signal.emit("INFO", f"Exported JSON for: {file_path}")
                    else:
                        self.signals.log_signal.emit("ERROR", f"Failed to export JSON for: {file_path}")
                
                self.signals.file_processed_signal.emit(file_path)
                self.file_queue.task_done()
                
            except Exception as e:
                self.signals.log_signal.emit("ERROR", f"Error processing file: {str(e)}")
                
        self.signals.log_signal.emit("INFO", "File processing stopped")
        self.signals.scan_complete_signal.emit()

class MediaMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Monitor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up the data paths
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".mediamonitor")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.db_path = os.path.join(self.app_data_dir, "mediamonitor.db")
        self.config_path = os.path.join(self.app_data_dir, "config.json")
        
        # Set up signals
        self.signals = SignalEmitter()
        self.signals.log_signal.connect(self.add_log)
        self.signals.file_processed_signal.connect(self.update_progress)
        self.signals.scan_complete_signal.connect(self.scan_complete)
        
        # Set up media monitor
        self.monitor = MediaMonitor(self.db_path, self.signals)
        
        # Set up UI
        self.setup_ui()
        
        # Load settings
        self.load_settings()
        
        # Set up automatic save on close
        self.destroyed.connect(self.save_settings)
        
    def setup_ui(self):
        # Main central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Dashboard tab
        self.dashboard_tab = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        
        # Library tab
        self.library_tab = QWidget()
        self.setup_library_tab()
        self.tabs.addTab(self.library_tab, "Library")
        
        # Stats tab
        self.stats_tab = QWidget()
        self.setup_stats_tab()
        self.tabs.addTab(self.stats_tab, "Stats")
        
        # Config tab
        self.config_tab = QWidget()
        self.setup_config_tab()
        self.tabs.addTab(self.config_tab, "Configuration")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Set the main layout to central widget
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
    def setup_dashboard_tab(self):
        layout = QVBoxLayout()
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_monitoring)
        control_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_monitoring)
        self.pause_button.setEnabled(False)
        control_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        layout.addLayout(control_layout)
        
        # Status overview
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Not running")
        status_layout.addWidget(self.status_label)
        
        self.files_processed_label = QLabel("Files processed: 0")
        status_layout.addWidget(self.files_processed_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Log area
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group, stretch=1)
        
        self.dashboard_tab.setLayout(layout)
        
    def setup_library_tab(self):
        layout = QVBoxLayout()
        
        # Search and filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        
        self.search_field = QLineEdit()
        self.search_field.textChanged.connect(self.filter_library)
        filter_layout.addWidget(self.search_field)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_library)
        filter_layout.addWidget(self.refresh_button)
        
        layout.addLayout(filter_layout)
        
        # Media files table
        self.library_table = QTableWidget()
        self.library_table.setColumnCount(6)
        self.library_table.setHorizontalHeaderLabels(["Filename", "Type", "Size", "Duration", "Streams", "Last Modified"])
        self.library_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.library_table)
        
        self.library_tab.setLayout(layout)
        
    def setup_config_tab(self):
        layout = QVBoxLayout()
        
        # Root folders
        root_group = QGroupBox("Root Folders to Monitor")
        root_layout = QVBoxLayout()
        
        self.root_folders_list = QListWidget()
        root_layout.addWidget(self.root_folders_list)
        
        root_buttons_layout = QHBoxLayout()
        self.add_root_button = QPushButton("Add Folder")
        self.add_root_button.clicked.connect(self.add_root_folder)
        root_buttons_layout.addWidget(self.add_root_button)
        
        self.remove_root_button = QPushButton("Remove Folder")
        self.remove_root_button.clicked.connect(self.remove_root_folder)
        root_buttons_layout.addWidget(self.remove_root_button)
        
        root_layout.addLayout(root_buttons_layout)
        root_group.setLayout(root_layout)
        layout.addWidget(root_group)
        
        # Excluded folders
        exclude_group = QGroupBox("Excluded Folders")
        exclude_layout = QVBoxLayout()
        
        self.exclude_folders_list = QListWidget()
        exclude_layout.addWidget(self.exclude_folders_list)
        
        exclude_buttons_layout = QHBoxLayout()
        self.add_exclude_button = QPushButton("Add Folder")
        self.add_exclude_button.clicked.connect(self.add_exclude_folder)
        exclude_buttons_layout.addWidget(self.add_exclude_button)
        
        self.remove_exclude_button = QPushButton("Remove Folder")
        self.remove_exclude_button.clicked.connect(self.remove_exclude_folder)
        exclude_buttons_layout.addWidget(self.remove_exclude_button)
        
        exclude_layout.addLayout(exclude_buttons_layout)
        exclude_group.setLayout(exclude_layout)
        layout.addWidget(exclude_group)
        
        # Output folder
        output_group = QGroupBox("JSON Export Folder")
        output_layout = QHBoxLayout()
        
        self.output_folder_field = QLineEdit()
        self.output_folder_field.setReadOnly(True)
        output_layout.addWidget(self.output_folder_field)
        
        self.output_browse_button = QPushButton("Browse")
        self.output_browse_button.clicked.connect(self.set_output_folder)
        output_layout.addWidget(self.output_browse_button)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Monitoring settings
        monitoring_group = QGroupBox("Monitoring Settings")
        monitoring_layout = QVBoxLayout()
        
        # Real-time monitoring option
        self.realtime_checkbox = QCheckBox("Use real-time monitoring (if available)")
        self.realtime_checkbox.stateChanged.connect(self.toggle_realtime)
        monitoring_layout.addWidget(self.realtime_checkbox)
        
        # Interval settings
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Scan interval (seconds):"))
        
        self.interval_spinner = QSpinBox()
        self.interval_spinner.setRange(60, 86400)  # 1 minute to 24 hours
        self.interval_spinner.setValue(3600)  # Default 1 hour
        interval_layout.addWidget(self.interval_spinner)
        
        monitoring_layout.addLayout(interval_layout)
        monitoring_group.setLayout(monitoring_layout)
        layout.addWidget(monitoring_group)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_config_button = QPushButton("Save Configuration")
        self.save_config_button.clicked.connect(self.save_settings)
        save_layout.addWidget(self.save_config_button)
        
        layout.addLayout(save_layout)
        
        self.config_tab.setLayout(layout)
    
    def setup_stats_tab(self):
        layout = QVBoxLayout()
        
        # Overall stats
        stats_layout = QHBoxLayout()
        
        self.total_files_label = QLabel("Total Files: 0")
        stats_layout.addWidget(self.total_files_label)
        
        self.total_size_label = QLabel("Total Size: 0 MB")
        stats_layout.addWidget(self.total_size_label)
        
        layout.addLayout(stats_layout)
        
        # Charts area using matplotlib
        charts_layout = QHBoxLayout()
        
        # Video codec chart
        video_chart_group = QGroupBox("Video Codecs")
        video_chart_layout = QVBoxLayout()
        self.video_figure = Figure(figsize=(4, 3))
        self.video_canvas = FigureCanvas(self.video_figure)
        video_chart_layout.addWidget(self.video_canvas)
        video_chart_group.setLayout(video_chart_layout)
        charts_layout.addWidget(video_chart_group)
        
        # Audio codec chart
        audio_chart_group = QGroupBox("Audio Codecs")
        audio_chart_layout = QVBoxLayout()
        self.audio_figure = Figure(figsize=(4, 3))
        self.audio_canvas = FigureCanvas(self.audio_figure)
        audio_chart_layout.addWidget(self.audio_canvas)
        audio_chart_group.setLayout(audio_chart_layout)
        charts_layout.addWidget(audio_chart_group)
        
        # Resolution chart
        res_chart_group = QGroupBox("Resolutions")
        res_chart_layout = QVBoxLayout()
        self.res_figure = Figure(figsize=(4, 3))
        self.res_canvas = FigureCanvas(self.res_figure)
        res_chart_layout.addWidget(self.res_canvas)
        res_chart_group.setLayout(res_chart_layout)
        charts_layout.addWidget(res_chart_group)
        
        layout.addLayout(charts_layout)
        
        # Details tables
        tables_layout = QHBoxLayout()
        
        # Video codecs table
        video_group = QGroupBox("Video Codecs")
        video_layout = QVBoxLayout()
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(2)
        self.video_table.setHorizontalHeaderLabels(["Codec", "Count"])
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        video_layout.addWidget(self.video_table)
        video_group.setLayout(video_layout)
        tables_layout.addWidget(video_group)
        
        # Audio codecs table
        audio_group = QGroupBox("Audio Codecs")
        audio_layout = QVBoxLayout()
        self.audio_table = QTableWidget()
        self.audio_table.setColumnCount(2)
        self.audio_table.setHorizontalHeaderLabels(["Codec", "Count"])
        self.audio_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        audio_layout.addWidget(self.audio_table)
        audio_group.setLayout(audio_layout)
        tables_layout.addWidget(audio_group)
        
        # Resolutions table
        res_group = QGroupBox("Resolutions")
        res_layout = QVBoxLayout()
        self.res_table = QTableWidget()
        self.res_table.setColumnCount(2)
        self.res_table.setHorizontalHeaderLabels(["Resolution", "Count"])
        self.res_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        res_layout.addWidget(self.res_table)
        res_group.setLayout(res_layout)
        tables_layout.addWidget(res_group)
        
        layout.addLayout(tables_layout)
        
        # Refresh button for stats
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        self.refresh_stats_button = QPushButton("Refresh Stats")
        self.refresh_stats_button.clicked.connect(self.refresh_stats)
        refresh_layout.addWidget(self.refresh_stats_button)
        
        layout.addLayout(refresh_layout)
        
        self.stats_tab.setLayout(layout)
