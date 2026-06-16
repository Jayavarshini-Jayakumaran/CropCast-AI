# Historical weather data by month (Tamil Nadu / South India climate)
HISTORICAL_WEATHER = {
    1:  {"temp_min": 20, "temp_max": 29, "rainfall": 35,  "humidity": 72, "wind": 9,  "season": "Winter"},
    2:  {"temp_min": 22, "temp_max": 32, "rainfall": 15,  "humidity": 65, "wind": 10, "season": "Winter"},
    3:  {"temp_min": 25, "temp_max": 36, "rainfall": 10,  "humidity": 60, "wind": 11, "season": "Summer"},
    4:  {"temp_min": 27, "temp_max": 38, "rainfall": 20,  "humidity": 62, "wind": 12, "season": "Summer"},
    5:  {"temp_min": 28, "temp_max": 39, "rainfall": 45,  "humidity": 68, "wind": 14, "season": "Summer"},
    6:  {"temp_min": 26, "temp_max": 36, "rainfall": 90,  "humidity": 78, "wind": 16, "season": "Southwest Monsoon"},
    7:  {"temp_min": 25, "temp_max": 34, "rainfall": 110, "humidity": 82, "wind": 15, "season": "Southwest Monsoon"},
    8:  {"temp_min": 25, "temp_max": 33, "rainfall": 120, "humidity": 84, "wind": 14, "season": "Southwest Monsoon"},
    9:  {"temp_min": 24, "temp_max": 33, "rainfall": 140, "humidity": 83, "wind": 13, "season": "Northeast Monsoon"},
    10: {"temp_min": 23, "temp_max": 31, "rainfall": 180, "humidity": 85, "wind": 11, "season": "Northeast Monsoon"},
    11: {"temp_min": 21, "temp_max": 30, "rainfall": 150, "humidity": 80, "wind": 10, "season": "Northeast Monsoon"},
    12: {"temp_min": 20, "temp_max": 28, "rainfall": 60,  "humidity": 75, "wind": 9,  "season": "Winter"},
}

# Crop recommendations per month
CROP_RECOMMENDATIONS = {
    1: {
        "crops": ["Tomato", "Brinjal", "Cabbage", "Cauliflower", "Peas"],
        "avoid": ["Paddy", "Sugarcane"],
        "tip": "Ideal for cool-season vegetables. Nights are cool — protect seedlings from frost in highland areas."
    },
    2: {
        "crops": ["Groundnut", "Sunflower", "Watermelon", "Cucumber", "Onion"],
        "avoid": ["Potato", "Wheat"],
        "tip": "Temperatures rising — great for oil seed crops. Ensure adequate irrigation as rainfall is low."
    },
    3: {
        "crops": ["Mango (harvest)", "Banana", "Maize", "Sesame", "Bitter Gourd"],
        "avoid": ["Cool-season vegetables"],
        "tip": "Hot and dry — mulching helps retain soil moisture. Good time for mango harvest."
    },
    4: {
        "crops": ["Paddy (nursery)", "Cotton", "Turmeric", "Ginger", "Chilli"],
        "avoid": ["Leafy vegetables"],
        "tip": "Pre-monsoon planting season. Prepare paddy nursery beds. High evaporation — irrigate in early morning."
    },
    5: {
        "crops": ["Paddy", "Maize", "Black Gram", "Green Gram", "Sesame"],
        "avoid": ["Potato", "Strawberry"],
        "tip": "Pre-monsoon showers expected. Sow drought-tolerant varieties. Land preparation for kharif crops."
    },
    6: {
        "crops": ["Paddy", "Sugarcane", "Taro", "Turmeric", "Banana"],
        "avoid": ["Onion", "Garlic"],
        "tip": "Southwest monsoon begins. Excellent for water-intensive crops. Ensure proper field drainage."
    },
    7: {
        "crops": ["Paddy", "Green Gram", "Black Gram", "Cowpea", "Soybean"],
        "avoid": ["Tomato", "Potato"],
        "tip": "Peak monsoon — heavy rains. Avoid waterlogging. Raise bunds and maintain proper drainage channels."
    },
    8: {
        "crops": ["Paddy", "Sorghum", "Pearl Millet", "Cowpea", "Yam"],
        "avoid": ["Groundnut", "Sesame"],
        "tip": "Continued heavy rainfall. Monitor for fungal diseases. Ensure surplus drainage in paddy fields."
    },
    9: {
        "crops": ["Paddy (harvest prep)", "Ragi", "Horsegram", "Pigeonpea", "Sweet Potato"],
        "avoid": ["Cotton", "Sunflower"],
        "tip": "Northeast monsoon sets in. Harvest early-sown kharif crops. Prepare fields for rabi season."
    },
    10: {
        "crops": ["Paddy (harvest)", "Vegetables", "Tomato", "Brinjal", "Green Gram"],
        "avoid": ["Sugarcane planting"],
        "tip": "Peak northeast monsoon. Harvest paddy before heavy rains cause lodging. Plant rabi nurseries."
    },
    11: {
        "crops": ["Wheat", "Sorghum", "Chickpea", "Mustard", "Sunflower"],
        "avoid": ["Paddy", "Taro"],
        "tip": "Retreating monsoon. Good time for rabi crops. Cool nights help in grain development."
    },
    12: {
        "crops": ["Tomato", "Potato", "Cabbage", "Carrot", "Garlic", "Onion"],
        "avoid": ["Paddy", "Banana planting"],
        "tip": "Cool and dry — perfect for rabi vegetables. Minimal pest pressure. Good for organic cultivation."
    },
}

