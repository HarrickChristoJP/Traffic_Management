from api.geocoder import geocode_place
from api.routes import get_route
from converters.geojson_converter import create_route_geojson


# -----------------------------------
# Get locations from user
# -----------------------------------

start_place = input("Enter start location: ")
destination_place = input("Enter destination: ")


# -----------------------------------
# Convert place names to coordinates
# -----------------------------------

print("\nFinding start location...")
start = geocode_place(start_place)

print("\nFinding destination location...")
destination = geocode_place(destination_place)


# -----------------------------------
# Get route from OSRM
# -----------------------------------

print("\nCalculating route...")

route = get_route(start, destination)
print("\nOSRM route keys:")
print(route["routes"][0].keys())

print("\nFirst route legs:")
print(route["routes"][0]["legs"][0].keys())
print("\nFirst route road steps:")

steps = route["routes"][0]["legs"][0]["steps"]

for i, step in enumerate(steps[:10]):

    print(f"\nStep {i + 1}")

    print("Road name :", step.get("name"))
    print("Road ref  :", step.get("ref"))
    print("Distance  :", step.get("distance"))
    print("Mode      :", step.get("mode"))

    print("Classes   :", step.get("classes"))
print("\nNumber of routes returned:", len(route["routes"]))

for i, r in enumerate(route["routes"]):
    print(
        f"Route {i + 1}: "
        f"{r['distance'] / 1000:.2f} km, "
        f"{r['duration'] / 60:.1f} min"
    )

# -----------------------------------
# Get first route
# -----------------------------------

route_data = route["routes"][0]

distance_m = route_data["distance"]
duration_sec = route_data["duration"]


# -----------------------------------
# Convert units
# -----------------------------------

distance_km = distance_m / 1000

hours = int(duration_sec // 3600)
minutes = int((duration_sec % 3600) // 60)


# -----------------------------------
# Create GeoJSON
# -----------------------------------

create_route_geojson(
    route,
    "output/route.geojson"
)


# -----------------------------------
# Display route information
# -----------------------------------

print("\n========================================")
print("          ROUTE INFORMATION")
print("========================================")

print(f"\nStart:")
print(start_place)

print(f"\nDestination:")
print(destination_place)

print(f"\nStart coordinates:")
print(f"Latitude : {start[0]}")
print(f"Longitude: {start[1]}")

print(f"\nDestination coordinates:")
print(f"Latitude : {destination[0]}")
print(f"Longitude: {destination[1]}")

print(f"\nDistance:")
print(f"{distance_km:.2f} km")

print(f"\nEstimated travel time:")

if hours > 0:
    print(f"{hours} hour(s) {minutes} minute(s)")
else:
    print(f"{minutes} minute(s)")

print("\nGeoJSON:")
print("output/route.geojson")

print("\n========================================")
print("       ROUTE GENERATED SUCCESSFULLY")
print("========================================")