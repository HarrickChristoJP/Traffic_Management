from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# PROJECT IMPORTS
# ============================================================

from api.geocoder import geocode_place
from api.routes import get_route

from emergency.expressway import analyze_route

from emergency.road_blocks import (
    add_blocked_road,
    check_route_for_blocked_roads
)

from emergency.route_selector import select_best_route

from converters.geojson_converter import (
    create_emergency_geojson
)


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():

    return render_template(
        "index.html"
    )


# ============================================================
# SERVE EMERGENCY GEOJSON
# ============================================================

@app.route("/emergency_routes.geojson")
def emergency_routes():

    output_folder = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "output"
        )
    )

    return send_from_directory(
        output_folder,
        "emergency_routes.geojson"
    )


# ============================================================
# CALCULATE EMERGENCY ROUTE
# ============================================================

@app.route(
    "/calculate-route",
    methods=["POST"]
)
def calculate_route():

    try:

        # ----------------------------------------------------
        # Get data from dashboard
        # ----------------------------------------------------

        data = request.get_json()

        start_place = data.get(
            "start",
            ""
        ).strip()

        destination_place = data.get(
            "destination",
            ""
        ).strip()


        # ----------------------------------------------------
        # Validate input
        # ----------------------------------------------------

        if not start_place:

            return jsonify({
                "success": False,
                "error": "Start location is required."
            }), 400


        if not destination_place:

            return jsonify({
                "success": False,
                "error": "Destination is required."
            }), 400


        print("\n========================================")
        print("       NEW EMERGENCY ROUTE REQUEST")
        print("========================================")

        print(
            f"Start: {start_place}"
        )

        print(
            f"Destination: {destination_place}"
        )
        print("Dashboard request received successfully.")

        # ====================================================
        # GEOCODE START
        # ====================================================

        print("\nFinding start location...")

        start = geocode_place(
            start_place
        )


        # ====================================================
        # GEOCODE DESTINATION
        # ====================================================

        print("\nFinding destination location...")

        destination = geocode_place(
            destination_place
        )


        print("\nStart coordinates:")
        print(start)

        print("\nDestination coordinates:")
        print(destination)


        # ====================================================
        # GET ROUTES FROM OSRM
        # ====================================================

        print("\nCalculating routes...")

        route_data = get_route(
            start,
            destination
        )


        print(
            f"\nNumber of routes returned: "
            f"{len(route_data['routes'])}"
        )


        # ====================================================
        # TEMPORARY TEST BLOCK
        # ====================================================
        #
        # We are keeping the same blocked road that
        # you have been using for testing.
        #
        # Later we will replace this with dashboard-based
        # road-block management.
        #

        add_blocked_road(
            "Rajiv Gandhi IT Expressway"
        )


        # ====================================================
        # ANALYZE ROUTES
        # ====================================================

        routes_for_selection = []


        for index, route in enumerate(
            route_data["routes"]
        ):

            print(
                f"\nAnalyzing Route {index + 1}..."
            )


            # ------------------------------------------------
            # Expressway analysis
            # ------------------------------------------------

            expressway_data = analyze_route(
                route
            )


            # ------------------------------------------------
            # Road block analysis
            # ------------------------------------------------

            block_data = check_route_for_blocked_roads(
                expressway_data["road_segments"]
            )


            # ------------------------------------------------
            # Route information
            # ------------------------------------------------

            route_info = {

                "route_number":
                    index + 1,

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


        # ====================================================
        # SELECT BEST EMERGENCY ROUTE
        # ====================================================

        best_route = select_best_route(
            routes_for_selection
        )


        # ====================================================
        # SELECTED ROUTE NUMBER
        # ====================================================

        if best_route is not None:

            selected_route_number = (
                best_route["route_number"]
            )

        else:

            selected_route_number = None


        # ====================================================
        # CREATE EMERGENCY GEOJSON
        # ====================================================

        output_file = os.path.join(
            PROJECT_ROOT,
            "output",
            "emergency_routes.geojson"
        )


        create_emergency_geojson(
            route_data,
            routes_for_selection,
            selected_route_number,
            output_file
        )


        print(
            "\nEmergency analysis layer created:"
        )

        print(
            output_file
        )


        # ====================================================
        # RETURN RESULT TO DASHBOARD
        # ====================================================

        return jsonify({

            "success": True,

            "start": start_place,

            "destination":
                destination_place,

            "start_coordinates": {

                "latitude":
                    start[0],

                "longitude":
                    start[1]
            },

            "destination_coordinates": {

                "latitude":
                    destination[0],

                "longitude":
                    destination[1]
            },

            "selected_route":
                selected_route_number,

            "routes_count":
                len(route_data["routes"])
        })


    except Exception as e:

        print("\nERROR:")
        print(str(e))

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# RUN FLASK
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000
    )