#!/usr/bin/env python3
"""
Media Analyzer for Media Manager
Analyzes media files to extract metadata
"""

import os
import logging
import subprocess
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MediaAnalyzer:
    """Analyzes media files to extract metadata"""
    
    def __init__(self, db_manager, notification_service):
        """
        Initialize the media analyzer
        
        Args:
            db_manager (DatabaseManager): Database manager instance
            notification_service (NotificationService): Notification service instance
        """
        self.db_manager = db_manager
        self.notification_service = notification_service
        
        # Statistics
        self.stats = {
            'analyzed': 0,
            'errors': 0
        }
    
    def analyze_new_files(self):
        """
        Analyze all unanalyzed files in the database
        
        Returns:
            dict: Analysis statistics
        """
        logger.info("Starting analysis of new media files")
        
        unanalyzed_files = self.db_manager.get_unanalyzed_files()
        
        if not unanalyzed_files:
            logger.info("No new files to analyze")
            return self.stats
        
        total_files = len(unanalyzed_files)
        logger.info(f"Found {total_files} files to analyze")
        
        self.notification_service.send_notification(
            "Media Analyzer",
            f"Starting analysis of {total_files} new media files",
            "INFO"
        )
        
        for i, file_info in enumerate(unanalyzed_files):
            try:
                # Report progress periodically
                if (i + 1) % 10 == 0 or (i + 1) == total_files:
                    progress_pct = round((i + 1) / total_files * 100)
                    logger.info(f"Analysis progress: {i + 1}/{total_files} ({progress_pct}%)")
                    
                    if (i + 1) % 50 == 0:  # Don't notify too often
                        self.notification_service.send_notification(
                            "Media Analyzer",
                            f"Analysis progress: {progress_pct}% ({i + 1}/{total_files})",
                            "INFO"
                        )
                
                self._analyze_file(file_info)
                self.stats['analyzed'] += 1
            except Exception as e:
                logger.error(f"Error analyzing file {file_info['file_path']}: {e}")
                self.stats['errors'] += 1
        
        # Send notification with analysis results
        message = (
            f"Analysis completed: {self.stats['analyzed']} files analyzed, "
            f"{self.stats['errors']} errors"
        )
        
        logger.info(message)
        self.notification_service.send_notification("Media Analyzer", message, "INFO")
        
        return self.stats
    
    def _analyze_file(self, file_info):
        """
        Analyze a single media file
        
        Args:
            file_info (dict): Information about the media file
        """
        media_id = file_info['id']
        file_path = file_info['file_path']
        
        logger.debug(f"Analyzing file: {file_path}")
        
        try:
            # Extract media metadata using ffprobe
            metadata = self._extract_ffprobe_metadata(file_path)
            
            # Update database with metadata
            self.db_manager.update_media_metadata(media_id, metadata['format'])
            
            # Update audio streams info
            self.db_manager.update_audio_streams(media_id, metadata['audio_streams'])
            
            # Update subtitle streams info
            self.db_manager.update_subtitle_streams(media_id, metadata['subtitle_streams'])
            
            # Check for external subtitle files
            self._find_external_subtitles(media_id, file_path)
            
            logger.debug(f"Successfully analyzed file: {file_path}")
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            self.stats['errors'] += 1
            raise
    
    def _extract_ffprobe_metadata(self, file_path):
        """
        Extract metadata using ffprobe
        
        Args:
            file_path (str): Path to the media file
            
        Returns:
            dict: Extracted metadata
        """
        try:
            # FFprobe command to get all streams info in JSON format
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(result.stdout)
            
            # Extract relevant metadata
            format_info = probe_data.get('format', {})
            streams = probe_data.get('streams', [])
            
            # Initialize metadata structures
            metadata = {
                'format': {
                    'duration': self._safe_float(format_info.get('duration', 0)) * 1000,  # Convert to milliseconds
                    'width': None,
                    'height': None,
                    'aspect_ratio': None,
                    'video_codec': None,
                    'video_bitrate': self._safe_int(format_info.get('bit_rate')),
                    'frame_rate': None,
                    'hdr_type': None
                },
                'audio_streams': [],
                'subtitle_streams': []
            }
            
            # Process each stream
            for stream in streams:
                stream_type = stream.get('codec_type')
                
                if stream_type == 'video':
                    # Process video stream (main one only)
                    if metadata['format']['video_codec'] is None:
                        metadata['format']['video_codec'] = stream.get('codec_name')
                        metadata['format']['width'] = self._safe_int(stream.get('width'))
                        metadata['format']['height'] = self._safe_int(stream.get('height'))
                        
                        # Calculate aspect ratio
                        if metadata['format']['width'] and metadata['format']['height']:
                            w, h = metadata['format']['width'], metadata['format']['height']
                            metadata['format']['aspect_ratio'] = f"{w}:{h}"
                        
                        # Calculate frame rate
                        frame_rate = stream.get('r_frame_rate', '0/0')
                        if '/' in frame_rate:
                            num, den = map(int, frame_rate.split('/'))
                            if den != 0:
                                metadata['format']['frame_rate'] = num / den
                        
                        # Detect HDR type
                        metadata['format']['hdr_type'] = self._detect_hdr_type(stream)
                
                elif stream_type == 'audio':
                    # Process audio stream
                    audio_stream = {
                        'stream_index': stream.get('index'),
                        'codec': stream.get('codec_name'),
                        'channels': self._safe_int(stream.get('channels')),
                        'language': stream.get('tags', {}).get('language'),
                        'bitrate': self._safe_int(stream.get('bit_rate'))
                    }
                    metadata['audio_streams'].append(audio_stream)
                
                elif stream_type == 'subtitle':
                    # Process subtitle stream
                    subtitle_stream = {
                        'stream_index': stream.get('index'),
                        'codec': stream.get('codec_name'),
                        'language': stream.get('tags', {}).get('language'),
                        'is_external': False,
                        'external_path': None
                    }
                    metadata['subtitle_streams'].append(subtitle_stream)
            
            return metadata
        
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error for {file_path}: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting metadata for {file_path}: {e}")
            raise
    
    def _detect_hdr_type(self, stream):
        """
        Detect HDR type from stream data
        
        Args:
            stream (dict): Stream data from ffprobe
            
        Returns:
            str: HDR type or "SDR"
        """
        # Check for HDR10
        if stream.get('color_transfer') == 'smpte2084' or stream.get('color_primaries') == 'bt2020':
            return 'HDR10'
        
        # Check for HDR10+
        if stream.get('tags', {}).get('DURATION-eng') == 'HDR10+':
            return 'HDR10+'
        
        # Check for Dolby Vision
        side_data = stream.get('side_data_list', [])
        for data in side_data:
            if data.get('side_data_type') == 'DOVI configuration record':
                return 'Dolby Vision'
        
        # Check for HLG
        if stream.get('color_transfer') == 'arib-std-b67':
            return 'HLG'
        
        # Default to SDR
        return 'SDR'
    
    def _find_external_subtitles(self, media_id, file_path):
        """
        Find external subtitle files for a media file
        
        Args:
            media_id (int): ID of the media file
            file_path (str): Path to the media file
        """
        try:
            path = Path(file_path)
            dir_path = path.parent
            base_name = path.stem
            
            # List of subtitle extensions to look for
            subtitle_extensions = ['.srt', '.ass', '.ssa', '.sub', '.idx', '.vtt']
            external_subtitles = []
            
            # Find subtitle files with the same base name
            for ext in subtitle_extensions:
                for sub_file in dir_path.glob(f"{base_name}*{ext}"):
                    # Check if it's a language-specific subtitle: filename.en.srt
                    sub_path = str(sub_file)
                    language = None
                    
                    # Try to extract language code if present
                    parts = sub_file.stem.split('.')
                    if len(parts) > 1:
                        potential_lang = parts[-1].lower()
                        if len(potential_lang) == 2 or len(potential_lang) == 3:
                            language = potential_lang
                    
                    subtitle = {
                        'stream_index': None,  # External subtitles don't have stream index
                        'codec': ext[1:],  # Remove the leading dot
                        'language': language,
                        'is_external': True,
                        'external_path': sub_path
                    }
                    external_subtitles.append(subtitle)
            
            # If we found any external subtitles, add them to the database
            if external_subtitles:
                logger.debug(f"Found {len(external_subtitles)} external subtitle files for {file_path}")
                
                # Get existing subtitle streams
                cursor = self.db_manager.conn.cursor()
                cursor.execute("SELECT * FROM subtitle_streams WHERE media_id = ?", (media_id,))
                existing_subtitles = [dict(row) for row in cursor.fetchall()]
                
                # Combine existing and external subtitles
                all_subtitles = existing_subtitles + external_subtitles
                
                # Update subtitle streams
                self.db_manager.update_subtitle_streams(media_id, all_subtitles)
        
        except Exception as e:
            logger.error(f"Error finding external subtitles for {file_path}: {e}")
            # Not raising the exception here as this is a non-critical operation
    
    def _safe_int(self, value):
        """Safely convert value to int"""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value):
        """Safely convert value to float"""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
