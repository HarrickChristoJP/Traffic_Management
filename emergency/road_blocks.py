"""
====================================================
Road Block Management

Stores roads that are currently blocked and provides
basic alias matching for common road names.
====================================================
"""

BLOCKED_ROADS = []

# Common road aliases
ROAD_ALIASES = {
    "omr": [
        "omr",
        "old mahabalipuram road",
        "rajiv gandhi salai"
    ],

    "ecr": [
        "ecr",
        "east coast road"
    ],

    "gst road": [
        "gst road",
        "grand southern trunk road",
        "nh 32",
        "nh32"
    ],

    "mount road": [
        "mount road",
        "anna salai"
    ],

    "velachery main road": [
        "velachery main road",
        "velachery road"
    ]
}


def normalize(text):
    """Convert text to a simple comparable format."""

    return text.strip().lower()


def add_blocked_road(road_name):
    """Add a road to the blocked-road list."""

    road_name = normalize(road_name)

    if road_name and road_name not in BLOCKED_ROADS:
        BLOCKED_ROADS.append(road_name)

        print(f"Road blocked: {road_name}")


def remove_blocked_road(road_name):
    """Remove a road from the blocked-road list."""

    road_name = normalize(road_name)

    if road_name in BLOCKED_ROADS:
        BLOCKED_ROADS.remove(road_name)

        print(f"Road unblocked: {road_name}")


def get_blocked_roads():
    """Return all currently blocked roads."""

    return BLOCKED_ROADS


def is_road_blocked(road_name):
    """
    Check whether a road is blocked.

    Supports common aliases such as:
    OMR ↔ Old Mahabalipuram Road
    ECR ↔ East Coast Road
    """

    if not road_name:
        return False

    road_name = normalize(road_name)

    for blocked_road in BLOCKED_ROADS:

        # Direct match
        if blocked_road in road_name:
            return True

        # Check aliases
        aliases = ROAD_ALIASES.get(blocked_road, [])

        for alias in aliases:

            if alias in road_name:
                return True

    return False
def check_route_for_blocked_roads(road_segments):
    """
    Check whether any road segment in a route
    is currently blocked.

    Parameters
    ----------
    road_segments : list
        Road segments returned by expressway analysis.

    Returns
    -------
    dict
        Block status and blocked road names.
    """

    blocked_roads = []

    for segment in road_segments:

        road_name = segment.get("road_name", "")

        if is_road_blocked(road_name):

            if road_name and road_name not in blocked_roads:
                blocked_roads.append(road_name)

    return {
        "blocked": len(blocked_roads) > 0,
        "blocked_roads": blocked_roads
    }