# Cultivation materials per month
CULTIVATION_MATERIALS = {
    1:  ["Compost manure", "Drip irrigation pipes", "Row covers / frost protection nets", "Fungicide (for late blight)", "NPK fertilizer (10-10-10)"],
    2:  ["Mulching film", "Groundnut shelling machine", "Drip tape", "Biopesticides", "Potash fertilizer"],
    3:  ["Sprinkler system", "Shade nets", "Organic mulch", "Neem oil spray", "Calcium nitrate"],
    4:  ["Paddy seed trays", "Pre-emergent herbicide", "Sprayer pump", "Phosphate fertilizer", "Rope and stakes"],
    5:  ["Seed treatment chemicals", "Hand weeders", "Urea fertilizer", "Water pumps", "Rainwater harvesting tanks"],
    6:  ["Drainage pumps", "Raised bed equipment", "Fungicide (downy mildew)", "Zinc sulphate", "Transplanting trays"],
    7:  ["Rain gauge", "Drainage pipes", "Contact fungicide", "Bund making tools", "Granular pesticide"],
    8:  ["Weed whacker", "Foliar spray", "Potassium fertilizer", "Field drainage nets", "Moisture meter"],
    9:  ["Harvesting sickles", "Threshing machine", "Storage bags", "Post-harvest fungicide", "Rabi seed varieties"],
    10: ["Combine harvester", "Grain dryer", "Jute storage sacks", "Pest control traps", "Lime (soil amendment)"],
    11: ["Seed drill machine", "Phosphate fertilizer", "Irrigation channels", "Weed control herbicide", "Row markers"],
    12: ["Cold storage solutions", "Raised bed planters", "Compost", "Insect netting", "Sulfur-based fungicide"],
}

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

def get_weather_prediction(month: int) -> dict:
    base = HISTORICAL_WEATHER[month]
    import random
    random.seed(month * 7)
    variation = lambda x, v: round(x + random.uniform(-v, v), 1)
    return {
        "month": month,
        "month_name": MONTH_NAMES[month],
        "season": base["season"],
        "temp_min": variation(base["temp_min"], 1.5),
        "temp_max": variation(base["temp_max"], 2.0),
        "temp_avg": round((base["temp_min"] + base["temp_max"]) / 2, 1),
        "rainfall": variation(base["rainfall"], base["rainfall"] * 0.1),
        "humidity": variation(base["humidity"], 3),
        "wind_speed": variation(base["wind"], 1.5),
    }

def get_all_monthly_data() -> list:
    return [get_weather_prediction(m) for m in range(1, 13)]
