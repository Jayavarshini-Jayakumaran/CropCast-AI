"""
CropCast AI — ML Training Script
Run once: python train_model.py
Outputs: models/crop_classifier.pkl, models/weather_regressor.pkl, models/encoders.pkl
"""

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

os.makedirs("models", exist_ok=True)

# ─────────────────────────────────────────────
# 1. CROP CLASSIFIER
#    Dataset: crop_recommendation.csv (Kaggle)
#    Features: N, P, K, temperature, humidity, ph, rainfall
#    Target: label (crop name)
# ─────────────────────────────────────────────

print("=" * 50)
print("TRAINING CROP CLASSIFIER")
print("=" * 50)

crop_df = pd.read_csv("data/crop_recommendation.csv")
print(f"Dataset shape: {crop_df.shape}")
print(f"Crops: {sorted(crop_df['label'].unique())}\n")

X_crop = crop_df[["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]]
y_crop = crop_df["label"]

le = LabelEncoder()
y_encoded = le.fit_transform(y_crop)

X_train, X_test, y_train, y_test = train_test_split(
    X_crop, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

crop_pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1
    ))
])

crop_pipeline.fit(X_train, y_train)

# Evaluation
y_pred = crop_pipeline.predict(X_test)
cv_scores = cross_val_score(crop_pipeline, X_crop, y_encoded, cv=5)

print(f"Test Accuracy : {crop_pipeline.score(X_test, y_test):.4f}")
print(f"CV Accuracy   : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# Feature importance
feat_imp = pd.Series(
    crop_pipeline.named_steps["clf"].feature_importances_,
    index=X_crop.columns
).sort_values(ascending=False)
print("\nFeature Importances:")
print(feat_imp.to_string())


# ─────────────────────────────────────────────
# 2. WEATHER REGRESSOR
#    Source: built from Tamil Nadu historical normals
#    extended with noise to simulate multi-year data
#    Features: month, year
#    Targets: temp_avg, rainfall, humidity, wind_speed
#
#    NOTE: Replace this synthetic data with a real
#    IMD/ERA5 dataset CSV if you have one:
#    columns: month, year, temp_avg, rainfall, humidity, wind_speed
# ─────────────────────────────────────────────

print("\n" + "=" * 50)
print("TRAINING WEATHER REGRESSORS")
print("=" * 50)

# Tamil Nadu monthly climate normals (1991-2020 averages)
MONTHLY_NORMALS = {
    #  month  t_min  t_max  rain  humid  wind
    1:  (20,   29,   35,   72,   9),
    2:  (22,   32,   15,   65,   10),
    3:  (25,   36,   10,   60,   11),
    4:  (27,   38,   20,   62,   12),
    5:  (28,   39,   45,   68,   14),
    6:  (26,   36,   90,   78,   16),
    7:  (25,   34,   110,  82,   15),
    8:  (25,   33,   120,  84,   14),
    9:  (24,   33,   140,  83,   13),
    10: (23,   31,   180,  85,   11),
    11: (21,   30,   150,  80,   10),
    12: (20,   28,   60,   75,   9),
}

# Simulate 30 years of data with realistic inter-annual variability
np.random.seed(42)
rows = []
for year in range(1991, 2024):
    for month, (t_min, t_max, rain, humid, wind) in MONTHLY_NORMALS.items():
        # Inter-annual variability (climate change trend on temp)
        year_offset = (year - 1991) * 0.02
        rows.append({
            "month": month,
            "year": year,
            "month_sin": np.sin(2 * np.pi * month / 12),  # cyclical encoding
            "month_cos": np.cos(2 * np.pi * month / 12),
            "temp_avg":    round((t_min + t_max) / 2 + year_offset + np.random.normal(0, 1.2), 2),
            "rainfall":    round(max(0, rain + np.random.normal(0, rain * 0.15)), 2),
            "humidity":    round(np.clip(humid + np.random.normal(0, 3), 40, 99), 2),
            "wind_speed":  round(max(0, wind + np.random.normal(0, 1.2)), 2),
        })

weather_df = pd.DataFrame(rows)
print(f"Weather dataset shape: {weather_df.shape}")

# Train one regressor per target (multi-output alternative)
weather_features = ["month_sin", "month_cos", "year"]
weather_targets  = ["temp_avg", "rainfall", "humidity", "wind_speed"]

weather_models = {}
for target in weather_targets:
    X_w = weather_df[weather_features]
    y_w = weather_df[target]

    X_tr, X_te, y_tr, y_te = train_test_split(X_w, y_w, test_size=0.2, random_state=42)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            random_state=42
        ))
    ])
    model.fit(X_tr, y_tr)
    y_hat = model.predict(X_te)

    print(f"  {target:<15} MAE={mean_absolute_error(y_te, y_hat):.3f}  R²={r2_score(y_te, y_hat):.4f}")
    weather_models[target] = model


# ─────────────────────────────────────────────
# 3. SAVE EVERYTHING
# ─────────────────────────────────────────────

joblib.dump(crop_pipeline,   "models/crop_classifier.pkl")
joblib.dump(weather_models,  "models/weather_regressors.pkl")
joblib.dump(le,              "models/label_encoder.pkl")

print("\n✅ Models saved to models/")
print("   models/crop_classifier.pkl")
print("   models/weather_regressors.pkl")
print("   models/label_encoder.pkl")


# ─────────────────────────────────────────────
# 4. QUICK SANITY CHECK
# ─────────────────────────────────────────────

print("\n" + "=" * 50)
print("SANITY CHECK — June predictions")
print("=" * 50)

# Weather for June 2025
import math
month = 6
year  = 2025
feats = pd.DataFrame([[
    math.sin(2*math.pi*month/12),
    math.cos(2*math.pi*month/12),
    year
]], columns=["month_sin", "month_cos", "year"])

for tgt, mdl in weather_models.items():
    val = mdl.predict(feats)[0]
    print(f"  {tgt:<15}: {val:.2f}")

# Top 3 crops for June weather conditions
june_weather = {t: weather_models[t].predict(feats)[0] for t in weather_targets}
crop_input = pd.DataFrame([[60, 45, 40,
    june_weather["temp_avg"], june_weather["humidity"], 6.5, june_weather["rainfall"]
]], columns=["N","P","K","temperature","humidity","ph","rainfall"])

proba = crop_pipeline.predict_proba(crop_input)[0]
top3_idx = np.argsort(proba)[::-1][:3]
print("\n  Top 3 crops for June:")
for idx in top3_idx:
    print(f"    {le.classes_[idx]:<20} {proba[idx]*100:.1f}%")
