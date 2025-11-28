"""
Geocoding service with caching
"""
import logging
import time
from typing import Optional, Tuple, Dict
import requests
from functools import lru_cache

logger = logging.getLogger(__name__)

# In-memory cache for geocoding results
_geocoding_cache: Dict[str, Tuple[float, float]] = {}


@lru_cache(maxsize=1000)
def geocode_location(location: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a location string to lat/lon coordinates
    
    Args:
        location: Location string (city/state/country)
    
    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    if not location or location == "unknown":
        return None
    
    # Check cache first
    if location in _geocoding_cache:
        return _geocoding_cache[location]
    
    try:
        # Use Nominatim (OpenStreetMap) geocoding service
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "VeritasAI/1.0"  # Required by Nominatim
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            
            # Cache result
            _geocoding_cache[location] = (lat, lon)
            
            logger.info(f"Geocoded '{location}' to ({lat}, {lon})")
            print(f"      ✅ Geocoded '{location}' → ({lat:.4f}, {lon:.4f})")
            return (lat, lon)
        
        logger.warning(f"Could not geocode location: {location}")
        print(f"      ⚠️  No geocoding results for '{location}'")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding request error: {e}")
        print(f"      ❌ Geocoding request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        print(f"      ❌ Geocoding error: {e}")
        return None
    finally:
        # Rate limiting: Nominatim allows 1 request per second
        time.sleep(1.1)


def geocode_location_cached(location: str) -> Optional[Tuple[float, float]]:
    """
    Geocode with in-memory cache (non-LRU, persistent)
    
    Args:
        location: Location string
    
    Returns:
        Tuple of (latitude, longitude) or None
    """
    if not location or location == "unknown":
        return None
    
    # Check in-memory cache
    if location in _geocoding_cache:
        cached_coords = _geocoding_cache[location]
        print(f"      💾 Using cached geocoding for '{location}' → ({cached_coords[0]:.4f}, {cached_coords[1]:.4f})")
        return cached_coords
    
    # Try geocoding
    result = geocode_location(location)
    
    if result:
        _geocoding_cache[location] = result
    
    return result

