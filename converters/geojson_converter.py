"""
====================================================
GeoJSON Converter

Responsible for converting OSRM JSON
into a GeoJSON file that QGIS can read.
====================================================
"""
import json


def create_route_geojson(route_json, output_file):
    """
    Convert all OSRM routes into a GeoJSON file.

    Each route returned by OSRM becomes
    a separate LineString feature.
    """

    features = []

    # Get all routes returned by OSRM
    routes = route_json["routes"]

    print(f"\nConverting {len(routes)} routes to GeoJSON...")

    for index, route in enumerate(routes):

        # Get route coordinates
        coordinates = route["geometry"]["coordinates"]

        # Give each route a name
        if index == 0:
            route_name = "Primary Route"
        else:
            route_name = f"Alternative Route {index}"

        # Create GeoJSON feature
        feature = {
            "type": "Feature",

            "properties": {
                "route_name": route_name,
                "route_number": index + 1,
                "distance_m": route["distance"],
                "duration_sec": route["duration"]
            },

            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            }
        }

        features.append(feature)

        print(
            f"Route {index + 1}: "
            f"{route['distance'] / 1000:.2f} km, "
            f"{route['duration'] / 60:.1f} min"
        )

    # Build final GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # Save GeoJSON
    with open(output_file, "w") as file:
        json.dump(geojson, file, indent=4)

    print("\nGeoJSON created successfully!")
    print(output_file)
def create_emergency_geojson(
    route_data,
    analyzed_routes,
    selected_route_number,
    output_file
):
    """
    Create a GeoJSON file containing routes
    together with emergency-analysis information.
    """

    features = []

    # Go through every OSRM route
    for index, route in enumerate(route_data["routes"]):

        # Get the corresponding analysis
        analysis = analyzed_routes[index]

        route_number = index + 1

        # Route name
        if route_number == 1:
            route_name = "Primary Route"
        else:
            route_name = f"Alternative Route {index}"

        # Check whether this route was selected
        selected = (
            route_number == selected_route_number
        )

        # Create GeoJSON feature
        feature = {

            "type": "Feature",

            "properties": {

                "route_name": route_name,

                "route_number": route_number,

                "distance_km": round(
                    route["distance"] / 1000,
                    2
                ),

                "duration_min": round(
                    route["duration"] / 60,
                    1
                ),

                "expressway_pct": analysis[
                    "expressway_percentage"
                ],

                "blocked": analysis[
                    "blocked"
                ],

                "blocked_roads": ", ".join(
                    analysis["blocked_roads"]
                ),

                "emergency_score": analysis.get(
                    "emergency_score",
                    None
                ),

                "selected": selected
            },

            "geometry": {

                "type": "LineString",

                "coordinates":
                    route["geometry"]["coordinates"]
            }
        }

        features.append(feature)

    # Complete GeoJSON
    geojson = {

        "type": "FeatureCollection",

        "features": features
    }

    # Save file
    with open(output_file, "w") as file:

        json.dump(
            geojson,
            file,
            indent=4
        )

    print("\nEmergency GeoJSON created successfully!")
    print(output_file)