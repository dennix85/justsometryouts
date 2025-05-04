#!/usr/bin/env python3
"""
Database Manager for Media Manager
Handles database operations and schema management
"""

import os
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for Media Manager"""
    
    def __init__(self, db_path):
        """Initialize the database manager"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            cursor = self.conn.cursor()
            
            # Media files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    file_extension TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    last_modified TIMESTAMP NOT NULL,
                    date_added TIMESTAMP NOT NULL,
                    last_scanned TIMESTAMP NOT NULL,
                    is_valid BOOLEAN DEFAULT NULL,
                    marked_as_valid BOOLEAN DEFAULT FALSE,
                    needs_review BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Media metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL,
                    duration INTEGER,
                    width INTEGER,
                    height INTEGER,
                    aspect_ratio TEXT,
                    video_codec TEXT,
                    video_bitrate INTEGER,
                    frame_rate REAL,
                    hdr_type TEXT,
                    FOREIGN KEY (media_id) REFERENCES media_files (id) ON DELETE CASCADE
                )
            ''')
            
            # Audio streams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_streams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL,
                    stream_index INTEGER NOT NULL,
                    codec TEXT,
                    channels INTEGER,
                    language TEXT,
                    bitrate INTEGER,
                    FOREIGN KEY (media_id) REFERENCES media_files (id) ON DELETE CASCADE
                )
            ''')
            
            # Subtitle streams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subtitle_streams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL,
                    stream_index INTEGER NOT NULL,
                    codec TEXT,
                    language TEXT,
                    is_external BOOLEAN DEFAULT FALSE,
                    external_path TEXT,
                    FOREIGN KEY (media_id) REFERENCES media_files (id) ON DELETE CASCADE
                )
            ''')
            
            # API metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL,
                    api_source TEXT NOT NULL,
                    source_id TEXT,
                    title TEXT,
                    year INTEGER,
                    expected_duration INTEGER,
                    imdb_id TEXT,
                    tmdb_id TEXT,
                    tvdb_id TEXT,
                    type TEXT,  -- movie or episode
                    season INTEGER,
                    episode INTEGER,
                    date_retrieved TIMESTAMP NOT NULL,
                    raw_data TEXT,
                    FOREIGN KEY (media_id) REFERENCES media_files (id) ON DELETE CASCADE
                )
            ''')
            
            # API rate limiting table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    daily_limit INTEGER NOT NULL,
                    calls_today INTEGER DEFAULT 0,
                    blocked_until TIMESTAMP,
                    last_reset TIMESTAMP
                )
            ''')
            
            # Commit the changes
            self.conn.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def add_media_file(self, file_info):
        """
        Add a new media file to the database
        
        Args:
            file_info (dict): Information about the media file
        
        Returns:
            int: ID of the inserted media file
        """
        try:
            cursor = self.conn.cursor()
            now = datetime.now()
            
            cursor.execute('''
                INSERT OR IGNORE INTO media_files (
                    file_path, file_name, file_extension, file_size, 
                    last_modified, date_added, last_scanned
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_info['file_path'],
                file_info['file_name'],
                file_info['file_extension'],
                file_info['file_size'],
                file_info['last_modified'],
                now,
                now
            ))
            
            self.conn.commit()
            return cursor.lastrowid if cursor.lastrowid else self.get_media_id_by_path(file_info['file_path'])
        except sqlite3.Error as e:
            logger.error(f"Error adding media file: {e}")
            self.conn.rollback()
            raise
    
    def get_media_id_by_path(self, file_path):
        """Get media ID by file path"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM media_files WHERE file_path = ?", (file_path,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting media ID: {e}")
            raise
    
    def update_media_metadata(self, media_id, metadata):
        """Update media metadata"""
        try:
            cursor = self.conn.cursor()
            
            # First check if metadata exists
            cursor.execute("SELECT id FROM media_metadata WHERE media_id = ?", (media_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE media_metadata SET
                    duration = ?, width = ?, height = ?, aspect_ratio = ?,
                    video_codec = ?, video_bitrate = ?, frame_rate = ?, hdr_type = ?
                    WHERE media_id = ?
                ''', (
                    metadata.get('duration'),
                    metadata.get('width'),
                    metadata.get('height'),
                    metadata.get('aspect_ratio'),
                    metadata.get('video_codec'),
                    metadata.get('video_bitrate'),
                    metadata.get('frame_rate'),
                    metadata.get('hdr_type'),
                    media_id
                ))
            else:
                cursor.execute('''
                    INSERT INTO media_metadata (
                        media_id, duration, width, height, aspect_ratio,
                        video_codec, video_bitrate, frame_rate, hdr_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    media_id,
                    metadata.get('duration'),
                    metadata.get('width'),
                    metadata.get('height'),
                    metadata.get('aspect_ratio'),
                    metadata.get('video_codec'),
                    metadata.get('video_bitrate'),
                    metadata.get('frame_rate'),
                    metadata.get('hdr_type')
                ))
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error updating media metadata: {e}")
            self.conn.rollback()
            raise
    
    def update_audio_streams(self, media_id, audio_streams):
        """Update audio streams for a media file"""
        try:
            cursor = self.conn.cursor()
            
            # First delete existing audio streams
            cursor.execute("DELETE FROM audio_streams WHERE media_id = ?", (media_id,))
            
            # Then insert new ones
            for stream in audio_streams:
                cursor.execute('''
                    INSERT INTO audio_streams (
                        media_id, stream_index, codec, channels, language, bitrate
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    media_id,
                    stream.get('stream_index'),
                    stream.get('codec'),
                    stream.get('channels'),
                    stream.get('language'),
                    stream.get('bitrate')
                ))
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error updating audio streams: {e}")
            self.conn.rollback()
            raise
    
    def update_subtitle_streams(self, media_id, subtitle_streams):
        """Update subtitle streams for a media file"""
        try:
            cursor = self.conn.cursor()
            
            # First delete existing subtitle streams
            cursor.execute("DELETE FROM subtitle_streams WHERE media_id = ?", (media_id,))
            
            # Then insert new ones
            for stream in subtitle_streams:
                cursor.execute('''
                    INSERT INTO subtitle_streams (
                        media_id, stream_index, codec, language, is_external, external_path
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    media_id,
                    stream.get('stream_index'),
                    stream.get('codec'),
                    stream.get('language'),
                    stream.get('is_external', False),
                    stream.get('external_path')
                ))
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error updating subtitle streams: {e}")
            self.conn.rollback()
            raise
    
    def update_api_metadata(self, media_id, api_source, api_data):
        """Update API metadata for a media file"""
        try:
            cursor = self.conn.cursor()
            now = datetime.now()
            
            # Check if metadata from this API source exists
            cursor.execute(
                "SELECT id FROM api_metadata WHERE media_id = ? AND api_source = ?", 
                (media_id, api_source)
            )
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE api_metadata SET
                    source_id = ?, title = ?, year = ?, expected_duration = ?,
                    imdb_id = ?, tmdb_id = ?, tvdb_id = ?, type = ?,
                    season = ?, episode = ?, date_retrieved = ?, raw_data = ?
                    WHERE media_id = ? AND api_source = ?
                ''', (
                    api_data.get('source_id'),
                    api_data.get('title'),
                    api_data.get('year'),
                    api_data.get('expected_duration'),
                    api_data.get('imdb_id'),
                    api_data.get('tmdb_id'),
                    api_data.get('tvdb_id'),
                    api_data.get('type'),
                    api_data.get('season'),
                    api_data.get('episode'),
                    now,
                    api_data.get('raw_data'),
                    media_id,
                    api_source
                ))
            else:
                cursor.execute('''
                    INSERT INTO api_metadata (
                        media_id, api_source, source_id, title, year, expected_duration,
                        imdb_id, tmdb_id, tvdb_id, type, season, episode, 
                        date_retrieved, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    media_id,
                    api_source,
                    api_data.get('source_id'),
                    api_data.get('title'),
                    api_data.get('year'),
                    api_data.get('expected_duration'),
                    api_data.get('imdb_id'),
                    api_data.get('tmdb_id'),
                    api_data.get('tvdb_id'),
                    api_data.get('type'),
                    api_data.get('season'),
                    api_data.get('episode'),
                    now,
                    api_data.get('raw_data')
                ))
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error updating API metadata: {e}")
            self.conn.rollback()
            raise
    
    def get_unanalyzed_files(self):
        """Get files that haven't been analyzed yet"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT mf.* FROM media_files mf
                LEFT JOIN media_metadata mm ON mf.id = mm.media_id
                WHERE mm.id IS NULL
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting unanalyzed files: {e}")
            raise
    
    def get_files_for_duration_validation(self):
        """Get files that need duration validation"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT mf.*, mm.duration FROM media_files mf
                JOIN media_metadata mm ON mf.id = mm.media_id
                LEFT JOIN api_metadata am ON mf.id = am.media_id
                WHERE mf.is_valid IS NULL 
                AND mf.marked_as_valid = FALSE
                AND am.id IS NULL
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting files for duration validation: {e}")
            raise
    
    def update_validation_status(self, media_id, is_valid, needs_review=False):
        """Update validation status of a media file"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE media_files
                SET is_valid = ?, needs_review = ?
                WHERE id = ?
            ''', (is_valid, needs_review, media_id))
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error updating validation status: {e}")
            self.conn.rollback()
            raise
    
    def mark_as_valid(self, media_id):
        """Mark a file as manually validated"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE media_files
                SET marked_as_valid = TRUE, needs_review = FALSE
                WHERE id = ?
            ''', (media_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error marking file as valid: {e}")
            self.conn.rollback()
            raise
    
    def get_files_needing_review(self):
        """Get files that need manual review"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT mf.*, mm.duration, am.expected_duration, am.title
                FROM media_files mf
                JOIN media_metadata mm ON mf.id = mm.media_id
                LEFT JOIN api_metadata am ON mf.id = am.media_id
                WHERE mf.needs_review = TRUE
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting files needing review: {e}")
            raise

    def update_api_rate_limit(self, api_name, api_key, calls=1):
        """Update API rate limit counters"""
        try:
            cursor = self.conn.cursor()
            now = datetime.now()
            today = datetime(now.year, now.month, now.day)
            
            # Check if this API key exists
            cursor.execute(
                "SELECT id, calls_today, last_reset FROM api_rate_limits WHERE api_name = ? AND api_key = ?",
                (api_name, api_key)
            )
            rate_limit = cursor.fetchone()
            
            if rate_limit:
                # Check if we should reset the counter (new day)
                if rate_limit['last_reset'] is None or datetime.fromisoformat(rate_limit['last_reset']).date() < today.date():
                    cursor.execute(
                        "UPDATE api_rate_limits SET calls_today = ?, last_reset = ? WHERE id = ?",
                        (calls, today, rate_limit['id'])
                    )
                else:
                    cursor.execute(
                        "UPDATE api_rate_limits SET calls_today = calls_today + ? WHERE id = ?", 
                        (calls, rate_limit['id'])
                    )
            else:
                # Get default daily limit for this API
                default_limits = {
                    'omdb': 1000,
                    'sonarr': 0,  # No limit
                    'radarr': 0,  # No limit
                }
                daily_limit = default_limits.get(api_name.lower(), 0)
                
                cursor.execute('''
                    INSERT INTO api_rate_limits (
                        api_name, api_key, daily_limit, calls_today, last_reset
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (api_name, api_key, daily_limit, calls, today))
            
            self.conn.commit()
            
            # Return updated call count
            cursor.execute(
                "SELECT calls_today FROM api_rate_limits WHERE api_name = ? AND api_key = ?",
                (api_name, api_key)
            )
            return cursor.fetchone()['calls_today']
        except sqlite3.Error as e:
            logger.error(f"Error updating API rate limit: {e}")
            self.conn.rollback()
            raise
    
    def block_api_key(self, api_name, api_key, hours=24):
        """Block an API key for a number of hours"""
        try:
            cursor = self.conn.cursor()
            now = datetime.now()
            blocked_until = datetime.now().replace(
                hour=now.hour + hours,
                minute=now.minute,
                second=now.second
            )
            
            cursor.execute(
                "UPDATE api_rate_limits SET blocked_until = ? WHERE api_name = ? AND api_key = ?",
                (blocked_until, api_name, api_key)
            )
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error blocking API key: {e}")
            self.conn.rollback()
            raise
    
    def get_available_api_key(self, api_name):
        """Get an available API key that's not blocked and has capacity"""
        try:
            cursor = self.conn.cursor()
            now = datetime.now()
            
            cursor.execute('''
                SELECT api_key, daily_limit, calls_today 
                FROM api_rate_limits
                WHERE api_name = ?
                AND (blocked_until IS NULL OR blocked_until < ?) 
                AND (daily_limit = 0 OR calls_today < daily_limit)
                ORDER BY calls_today ASC
                LIMIT 1
            ''', (api_name, now))
            
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting available API key: {e}")
            raise
    
    def get_media_stats(self):
        """Get media statistics for dashboard"""
        try:
            cursor = self.conn.cursor()
            
            # Total file count
            cursor.execute("SELECT COUNT(*) as total FROM media_files")
            total_count = cursor.fetchone()['total']
            
            # Valid files
            cursor.execute("SELECT COUNT(*) as valid FROM media_files WHERE is_valid = TRUE OR marked_as_valid = TRUE")
            valid_count = cursor.fetchone()['valid']
            
            # Invalid files
            cursor.execute("SELECT COUNT(*) as invalid FROM media_files WHERE is_valid = FALSE AND marked_as_valid = FALSE")
            invalid_count = cursor.fetchone()['invalid']
            
            # Files needing review
            cursor.execute("SELECT COUNT(*) as review FROM media_files WHERE needs_review = TRUE")
            review_count = cursor.fetchone()['review']
            
            # Not yet processed
            cursor.execute("SELECT COUNT(*) as unprocessed FROM media_files WHERE is_valid IS NULL AND marked_as_valid = FALSE")
            unprocessed_count = cursor.fetchone()['unprocessed']
            
            # Total size
            cursor.execute("SELECT SUM(file_size) as total_size FROM media_files")
            total_size = cursor.fetchone()['total_size'] or 0
            
            # Average duration
            cursor.execute("SELECT AVG(duration) as avg_duration FROM media_metadata")
            avg_duration = cursor.fetchone()['avg_duration'] or 0
            
            # Video codec distribution
            cursor.execute('''
                SELECT video_codec, COUNT(*) as count 
                FROM media_metadata 
                GROUP BY video_codec
                ORDER BY count DESC
            ''')
            video_codecs = [dict(row) for row in cursor.fetchall()]
            
            # HDR type distribution
            cursor.execute('''
                SELECT hdr_type, COUNT(*) as count 
                FROM media_metadata 
                GROUP BY hdr_type
                ORDER BY count DESC
            ''')
            hdr_types = [dict(row) for row in cursor.fetchall()]
            
            # Audio codec distribution
            cursor.execute('''
                SELECT codec, COUNT(*) as count 
                FROM audio_streams 
                GROUP BY codec
                ORDER BY count DESC
            ''')
            audio_codecs = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_count': total_count,
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'review_count': review_count,
                'unprocessed_count': unprocessed_count,
                'total_size': total_size,
                'avg_duration': avg_duration,
                'video_codecs': video_codecs,
                'hdr_types': hdr_types,
                'audio_codecs': audio_codecs
            }
        except sqlite3.Error as e:
            logger.error(f"Error getting media stats: {e}")
            raise
