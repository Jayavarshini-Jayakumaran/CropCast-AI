"""
CropCast AI — ML-powered predictions
Replaces the hardcoded crop_data.py with model inference.
Models must be trained first: python train_model.py
"""

import math
import joblib
import numpy as np
from pathlib import Path

# ── Load models once at import time ──
_MODEL_DIR = Path(__file__).parent.parent / "models"

_crop_clf     = joblib.load(_MODEL_DIR / "crop_classifier.pkl")
_weather_regs = joblib.load(_MODEL_DIR / "weather_regressors.pkl")
_label_enc    = joblib.load(_MODEL_DIR / "label_encoder.pkl")

MONTH_NAMES = {
    1: "January", 2: "February", 3:  "March",    4:  "April",
    5: "May",     6: "June",     7:  "July",      8:  "August",
    9: "September",10:"October", 11: "November",  12: "December"
}

SEASONS = {
    1: "Winter",           2: "Winter",
    3: "Summer",           4: "Summer",           5: "Summer",
    6: "Southwest Monsoon",7: "Southwest Monsoon", 8: "Southwest Monsoon",
    9: "Northeast Monsoon",10:"Northeast Monsoon", 11:"Northeast Monsoon",
    12:"Winter"
}

# Typical soil NPK + pH ranges per season for Tamil Nadu
# (used as inputs to the crop classifier since users don't enter soil data)
_SEASON_SOIL = {
    "Winter":             {"N": 55,  "P": 40, "K": 38, "ph": 6.8},
    "Summer":             {"N": 50,  "P": 35, "K": 35, "ph": 6.5},
    "Southwest Monsoon":  {"N": 65,  "P": 48, "K": 42, "ph": 6.3},
    "Northeast Monsoon":  {"N": 60,  "P": 45, "K": 40, "ph": 6.5},
}

# Crops that don't suit Tamil Nadu climate — filtered out from model output
_UNSUITABLE = {
    "apple",        # temperate — wrong climate
    "grapes",       # needs cold winters  
    "muskmelon",    # model overestimates in monsoon
    "pomegranate",  # arid crop, wrong for TN monsoon
    "papaya",       # perennial, not season-specific recommendation
    "orange",       # not a seasonal crop choice
    "coffee",       # plantation crop, not seasonal
}

# Static avoid-list and cultivation materials (agronomic knowledge,
# not learnable from the crop recommendation dataset)
_AVOID = {
    1:  ["Paddy", "Sugarcane"],        2:  ["Potato", "Wheat"],
    3:  ["Cool-season vegetables"],    4:  ["Leafy vegetables"],
    5:  ["Potato", "Strawberry"],      6:  ["Onion", "Garlic"],
    7:  ["Tomato", "Potato"],          8:  ["Groundnut", "Sesame"],
    9:  ["Cotton", "Sunflower"],       10: ["Sugarcane planting"],
    11: ["Paddy", "Taro"],             12: ["Paddy", "Banana planting"],
}

_MATERIALS = {
    1:  ["Compost manure", "Drip irrigation pipes", "Frost protection nets", "Fungicide (late blight)", "NPK 10-10-10"],
    2:  ["Mulching film", "Groundnut sheller", "Drip tape", "Biopesticides", "Potash fertilizer"],
    3:  ["Sprinkler system", "Shade nets", "Organic mulch", "Neem oil spray", "Calcium nitrate"],
    4:  ["Paddy seed trays", "Pre-emergent herbicide", "Sprayer pump", "Phosphate fertilizer", "Stakes"],
    5:  ["Seed treatment chemicals", "Hand weeders", "Urea fertilizer", "Water pumps", "Rainwater tanks"],
    6:  ["Drainage pumps", "Raised bed equipment", "Fungicide (downy mildew)", "Zinc sulphate", "Transplanting trays"],
    7:  ["Rain gauge", "Drainage pipes", "Contact fungicide", "Bund making tools", "Granular pesticide"],
    8:  ["Weed whacker", "Foliar spray", "Potassium fertilizer", "Field drainage nets", "Moisture meter"],
    9:  ["Harvesting sickles", "Threshing machine", "Storage bags", "Post-harvest fungicide", "Rabi seed varieties"],
    10: ["Combine harvester", "Grain dryer", "Jute storage sacks", "Pest control traps", "Lime (soil amendment)"],
    11: ["Seed drill machine", "Phosphate fertilizer", "Irrigation channels", "Weed control herbicide", "Row markers"],
    12: ["Cold storage solutions", "Raised bed planters", "Compost", "Insect netting", "Sulfur-based fungicide"],
}

