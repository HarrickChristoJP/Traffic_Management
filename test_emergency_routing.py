from api.routes import get_route
from emergency.expressway import analyze_route
from emergency.road_blocks import (
    add_blocked_road,
    check_route_for_blocked_roads
)
from emergency.route_selector import select_best_route
from converters.geojson_converter import create_emergency_geojson

# --------------------------------------------------
# Known coordinates
# --------------------------------------------------

start = (12.9174426, 80.2164902)

destination = (12.993374, 80.1725867)


# --------------------------------------------------
# Example blocked road
# --------------------------------------------------

# For testing, we will temporarily mark
# Rajiv Gandhi IT Expressway as blocked.

add_blocked_road("Rajiv Gandhi IT Expressway")


# --------------------------------------------------
# Get routes from OSRM
# --------------------------------------------------

print("\nCalculating routes...")

route_data = get_route(
    start,
    destination
)


# --------------------------------------------------
# Analyze every route
# --------------------------------------------------

routes_for_selection = []


for index, route in enumerate(
    route_data["routes"]
):

    print(
        f"\nAnalyzing Route {index + 1}..."
    )

    # ----------------------------------------------
    # Expressway analysis
    # ----------------------------------------------

    expressway_data = analyze_route(
        route
    )

    # ----------------------------------------------
    # Road-block analysis
    # ----------------------------------------------

    block_data = check_route_for_blocked_roads(
        expressway_data["road_segments"]
    )

    # ----------------------------------------------
    # Build route information
    # ----------------------------------------------

    route_info = {

        "route_number": index + 1,

        "distance_m":
            route["distance"],

        "duration_sec":
            route["duration"],

        "expressway_percentage":
            expressway_data[
                "expressway_percentage"
            ],

        "blocked":
            block_data["blocked"],

        "blocked_roads":
            block_data["blocked_roads"]
    }

    routes_for_selection.append(
        route_info
    )


# --------------------------------------------------
# Select emergency route
# --------------------------------------------------

best_route = select_best_route(
    routes_for_selection
)
# --------------------------------------------------
# Determine selected route
# --------------------------------------------------

if best_route is not None:

    selected_route_number = best_route["route_number"]

else:

    selected_route_number = None
# --------------------------------------------------
# Create Emergency GeoJSON
# --------------------------------------------------

create_emergency_geojson(
    route_data,
    routes_for_selection,
    selected_route_number,
    "output/emergency_routes.geojson"
)
print("\nEmergency analysis layer created:")
print("output/emergency_routes.geojson")

print("\n========================================")
print("        ROUTE ROAD SEGMENTS")
print("========================================")

for index, route in enumerate(route_data["routes"]):

    print(f"\nROUTE {index + 1}")

    for leg in route["legs"]:

        for step in leg["steps"]:

            road_name = step.get("name", "")

            if road_name:
                print(
                    f"{road_name} "
                    f"→ {step.get('distance', 0):.1f} m"
                )
# --------------------------------------------------
# Display results
# --------------------------------------------------

print("\n")
print("========================================")
print("       🚑 EMERGENCY ROUTE ANALYSIS")
print("========================================")


for route in routes_for_selection:

    print(
        f"\nRoute {route['route_number']}"
    )

    print(
        f"Distance: "
        f"{route['distance_m'] / 1000:.2f} km"
    )

    print(
        f"Time: "
        f"{route['duration_sec'] / 60:.1f} min"
    )

    print(
        f"Expressway: "
        f"{route['expressway_percentage']:.2f}%"
    )

    print(
        f"Blocked: "
        f"{route['blocked']}"
    )

    if route["blocked_roads"]:

        print(
        "Blocked roads:",
        ", ".join(
            route["blocked_roads"]
        )
        )

    if route["blocked"]:

        print(
        "Emergency Score: "
        "Not calculated (route is blocked)"
        )

    elif "emergency_score" in route:

        print(
        f"Emergency Score: "
        f"{route['emergency_score']}"
        )

# --------------------------------------------------
# Final decision
# --------------------------------------------------

print("\n----------------------------------------")



if best_route is None:

    print(
        "⚠️ WARNING:"
    )

    print(
        "All available routes contain blocked roads."
    )

    print(
        "No clear emergency route is available."
    )

else:

    print(
        f"🚑 SELECTED EMERGENCY ROUTE: "
        f"Route {best_route['route_number']}"
    )

    print(
        f"Emergency Score: "
        f"{best_route['emergency_score']}"
    )

print("=========================================")
