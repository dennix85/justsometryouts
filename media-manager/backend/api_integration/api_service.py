#!/usr/bin/env python3
"""
API Service for Media Manager
Handles connections to external APIs like Sonarr, Radarr, and OMDB
"""

import os
import logging
import json
import time
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class APIService:
    """Service for interacting with external APIs"""
    
    def __init__(self, api_config, notification_service):
        """
        Initialize the API service
        
        Args:
            api_config (dict): API configuration
            notification_service (NotificationService): Notification service instance
        """
        self.api_config = api_config
        self.notification_service = notification_service
        self.sonarr_instances = self._initialize_instances('sonarr_instances')
        self.radarr_instances = self._initialize_instances('radarr_instances')
        self.omdb_api_keys = api_config.get('omdb_api_keys', [])
        
        # Statistics
        self.stats = {
            'sonarr_calls': 0,
            'radarr_calls': 0,
            'omdb_calls': 0,
            'errors': 0
        }
    
    def _initialize_instances(self, instance_type):
        """
        Initialize API instances from configuration
        
        Args:
            instance_type (str): Type of instance (sonarr_instances or radarr_instances)
            
        Returns:
            list: List of configured instances
        """
        instances = []
        
        for instance in self.api_config.get(instance_type, []):
            if 'url' in instance and 'api_key' in instance:
                instances.append({
                    'name': instance.get('name', f"{instance_type.split('_')[0]}_{len(instances) + 1}"),
                    'url': instance['url'].rstrip('/'),
                    'api_key': instance['api_key'],
                    'active': instance.get('active', True)
                })
        
        return instances
    
    def lookup_media_info(self, file_info, db_manager):
        """
        Look up media information from APIs
        
        Args:
            file_info (dict): Media file information
            db_manager (DatabaseManager): Database manager instance
            
        Returns:
            dict: Media information from APIs
        """
        media_id = file_info['id']
        file_path = file_info['file_path']
        file_name = file_info['file_name']
        
        logger.info(f"Looking up media info for: {file_name}")
        
        # First, try to get info from Sonarr/Radarr
        arr_result = self._lookup_from_arr_apps(file_path, file_name, db_manager)
        
        if arr_result:
            # We got info from Sonarr/Radarr, save it to database
            db_manager.update_api_metadata(media_id, arr_result['source'], arr_result)
            
            # If we have an IMDb ID or title/year, try to get more info from OMDB
            imdb_id = arr_result.get('imdb_id')
            title = arr_result.get('title')
            year = arr_result.get('year')
            
            if imdb_id or (title and year):
                try:
                    omdb_result = self._lookup_from_omdb(imdb_id, title, year, db_manager)
                    if omdb_result:
                        db_manager.update_api_metadata(media_id, 'omdb', omdb_result)
                        # If OMDB has expected duration, use it
                        if omdb_result.get('expected_duration'):
                            arr_result['expected_duration'] = omdb_result['expected_duration']
                except Exception as e:
                    logger.error(f"Error fetching OMDB data for {file_name}: {e}")
                    self.stats['errors'] += 1
            
            return arr_result
        
        # If we didn't get info from Sonarr/Radarr, try to guess from filename
        # This is very basic and will need to be improved
        guess = self._guess_info_from_filename(file_name)
        
        if guess.get('title'):
            try:
                omdb_result = self._lookup_from_omdb(None, guess.get('title'), guess.get('year'), db_manager)
                if omdb_result:
                    db_manager.update_api_metadata(media_id, 'omdb', omdb_result)
                    return omdb_result
            except Exception as e:
                logger.error(f"Error fetching OMDB data for {file_name}: {e}")
                self.stats['errors'] += 1
        
        # Couldn't find information
        logger.warning(f"Could not find media info for: {file_name}")
        return None
    
    def _lookup_from_arr_apps(self, file_path, file_name, db_manager):
        """
        Look up media information from Sonarr and Radarr
        
        Args:
            file_path (str): Path to the media file
            file_name (str): Name of the media file
            db_manager (DatabaseManager): Database manager instance
            
        Returns:
            dict: Media information or None if not found
        """
        # Try Sonarr first
        for instance in self.sonarr_instances:
            if not instance['active']:
                continue
            
            try:
                result = self._query_sonarr(instance, file_path, db_manager)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error querying Sonarr instance {instance['name']}: {e}")
                self.stats['errors'] += 1
        
        # Then try Radarr
        for instance in self.radarr_instances:
            if not instance['active']:
                continue
            
            try:
                result = self._query_radarr(instance, file_path, db_manager)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error querying Radarr instance {instance['name']}: {e}")
                self.stats['errors'] += 1
        
        return None
    
    def _query_sonarr(self, instance, file_path, db_manager):
        """
        Query Sonarr API for media information
        
        Args:
            instance (dict): Sonarr instance configuration
            file_path (str): Path to the media file
            db_manager (DatabaseManager): Database manager instance
            
        Returns:
            dict: Media information or None if not found
        """
        # Update call counter
        self.stats['sonarr_calls'] += 1
        db_manager.update_api_rate_limit('sonarr', instance['api_key'])
        
        # First try to lookup by file path
        headers = {
            'X-Api-Key': instance['api_key'],
            'Content-Type': 'application/json'
        }
        
        # Sonarr might have the file registered, so check
        endpoint = f"{instance['url']}/api/v3/episodefile/lookup"
        params = {'path': file_path}
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data:
                # Found episode file info in Sonarr
                episode_id = data[0].get('episodeId')
                
                if episode_id:
                    # Get detailed episode info
                    episode_endpoint = f"{instance['url']}/api/v3/episode/{episode_id}"
                    episode_response = requests.get(episode_endpoint, headers=headers)
                    episode_response.raise_for_status()
                    episode_data = episode_response.json()
                    
                    # Get series info
                    series_id = episode_data.get('seriesId')
                    series_endpoint = f"{instance['url']}/api/v3/series/{series_id}"
                    series_response = requests.get(series_endpoint, headers=headers)
                    series_response.raise_for_status()
                    series_data = series_response.json()
                    
                    # Compile the information
                    return {
                        'source': 'sonarr',
                        'source_id': str(episode_id),
                        'title': series_data.get('title'),
                        'year': series_data.get('year'),
                        'expected_duration': episode_data.get('episodeFile', {}).get('runtime') * 60 * 1000 if episode_data.get('episodeFile', {}).get('runtime') else None,
                        'imdb_id': series_data.get('imdbId'),
                        'tvdb_id': series_data.get('tvdbId'),
                        'type': 'episode',
                        'season': episode_data.get('seasonNumber'),
                        'episode': episode_data.get('episodeNumber'),
                        'raw_data': json.dumps({
                            'episode': episode_data,
                            'series': series_data
                        })
                    }
        except requests.RequestException as e:
            logger.error(f"Sonarr API error: {e}")
            
        return None
    
    def _query_radarr(self, instance, file_path, db_manager):
        """
        Query Radarr API for media information
        
        Args:
            instance (dict): Radarr instance configuration
            file_path (str): Path to the media file
            db_manager (DatabaseManager): Database manager instance
            
        Returns:
            dict: Media information or None if not found
        """
        # Update call counter
        self.stats['radarr_calls'] += 1
        db_manager.update_api_rate_limit('radarr', instance['api_key'])
        
        headers = {
            'X-Api-Key': instance['api_key'],
            'Content-Type': 'application/json'
        }
        
        # Radarr might have the file registered, so check
        endpoint = f"{instance['url']}/api/v3/moviefile/lookup"
        params = {'path': file_path}
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data:
                # Found movie file info in Radarr
                movie_id = data[0].get('movieId')
                
                if movie_id:
                    # Get detailed movie info
                    movie_endpoint = f"{instance['url']}/api/v3/movie/{movie_id}"
                    movie_response = requests.get(movie_endpoint, headers=headers)
                    movie_response.raise_for_status()
                    movie_data = movie_response.json()
                    
                    # Compile the information
                    return {
                        'source': 'radarr',
                        'source_id': str(movie_id),
                        'title': movie_data.get('title'),
                        'year': movie_data.get('year'),
                        'expected_duration': movie_data.get('runtime') * 60 * 1000 if movie_data.get('runtime') else None,
                        'imdb_id': movie_data.get('imdbId'),
                        'tmdb_id': movie_data.get('tmdbId'),
                        'type': 'movie',
                        'raw_data': json.dumps(movie_data)
                    }
        except requests.RequestException as e:
            logger.error(f"Radarr API error: {e}")
            
        return None
    
    def _lookup_from_omdb(self, imdb_id, title, year, db_manager):
        """
        Look up media information from OMDB API
        
        Args:
            imdb_id (str): IMDb ID
            title (str): Title of the media
            year (int): Year of release
            db_manager (DatabaseManager): Database manager instance
            
        Returns:
            dict: Media information or None if not found
        """
        if not self.omdb_api_keys:
            logger.warning("No OMDB API key configured")
            return None
        
        # Try to get an available API key
        api_key_info = db_manager.get_available_api_key('omdb')
        
        if not api_key_info:
            logger.warning("No available OMDB API key (all blocked or at limit)")
            return None
        
        api_key = api_key_info['api_key']
        
        # Construct query parameters
        params = {'apikey': api_key}
        
        if imdb_id:
            params['i'] = imdb_id
        elif title:
            params['t'] = title
            if year:
                params['y'] = year
        else:
            return None
            
        # Make the request
        try:
            self.stats['omdb_calls'] += 1
            call_count = db_manager.update_api_rate_limit('omdb', api_key)
            
            response = requests.get('http://www.omdbapi.com/', params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('Response') == 'True':
                # Check remaining calls
                if call_count >= api_key_info['daily_limit'] and api_key_info['daily_limit'] > 0:
                    logger.warning(f"OMDB API key {api_key} reached daily limit")
                    self.notification_service.send_notification(
                        "API Service",
                        f"OMDB API key {api_key} reached daily limit",
                        "WARNING"
                    )
                    db_manager.block_api_key('omdb', api_key)
                
                # Extract runtime from string like "120 min" to minutes
                runtime_min = None
                if 'Runtime' in data:
                    runtime_str = data['Runtime']
                    try:
                        runtime_min = int(runtime_str.split()[0])
                    except (ValueError, IndexError):
                        pass
                
                # Convert minutes to milliseconds if available
                expected_duration = runtime_min * 60 * 1000 if runtime_min else None
                
                # Determine if this is a movie or series
                media_type = data.get('Type', 'movie')
                
                # Extract season/episode for series
                season = None
                episode = None
                if media_type == 'series' and 'Season' in data:
                    try:
                        season = int(data['Season'])
                    except ValueError:
                        pass
                if media_type == 'series' and 'Episode' in data:
                    try:
                        episode = int(data['Episode'])
                    except ValueError:
                        pass
                
                # Compile the information
                return {
                    'source': 'omdb',
                    'source_id': data.get('imdbID'),
                    'title': data.get('Title'),
                    'year': int(data.get('Year', 0)) if data.get('Year', '').isdigit() else None,
                    'expected_duration': expected_duration,
                    'imdb_id': data.get('imdbID'),
                    'type': media_type,
                    'season': season,
                    'episode': episode,
                    'raw_data': json.dumps(data)
                }
            else:
                logger.warning(f"OMDB API returned no results: {data.get('Error', 'Unknown error')}")
                
        except requests.RequestException as e:
            logger.error(f"OMDB API error: {e}")
            self.stats['errors'] += 1
            
        return None
    
    def _guess_info_from_filename(self, file_name):
        """
        Try to guess media information from filename
        
        Args:
            file_name (str): Name of the media file
            
        Returns:
            dict: Guessed media information
        """
        # Stripping file extension
        name_without_ext = os.path.splitext(file_name)[0]
        
        # Very basic pattern matching for movies: "Title (Year)"
        # This needs to be improved with better regex patterns
        import re
        movie_pattern = re.compile(r'^(.*?)\s*[\(\[\{](\d{4})[\)\]\}]')
        match = movie_pattern.match(name_without_ext)
        
        if match:
            title = match.group(1).strip()
            year = int(match.group(2))
            return {
                'title': title,
                'year': year,
                'type': 'movie'
            }
        
        # Try to match TV shows: "Show Name S01E01" or "Show Name 1x01"
        tv_pattern = re.compile(r'^(.*?)\s*[Ss](\d{1,2})[Ee](\d{1,2})|(\d{1,2})[Xx](\d{1,2})')
        match = tv_pattern.search(name_without_ext)
        
        if match:
            if match.group(1):  # S01E01 format
                title = match.group(1).strip()
                season = int(match.group(2))
                episode = int(match.group(3))
            else:  # 1x01 format
                title = name_without_ext[:match.start()].strip()
                season = int(match.group(4))
                episode = int(match.group(5))
                
            return {
                'title': title,
                'season': season,
                'episode': episode,
                'type': 'episode'
            }
        
        # If all else fails, just use the filename as title
        return {
            'title': name_without_ext.replace('.', ' ').strip(),
            'type': 'unknown'
        }
    
    def get_stats(self):
        """
        Get API service statistics
        
        Returns:
            dict: API service statistics
        """
        return self.stats
    
    def test_connection(self, notify=True):
        """
        Test connections to configured APIs
        
        Args:
            notify (bool): Whether to send notifications for connection status
            
        Returns:
            dict: Connection test results
        """
        results = {
            'sonarr': [],
            'radarr': [],
            'omdb': []
        }
        
        # Test Sonarr instances
        for instance in self.sonarr_instances:
            if not instance['active']:
                continue
                
            result = {
                'name': instance['name'],
                'url': instance['url'],
                'status': 'error',
                'message': ''
            }
            
            try:
                headers = {
                    'X-Api-Key': instance['api_key'],
                    'Content-Type': 'application/json'
                }
                
                endpoint = f"{instance['url']}/api/v3/system/status"
                response = requests.get(endpoint, headers=headers, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                result['status'] = 'success'
                result['message'] = f"Connected to Sonarr {data.get('version', 'unknown version')}"
                
                if notify:
                    self.notification_service.send_notification(
                        "API Service",
                        f"Successfully connected to Sonarr instance {instance['name']}",
                        "INFO"
                    )
                
            except Exception as e:
                result['message'] = str(e)
                
                if notify:
                    self.notification_service.send_notification(
                        "API Service",
                        f"Failed to connect to Sonarr instance {instance['name']}: {e}",
                        "ERROR"
                    )
            
            results['sonarr'].append(result)
        
        # Test Radarr instances
        for instance in self.radarr_instances:
            if not instance['active']:
                continue
                
            result = {
                'name': instance['name'],
                'url': instance['url'],
                'status': 'error',
                'message': ''
            }
            
            try:
                headers = {
                    'X-Api-Key': instance['api_key'],
                    'Content-Type': 'application/json'
                }
                
                endpoint = f"{instance['url']}/api/v3/system/status"
                response = requests.get(endpoint, headers=headers, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                result['status'] = 'success'
                result['message'] = f"Connected to Radarr {data.get('version', 'unknown version')}"
                
                if notify:
                    self.notification_service.send_notification(
                        "API Service",
                        f"Successfully connected to Radarr instance {instance['name']}",
                        "INFO"
                    )
                
            except Exception as e:
                result['message'] = str(e)
                
                if notify:
                    self.notification_service.send_notification(
                        "API Service",
                        f"Failed to connect to Radarr instance {instance['name']}: {e}",
                        "ERROR"
                    )
            
            results['radarr'].append(result)
        
        # Test OMDB API
        for i, api_key in enumerate(self.omdb_api_keys):
            result = {
                'name': f"OMDB Key {i+1}",
                'status': 'error',
                'message': ''
            }
            
            try:
                params = {
                    'apikey': api_key,
                    'i': 'tt0111161'  # Test with The Shawshank Redemption
                }
                
                response = requests.get('http://www.omdbapi.com/', params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('Response') == 'True':
                    result['status'] = 'success'
                    result['message'] = f"OMDB API key validated successfully"
                    
                    if notify:
                        self.notification_service.send_notification(
                            "API Service",
                            f"Successfully validated OMDB API key {i+1}",
                            "INFO"
                        )
                else:
                    result['message'] = data.get('Error', 'Unknown error')
                    
                    if notify:
                        self.notification_service.send_notification(
                            "API Service",
                            f"OMDB API key {i+1} validation failed: {data.get('Error', 'Unknown error')}",
                            "ERROR"
                        )
            
            except Exception as e:
                result['message'] = str(e)
                
                if notify:
                    self.notification_service.send_notification(
                        "API Service",
                        f"Failed to validate OMDB API key {i+1}: {e}",
                        "ERROR"
                    )
            
            results['omdb'].append(result)
        
        return results
