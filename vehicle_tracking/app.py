from flask import Flask, render_template, jsonify
from vehicle_data import vehicle_data
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/track/<vehicle_number>")
def track_vehicle(vehicle_number):

    vehicle_number = vehicle_number.upper()

    records = vehicle_data.get(
        vehicle_number,
        []
    )

    return jsonify(records)
if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )