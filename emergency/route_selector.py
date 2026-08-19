"""
====================================================
Emergency Route Selector

Selects the best route for an ambulance based on:

1. Travel time
2. Distance
3. Expressway usage
4. Blocked roads

Higher score = better emergency route.
====================================================
"""


def calculate_route_score(
    distance_m,
    duration_sec,
    expressway_percentage=0,
    blocked=False
):
    """
    Calculate emergency route score.
    """

    distance_km = distance_m / 1000
    duration_min = duration_sec / 60

    # Start with a base score
    score = 100

    # Faster routes are preferred
    score -= duration_min * 1.5

    # Shorter routes are preferred
    score -= distance_km * 0.5

    # More expressway usage gets a bonus
    score += expressway_percentage * 0.2

    # A blocked route receives a major penalty
    if blocked:
        score -= 50

    return round(score, 2)


def select_best_route(routes):
    """
    Select the best emergency route.

    Blocked routes are avoided whenever at least
    one clear route is available.
    """

    if not routes:
        raise ValueError("No routes available.")

    # -----------------------------------------
    # First find routes that are NOT blocked
    # -----------------------------------------

    clear_routes = [
        route
        for route in routes
        if not route.get("blocked", False)
    ]

    # -----------------------------------------
    # If clear routes exist, use only those
    # -----------------------------------------

    if clear_routes:

        best_route = None
        best_score = float("-inf")

        for route in clear_routes:

            score = calculate_route_score(
                route["distance_m"],
                route["duration_sec"],
                route.get(
                    "expressway_percentage",
                    0
                ),
                False
            )

            route["emergency_score"] = score

            if score > best_score:

                best_score = score
                best_route = route

        return best_route

    # -----------------------------------------
    # No clear route exists
    # -----------------------------------------

    return None