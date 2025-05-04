import os
import logging
from pathlib import Path
from pymediainfo import MediaInfo
from enum import Enum

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('duration_validator')

class ValidatorResult(Enum):
    VALID = "valid"
    TOO_SHORT = "too_short"
    CORRUPTED = "corrupted"
    UNKNOWN = "unknown"

class DurationValidator:
    """
    Validates media files based on their duration to identify potentially corrupted
    or incomplete files.
    """
    
    def __init__(self, db_manager, min_video_duration_sec=60, min_audio_duration_sec=30):
        """
        Initialize the validator with minimum duration thresholds.
        
        Args:
            db_manager: Database manager instance for recording validation results
            min_video_duration_sec: Minimum acceptable duration for video files in seconds
            min_audio_duration_sec: Minimum acceptable duration for audio files in seconds
        """
        self.db_manager = db_manager
        self.min_video_duration_sec = min_video_duration_sec
        self.min_audio_duration_sec = min_audio_duration_sec
        
    def validate_file_duration(self, file_path):
        """
        Validates a media file's duration against minimum thresholds.
        
        Args:
            file_path: Path to the media file to validate
            
        Returns:
            A tuple of (ValidatorResult, duration_in_seconds)
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return ValidatorResult.UNKNOWN, 0
                
            media_info = MediaInfo.parse(file_path)
            
            # Get general track info
            general_track = None
            for track in media_info.tracks:
                if track.track_type == 'General':
                    general_track = track
                    break
            
            if not general_track:
                logger.warning(f"No general track found in {file_path}")
                return ValidatorResult.UNKNOWN, 0
                
            # Get duration
            duration_sec = getattr(general_track, 'duration', None)
            if duration_sec is None:
                logger.warning(f"Could not determine duration for {file_path}")
                return ValidatorResult.UNKNOWN, 0
                
            # Convert to seconds if needed
            if isinstance(duration_sec, str):
                try:
                    duration_sec = float(duration_sec) / 1000.0  # Convert from ms to seconds
                except ValueError:
                    logger.error(f"Invalid duration format for {file_path}: {duration_sec}")
                    return ValidatorResult.UNKNOWN, 0
            else:
                duration_sec = float(duration_sec) / 1000.0  # Convert from ms to seconds
                
            # Determine media type
            is_video = False
            for track in media_info.tracks:
                if track.track_type == 'Video':
                    is_video = True
                    break
            
            # Apply appropriate threshold
            min_duration = self.min_video_duration_sec if is_video else self.min_audio_duration_sec
            
            # Check if file meets minimum duration
            if duration_sec < min_duration:
                logger.warning(f"Media file too short: {file_path} ({duration_sec:.2f}s)")
                return ValidatorResult.TOO_SHORT, duration_sec
            
            # Check if file appears corrupted (0 duration but file exists)
            if duration_sec <= 0:
                logger.warning(f"Media file appears corrupted: {file_path}")
                return ValidatorResult.CORRUPTED, duration_sec
                
            logger.info(f"Media file is valid: {file_path} ({duration_sec:.2f}s)")
            return ValidatorResult.VALID, duration_sec
            
        except Exception as e:
            logger.error(f"Error validating {file_path}: {str(e)}")
            return ValidatorResult.UNKNOWN, 0
    
    def validate_and_record(self, file_path):
        """
        Validates a file and records the result in the database.
        
        Args:
            file_path: Path to the media file to validate
            
        Returns:
            ValidatorResult indicating the validation status
        """
        result, duration = self.validate_file_duration(file_path)
        
        # Record the result in the database
        try:
            file_info = {
                'path': str(file_path),
                'duration': duration,
                'duration_status': result.value
            }
            self.db_manager.update_file_info(file_path, file_info)
            logger.info(f"Updated duration info for {file_path}")
        except Exception as e:
            logger.error(f"Failed to record validation result for {file_path}: {str(e)}")
            
        return result
    
    def validate_batch(self, file_paths):
        """
        Validates a batch of files and returns summary statistics.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Dictionary with validation statistics
        """
        results = {
            ValidatorResult.VALID.value: 0,
            ValidatorResult.TOO_SHORT.value: 0,
            ValidatorResult.CORRUPTED.value: 0,
            ValidatorResult.UNKNOWN.value: 0,
            'total_files': len(file_paths),
            'problem_files': []
        }
        
        for file_path in file_paths:
            result = self.validate_and_record(file_path)
            results[result.value] += 1
            
            if result != ValidatorResult.VALID:
                results['problem_files'].append({
                    'path': str(file_path),
                    'issue': result.value
                })
                
        return results

    def set_min_duration(self, video_duration_sec=None, audio_duration_sec=None):
        """
        Updates the minimum duration thresholds.
        
        Args:
            video_duration_sec: New minimum video duration in seconds
            audio_duration_sec: New minimum audio duration in seconds
        """
        if video_duration_sec is not None:
            self.min_video_duration_sec = video_duration_sec
        if audio_duration_sec is not None:
            self.min_audio_duration_sec = audio_duration_sec
        
        logger.info(f"Updated minimum durations - Video: {self.min_video_duration_sec}s, Audio: {self.min_audio_duration_sec}s")
