from api.routes import get_route
from emergency.expressway import analyze_route


# Coordinates we already verified
start = (12.9174426, 80.2164902)
destination = (12.993374, 80.1725867)


# Get routes from OSRM
route_data = get_route(
    start,
    destination
)


print("\n========================================")
print("        EXPRESSWAY ANALYSIS")
print("========================================")


for index, route in enumerate(route_data["routes"]):

    analysis = analyze_route(route)

    print(f"\nRoute {index + 1}")

    print(
        f"Total distance: "
        f"{analysis['total_distance_m'] / 1000:.2f} km"
    )

    print(
        f"Expressway distance: "
        f"{analysis['expressway_distance_m'] / 1000:.2f} km"
    )

    print(
        f"Expressway percentage: "
        f"{analysis['expressway_percentage']:.2f}%"
    )

    print("\nExpressway roads:")

    for segment in analysis["road_segments"]:

        if segment["expressway"]:

            print(
                f"  {segment['road_name']} "
                f"→ "
                f"{segment['distance_m']:.1f} m"
            )