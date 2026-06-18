"""
CropCast AI — ML inference engine (location-aware)
All predictions are driven by trained models + NASA real weather data.
"""

import math
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

_MODEL_DIR = Path(__file__).parent.parent / "models"

_crop_clf     = joblib.load(_MODEL_DIR / "crop_classifier.pkl")
_weather_regs = joblib.load(_MODEL_DIR / "weather_regressors.pkl")
_label_enc    = joblib.load(_MODEL_DIR / "label_encoder.pkl")

# Location metadata saved during training
try:
    _loc_meta = joblib.load(_MODEL_DIR / "location_meta.pkl")
except Exception:
    _loc_meta = {"lat": 11.0, "lon": 76.95, "source": "synthetic", "has_real_data": False}

MONTH_NAMES = {
    1:"January",2:"February",3:"March",4:"April",
    5:"May",6:"June",7:"July",8:"August",
    9:"September",10:"October",11:"November",12:"December"
}

SEASONS = {
    1:"Winter",2:"Winter",3:"Summer",4:"Summer",5:"Summer",
    6:"Southwest Monsoon",7:"Southwest Monsoon",8:"Southwest Monsoon",
    9:"Northeast Monsoon",10:"Northeast Monsoon",11:"Northeast Monsoon",
    12:"Winter"
}

# Koppen climate zones → season names (simplified)
# Used when location is outside Tamil Nadu
GENERIC_SEASONS = {
    1:"Jan–Feb (Cool)",2:"Jan–Feb (Cool)",3:"Mar–May (Warm)",
    4:"Mar–May (Warm)",5:"Mar–May (Warm)",6:"Jun–Sep (Wet)",
    7:"Jun–Sep (Wet)",8:"Jun–Sep (Wet)",9:"Jun–Sep (Wet)",
    10:"Oct–Dec (Retreat)",11:"Oct–Dec (Retreat)",12:"Jan–Feb (Cool)"
}

_SEASON_SOIL = {
    "Winter":             {"N":55,"P":40,"K":38,"ph":6.8},
    "Summer":             {"N":50,"P":35,"K":35,"ph":6.5},
    "Southwest Monsoon":  {"N":65,"P":48,"K":42,"ph":6.3},
    "Northeast Monsoon":  {"N":60,"P":45,"K":40,"ph":6.5},
    "Jan–Feb (Cool)":     {"N":55,"P":40,"K":38,"ph":6.8},
    "Mar–May (Warm)":     {"N":50,"P":35,"K":35,"ph":6.5},
    "Jun–Sep (Wet)":      {"N":65,"P":48,"K":42,"ph":6.3},
    "Oct–Dec (Retreat)":  {"N":60,"P":45,"K":40,"ph":6.5},
}

_UNSUITABLE_GLOBAL = set()  # no filtering globally — let the model decide

_AVOID = {
    1:["Paddy","Sugarcane"],       2:["Potato","Wheat"],
    3:["Cool-season vegetables"],  4:["Leafy vegetables"],
    5:["Potato","Strawberry"],     6:["Onion","Garlic"],
    7:["Tomato","Potato"],         8:["Groundnut","Sesame"],
    9:["Cotton","Sunflower"],      10:["Sugarcane planting"],
    11:["Paddy","Taro"],           12:["Paddy","Banana planting"],
}

_MATERIALS = {
    1: ["Compost manure","Drip irrigation pipes","Frost protection nets","Fungicide (late blight)","NPK 10-10-10"],
    2: ["Mulching film","Groundnut sheller","Drip tape","Biopesticides","Potash fertilizer"],
    3: ["Sprinkler system","Shade nets","Organic mulch","Neem oil spray","Calcium nitrate"],
    4: ["Paddy seed trays","Pre-emergent herbicide","Sprayer pump","Phosphate fertilizer","Stakes"],
    5: ["Seed treatment chemicals","Hand weeders","Urea fertilizer","Water pumps","Rainwater tanks"],
    6: ["Drainage pumps","Raised bed equipment","Fungicide (downy mildew)","Zinc sulphate","Transplanting trays"],
    7: ["Rain gauge","Drainage pipes","Contact fungicide","Bund making tools","Granular pesticide"],
    8: ["Weed whacker","Foliar spray","Potassium fertilizer","Field drainage nets","Moisture meter"],
    9: ["Harvesting sickles","Threshing machine","Storage bags","Post-harvest fungicide","Rabi seed varieties"],
    10:["Combine harvester","Grain dryer","Jute storage sacks","Pest control traps","Lime (soil amendment)"],
    11:["Seed drill machine","Phosphate fertilizer","Irrigation channels","Weed control herbicide","Row markers"],
    12:["Cold storage solutions","Raised bed planters","Compost","Insect netting","Sulfur-based fungicide"],
}

