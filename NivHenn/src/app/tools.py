"""Optional helper tools for agents (stubs for future extensions)."""
from typing import Optional


def geocode_address(address: str) -> Optional[dict]:
    """
    Geocode an address to lat/lng (stub).
    
    Future: Integrate with Google Maps, Mapbox, or similar API.
    
    Args:
        address: Street address to geocode
    
    Returns:
        Dict with lat, lng, or None if unavailable
    """
    # Stub implementation - return None for now
    # Future: Implement actual geocoding
    return None


def get_walk_score(lat: float, lng: float) -> Optional[int]:
    """
    Get walk score for a location (stub).
    
    Future: Integrate with Walk Score API.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Walk score (0-100) or None
    """
    # Stub implementation
    return None


def get_transit_score(lat: float, lng: float) -> Optional[int]:
    """
    Get transit score for a location (stub).
    
    Future: Integrate with Walk Score API.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Transit score (0-100) or None
    """
    # Stub implementation
    return None


def search_news(location: str, days_back: int = 30) -> list[dict]:
    """
    Search news for a location (stub).
    
    Future: Integrate with News API or similar.
    
    Args:
        location: City or area to search
        days_back: Days to look back
    
    Returns:
        List of news articles
    """
    # Stub implementation
    return []


def search_reddit(location: str, subreddit: str = "RealEstate") -> list[dict]:
    """
    Search Reddit for location mentions (stub).
    
    Future: Integrate with Reddit API.
    
    Args:
        location: Location to search for
        subreddit: Subreddit to search
    
    Returns:
        List of relevant posts
    """
    # Stub implementation
    return []


def get_demographics(city: str, state: str) -> Optional[dict]:
    """
    Get demographic data for a location (stub).
    
    Future: Integrate with Census API or similar.
    
    Args:
        city: City name
        state: State code
    
    Returns:
        Dict with population, income, etc., or None
    """
    # Stub implementation
    return None


def get_crime_data(city: str, state: str) -> Optional[dict]:
    """
    Get crime statistics (stub).
    
    Future: Integrate with FBI Crime Data API or local police APIs.
    
    Args:
        city: City name
        state: State code
    
    Returns:
        Dict with crime stats or None
    """
    # Stub implementation
    return None
