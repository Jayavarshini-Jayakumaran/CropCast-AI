from flask import Flask, render_template, jsonify, request
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from data.crop_data import (
    get_weather_prediction,
    get_all_monthly_data,
    CROP_RECOMMENDATIONS,
    CULTIVATION_MATERIALS,
    MONTH_NAMES,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/predict/<int:month>")
def predict(month):
    if month < 1 or month > 12:
        return jsonify({"error": "Month must be between 1 and 12"}), 400

    weather = get_weather_prediction(month)
    crops = CROP_RECOMMENDATIONS[month]
    materials = CULTIVATION_MATERIALS[month]

    return jsonify({
        "weather": weather,
        "crops": {
            "recommended": crops["crops"],
            "avoid": crops["avoid"],
            "tip": crops["tip"],
        },
        "materials": materials,
    })


@app.route("/api/yearly")
def yearly():
    data = get_all_monthly_data()
    return jsonify(data)


@app.route("/api/months")
def months():
    return jsonify([{"id": k, "name": v} for k, v in MONTH_NAMES.items()])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
