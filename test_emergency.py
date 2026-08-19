from emergency.road_blocks import (
    add_blocked_road,
    remove_blocked_road,
    get_blocked_roads,
    is_road_blocked
)


add_blocked_road("OMR")

add_blocked_road("Velachery Main Road")


print("\nBlocked roads:")
print(get_blocked_roads())


print("\nChecking roads:")

print("OMR:", is_road_blocked("Old Mahabalipuram Road"))

print(
    "Velachery Main Road:",
    is_road_blocked("Velachery Main Road")
)

print(
    "Mount Road:",
    is_road_blocked("Anna Salai / Mount Road")
)