_TIPS = {
    1:"Cool nights — protect seedlings from frost in highland areas.",
    2:"Temperatures rising — ensure adequate irrigation as rainfall is low.",
    3:"Hot and dry — mulching helps retain soil moisture.",
    4:"Pre-monsoon season — prepare nursery beds, irrigate in early morning.",
    5:"Pre-monsoon showers expected — land prep for kharif crops.",
    6:"Southwest monsoon begins — ensure proper field drainage.",
    7:"Peak monsoon — avoid waterlogging, raise bunds.",
    8:"Heavy rainfall continues — monitor for fungal diseases.",
    9:"Northeast monsoon sets in — harvest kharif, prep for rabi.",
    10:"Peak northeast monsoon — harvest paddy before lodging.",
    11:"Retreating monsoon — cool nights help grain development.",
    12:"Cool and dry — minimal pest pressure, ideal for organic cultivation.",
}


def _feats(month: int, year: int) -> pd.DataFrame:
    return pd.DataFrame([[
        math.sin(2 * math.pi * month / 12),
        math.cos(2 * math.pi * month / 12),
        year
    ]], columns=["month_sin","month_cos","year"])


def get_location_meta() -> dict:
    return _loc_meta


def get_weather_prediction(month: int, year: int = 2025) -> dict:
    f = _feats(month, year)
    regs = _weather_regs
    t_avg = round(regs["temp_avg"].predict(f)[0], 1)
    t_max = round(regs["temp_max"].predict(f)[0], 1) if "temp_max" in regs else round(t_avg + 4.5, 1)
    t_min = round(regs["temp_min"].predict(f)[0], 1) if "temp_min" in regs else round(t_avg - 4.5, 1)
    return {
        "month":      month,
        "month_name": MONTH_NAMES[month],
        "season":     SEASONS.get(month, GENERIC_SEASONS[month]),
        "temp_avg":   t_avg,
        "temp_max":   t_max,
        "temp_min":   t_min,
        "rainfall":   round(max(0, regs["rainfall"].predict(f)[0]), 1),
        "humidity":   round(float(np.clip(regs["humidity"].predict(f)[0], 10, 99)), 1),
        "wind_speed": round(max(0, regs["wind_speed"].predict(f)[0]), 1),
    }


def get_crop_recommendations(month: int, year: int = 2025, top_n: int = 6) -> dict:
    weather = get_weather_prediction(month, year)
    season  = SEASONS.get(month, GENERIC_SEASONS[month])
    soil    = _SEASON_SOIL.get(season, {"N":60,"P":45,"K":40,"ph":6.5})

    crop_in = pd.DataFrame([[
        soil["N"], soil["P"], soil["K"],
        weather["temp_avg"], weather["humidity"],
        soil["ph"], weather["rainfall"],
    ]], columns=["N","P","K","temperature","humidity","ph","rainfall"])

    proba     = _crop_clf.predict_proba(crop_in)[0]
    all_crops = _label_enc.classes_

    ranked = sorted(
        [(all_crops[i], round(proba[i]*100, 1)) for i in range(len(all_crops))
         if all_crops[i].lower() not in _UNSUITABLE_GLOBAL],
        key=lambda x: x[1], reverse=True
    )

    return {
        "crops":           [n for n,_ in ranked[:top_n]],
        "crops_with_conf": [f"{n} ({c}%)" for n,c in ranked[:top_n]],
        "avoid":           _AVOID[month],
        "tip":             _TIPS[month],
        "model_used":      True,
    }


def get_all_monthly_data(year: int = 2025) -> list:
    return [get_weather_prediction(m, year) for m in range(1, 13)]
