from emergency.route_selector import select_best_route


routes = [

    {
        "route_number": 1,
        "distance_m": 20890,
        "duration_sec": 1326.1,
        "expressway_percentage": 60,
        "blocked": False
    },

    {
        "route_number": 2,
        "distance_m": 23567.1,
        "duration_sec": 1431.8,
        "expressway_percentage": 20,
        "blocked": False
    }

]


best_route = select_best_route(routes)


print("\n==============================")
print("EMERGENCY ROUTE ANALYSIS")
print("==============================")

for route in routes:

    print(
        f"Route {route['route_number']} "
        f"→ Score: {route['emergency_score']}"
    )


print("\n------------------------------")

print(
    f"🚑 BEST ROUTE: "
    f"Route {best_route['route_number']}"
)

print(
    f"Emergency Score: "
    f"{best_route['emergency_score']}"
)