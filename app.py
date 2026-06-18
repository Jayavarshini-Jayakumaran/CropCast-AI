"""
CropCast AI — Global Flask App
Supports dynamic location selection + NASA data fetching + model retraining on the fly.
"""

from flask import Flask, render_template, jsonify, request
import sys, os, subprocess, glob
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)

def _load_data_module():
    """Reload data module so model switches take effect without restart."""
    import importlib
    import data.crop_data as cd
    importlib.reload(cd)
    return cd


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/location/meta")
def location_meta():
    """Returns what location the current model was trained on."""
    cd = _load_data_module()
    meta = cd.get_location_meta()
    return jsonify(meta)


@app.route("/api/location/set", methods=["POST"])
def set_location():
    """
    Fetch NASA data for a new lat/lon and retrain weather regressors.
    This runs synchronously — takes ~10s. For production, use a task queue.
    """
    body = request.get_json()
    lat  = round(float(body["lat"]), 4)
    lon  = round(float(body["lon"]), 4)
    name = body.get("name", f"{lat}, {lon}")

    csv_path = f"data/nasa_weather_{lat}_{lon}.csv"

    # Step 1: Fetch NASA data if not cached
    if not Path(csv_path).exists():
        try:
            from fetch_nasa_data import fetch
            fetch(lat, lon)
        except Exception as e:
            return jsonify({"error": f"NASA fetch failed: {str(e)}"}), 500

    # Step 2: Retrain weather regressors only (crop classifier stays the same)
    try:
        from train_model import train_weather_regressors
        train_weather_regressors(lat, lon)
    except Exception as e:
        return jsonify({"error": f"Retraining failed: {str(e)}"}), 500

    return jsonify({
        "status": "ok",
        "lat": lat, "lon": lon, "name": name,
        "csv": csv_path,
    })


@app.route("/api/predict/<int:month>")
def predict(month):
    if month < 1 or month > 12:
        return jsonify({"error": "Month must be between 1 and 12"}), 400

    year = request.args.get("year", datetime.now().year, type=int)
    cd   = _load_data_module()

    weather = cd.get_weather_prediction(month, year)
    crops   = cd.get_crop_recommendations(month, year)
    meta    = cd.get_location_meta()

    return jsonify({
        "weather":  weather,
        "crops": {
            "recommended":      crops["crops"],
            "recommended_conf": crops["crops_with_conf"],
            "avoid":            crops["avoid"],
            "tip":              crops["tip"],
            "model_used":       crops["model_used"],
        },
        "materials": cd._MATERIALS[month],
        "location":  meta,
    })


@app.route("/api/yearly")
def yearly():
    year = request.args.get("year", datetime.now().year, type=int)
    cd   = _load_data_module()
    return jsonify(cd.get_all_monthly_data(year))


@app.route("/api/months")
def months():
    cd = _load_data_module()
    return jsonify([{"id": k, "name": v} for k, v in cd.MONTH_NAMES.items()])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
