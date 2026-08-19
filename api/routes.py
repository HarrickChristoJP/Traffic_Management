"""
====================================================
Routes API Module
Responsible for communicating with the OSRM Routing API.
This file should ONLY fetch route data.
====================================================
"""

# Import the requests library to send HTTP requests
import requests

# Import configuration values from config.py
from config import OSRM_BASE_URL


def get_route(origin, destination):
    """
    Fetch driving routes between two coordinates.

    Parameters:
        origin (tuple): (latitude, longitude)
        destination (tuple): (latitude, longitude)

    Returns:
        dict: JSON response from OSRM.
    """

    # Extract latitude and longitude
    origin_lat, origin_lon = origin
    dest_lat, dest_lon = destination

    # Build OSRM URL
    url = (
        f"{OSRM_BASE_URL}/route/v1/driving/"
        f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        "?overview=full"
        "&geometries=geojson"
        "&alternatives=true"
        "&steps=true"
        "&annotations=true"
    )

    # Send request
    response = requests.get(url, timeout=10)

    # Raise an error if the API request failed
    response.raise_for_status()

    # Convert response to Python dictionary
    return response.json()