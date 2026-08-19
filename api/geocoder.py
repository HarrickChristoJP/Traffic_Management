"""
====================================================
Geocoder Module

Converts place names into latitude and longitude
using OpenStreetMap Nominatim.
====================================================
"""

import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": "gmaps-qgis-integration/1.0"
}


def geocode_place(place_name):
    """
    Convert a place name/address into
    (latitude, longitude).
    """

    # Try the original search first
    search_queries = [
        place_name,
        place_name.replace(" Junction", ""),
        place_name.replace(", Chennai", ""),
        f"{place_name}, Tamil Nadu, India"
    ]

    for query in search_queries:

        print(f"\nSearching: {query}")

        params = {
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "in"
        }

        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        results = response.json()

        if results:

            latitude = float(results[0]["lat"])
            longitude = float(results[0]["lon"])

            print("Location found!")
            print("Matched place:", results[0]["display_name"])

            return latitude, longitude

    raise ValueError(
        f"Could not find location: {place_name}"
    )


# --------------------------------------------------
# Test the geocoder
# --------------------------------------------------

if __name__ == "__main__":

    place = input("Enter a place: ")

    latitude, longitude = geocode_place(place)

    print("\nCoordinates:")
    print("Latitude :", latitude)
    print("Longitude:", longitude)