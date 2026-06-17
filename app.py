from flask import Flask, render_template, jsonify, request
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from data.crop_data import (
    get_weather_prediction,
    get_crop_recommendations,
    get_all_monthly_data,
    MONTH_NAMES,
    _MATERIALS,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/predict/<int:month>")
def predict(month):
    if month < 1 or month > 12:
        return jsonify({"error": "Month must be between 1 and 12"}), 400

    year    = request.args.get("year", 2025, type=int)
    weather = get_weather_prediction(month, year)
    crops   = get_crop_recommendations(month, year)

    return jsonify({
        "weather":  weather,
        "crops": {
            "recommended":      crops["crops"],
            "recommended_conf": crops["crops_with_conf"],  # includes % confidence
            "avoid":            crops["avoid"],
            "tip":              crops["tip"],
            "model_used":       crops["model_used"],
        },
        "materials": _MATERIALS[month],
    })


@app.route("/api/yearly")
def yearly():
    year = request.args.get("year", 2025, type=int)
    return jsonify(get_all_monthly_data(year))


@app.route("/api/months")
def months():
    return jsonify([{"id": k, "name": v} for k, v in MONTH_NAMES.items()])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