_TIPS = {
    1:  "Cool nights — protect seedlings from frost in highland areas.",
    2:  "Temperatures rising — ensure adequate irrigation as rainfall is low.",
    3:  "Hot and dry — mulching helps retain soil moisture.",
    4:  "Pre-monsoon season — prepare nursery beds, irrigate in early morning.",
    5:  "Pre-monsoon showers expected — land prep for kharif crops.",
    6:  "Southwest monsoon begins — ensure proper field drainage.",
    7:  "Peak monsoon — avoid waterlogging, raise bunds.",
    8:  "Heavy rainfall continues — monitor for fungal diseases.",
    9:  "Northeast monsoon sets in — harvest kharif, prep for rabi.",
    10: "Peak northeast monsoon — harvest paddy before lodging.",
    11: "Retreating monsoon — cool nights help grain development.",
    12: "Cool and dry — minimal pest pressure, ideal for organic cultivation.",
}


def _weather_features(month: int, year: int = 2025) -> list:
    return [[
        math.sin(2 * math.pi * month / 12),
        math.cos(2 * math.pi * month / 12),
        year
    ]]


def get_weather_prediction(month: int, year: int = 2025) -> dict:
    feats = _weather_features(month, year)
    return {
        "month":      month,
        "month_name": MONTH_NAMES[month],
        "season":     SEASONS[month],
        "temp_avg":   round(_weather_regs["temp_avg"].predict(feats)[0], 1),
        "temp_min":   round(_weather_regs["temp_avg"].predict(feats)[0] - 4.5, 1),
        "temp_max":   round(_weather_regs["temp_avg"].predict(feats)[0] + 4.5, 1),
        "rainfall":   round(max(0, _weather_regs["rainfall"].predict(feats)[0]), 1),
        "humidity":   round(np.clip(_weather_regs["humidity"].predict(feats)[0], 40, 99), 1),
        "wind_speed": round(max(0, _weather_regs["wind_speed"].predict(feats)[0]), 1),
    }


def get_crop_recommendations(month: int, year: int = 2025, top_n: int = 6) -> dict:
    """
    Returns top_n crops predicted by the Random Forest classifier,
    filtered for Tamil Nadu suitability, with confidence scores.
    """
    weather = get_weather_prediction(month, year)
    season  = SEASONS[month]
    soil    = _SEASON_SOIL[season]

    crop_input = [[
        soil["N"], soil["P"], soil["K"],
        weather["temp_avg"],
        weather["humidity"],
        soil["ph"],
        weather["rainfall"],
    ]]

    proba    = _crop_clf.predict_proba(crop_input)[0]
    all_crops = _label_enc.classes_

    # Rank and filter
    ranked = sorted(
        [(all_crops[i], round(proba[i] * 100, 1)) for i in range(len(all_crops))
         if all_crops[i].lower() not in _UNSUITABLE],
        key=lambda x: x[1], reverse=True
    )

    top_crops      = [f"{name} ({conf}%)" for name, conf in ranked[:top_n]]
    top_crops_plain = [name for name, _ in ranked[:top_n]]  # for display

    return {
        "crops":          top_crops_plain,
        "crops_with_conf": top_crops,
        "avoid":          _AVOID[month],
        "tip":            _TIPS[month],
        "model_used":     True,
    }


def get_all_monthly_data(year: int = 2025) -> list:
    return [get_weather_prediction(m, year) for m in range(1, 13)]
