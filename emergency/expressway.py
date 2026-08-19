"""
====================================================
Expressway Detection Module

Analyzes the actual road segments returned by OSRM
and determines how much of a route uses
expressway/high-speed roads.

This is a prototype classification based on
OpenStreetMap/OSRM road names and references.

====================================================
"""


# --------------------------------------------------
# Road names that clearly indicate expressways
# --------------------------------------------------

EXPRESSWAY_KEYWORDS = [
    "expressway",
    "motorway"
]


def is_expressway(road_name, road_ref=None):
    """
    Determine whether a road should be classified
    as an expressway/high-speed road.

    Parameters
    ----------
    road_name : str
        Name of the road.

    road_ref : str
        Road reference such as SH49A, NH32, etc.

    Returns
    -------
    bool
        True if the road is classified as expressway.
    """

    # Handle missing values
    road_name = road_name or ""
    road_ref = road_ref or ""

    # Convert to lowercase for comparison
    road_name = road_name.lower()
    road_ref = road_ref.lower()

    # Check road name
    for keyword in EXPRESSWAY_KEYWORDS:

        if keyword in road_name:
            return True

    # We deliberately do NOT automatically classify
    # every NH/SH road as an expressway.
    #
    # Example:
    # NH32 does not automatically mean expressway.
    #
    # This avoids incorrectly labeling normal highways.

    return False


def analyze_route(route):
    """
    Analyze all road segments in an OSRM route.

    Parameters
    ----------
    route : dict
        One route from the OSRM response.

    Returns
    -------
    dict
        Expressway analysis information.
    """

    total_distance = route["distance"]

    expressway_distance = 0

    road_segments = []

    # ----------------------------------------------
    # Go through every leg
    # ----------------------------------------------

    for leg in route["legs"]:

        # ------------------------------------------
        # Go through every road step
        # ------------------------------------------

        for step in leg["steps"]:

            road_name = step.get("name", "")
            road_ref = step.get("ref", "")
            distance = step.get("distance", 0)

            expressway = is_expressway(
                road_name,
                road_ref
            )

            # Store segment information
            road_segments.append({
                "road_name": road_name,
                "road_ref": road_ref,
                "distance_m": distance,
                "expressway": expressway
            })

            # Add expressway distance
            if expressway:

                expressway_distance += distance

    # ----------------------------------------------
    # Calculate percentage
    # ----------------------------------------------

    if total_distance > 0:

        expressway_percentage = (
            expressway_distance / total_distance
        ) * 100

    else:

        expressway_percentage = 0

    return {
        "total_distance_m": total_distance,

        "expressway_distance_m":
            expressway_distance,

        "expressway_percentage":
            round(expressway_percentage, 2),

        "road_segments":
            road_segments
    }