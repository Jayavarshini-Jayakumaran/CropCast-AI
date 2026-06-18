"""
CropCast AI — Unified Training Script
Trains:
  1. Crop classifier      (Random Forest,        Kaggle dataset)
  2. Weather regressors   (Gradient Boosting,     NASA POWER CSV or synthetic fallback)

Run:
  python train_model.py                          # uses data/nasa_weather_11.0_76.95.csv
  python train_model.py 28.61 77.20             # train for Delhi coords
  python train_model.py --synthetic              # fallback synthetic data
"""

import sys
import os
import math
import glob
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

os.makedirs("models", exist_ok=True)


# ════════════════════════════════════════════════
# 1. CROP CLASSIFIER  (same for all locations)
# ════════════════════════════════════════════════
def train_crop_classifier():
    print("=" * 55)
    print("TRAINING CROP CLASSIFIER")
    print("=" * 55)

    df = pd.read_csv("data/crop_recommendation.csv")
    print(f"Dataset : {df.shape}  |  Crops: {df['label'].nunique()}")

    X = df[["N","P","K","temperature","humidity","ph","rainfall"]]
    y = df["label"]
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=200, max_depth=None,
            min_samples_split=2, random_state=42, n_jobs=-1
        ))
    ])
    pipe.fit(X_tr, y_tr)

    cv = cross_val_score(pipe, X, y_enc, cv=5)
    print(f"Test Acc : {pipe.score(X_te, y_te):.4f}")
    print(f"CV Acc   : {cv.mean():.4f} ± {cv.std():.4f}\n")
    print(classification_report(y_te, pipe.predict(X_te), target_names=le.classes_))

    feat_imp = pd.Series(
        pipe.named_steps["clf"].feature_importances_, index=X.columns
    ).sort_values(ascending=False)
    print("Feature importances:\n", feat_imp.to_string())

    joblib.dump(pipe, "models/crop_classifier.pkl")
    joblib.dump(le,   "models/label_encoder.pkl")
    print("\n✅ Saved crop_classifier.pkl + label_encoder.pkl")
    return pipe, le


# ════════════════════════════════════════════════
# 2. WEATHER REGRESSORS
# ════════════════════════════════════════════════
def _synthetic_weather() -> pd.DataFrame:
    """Fallback: Tamil Nadu climate normals with 30-yr noise."""
    NORMALS = {
        1:(20,29,35,72,9),  2:(22,32,15,65,10), 3:(25,36,10,60,11),
        4:(27,38,20,62,12), 5:(28,39,45,68,14), 6:(26,36,90,78,16),
        7:(25,34,110,82,15),8:(25,33,120,84,14),9:(24,33,140,83,13),
        10:(23,31,180,85,11),11:(21,30,150,80,10),12:(20,28,60,75,9),
    }
    np.random.seed(42)
    rows = []
    for year in range(1991, 2024):
        for month, (tmin,tmax,rain,hum,wind) in NORMALS.items():
            yo = (year - 1991) * 0.02
            rows.append({
                "year": year, "month": month,
                "month_sin": math.sin(2*math.pi*month/12),
                "month_cos": math.cos(2*math.pi*month/12),
                "temp_avg":   round((tmin+tmax)/2 + yo + np.random.normal(0,1.2), 2),
                "temp_max":   round(tmax + yo + np.random.normal(0,1.5), 2),
                "temp_min":   round(tmin + yo + np.random.normal(0,1.0), 2),
                "rainfall":   round(max(0, rain + np.random.normal(0, rain*0.15)), 2),
                "humidity":   round(np.clip(hum + np.random.normal(0,3), 40, 99), 2),
                "wind_speed": round(max(0, wind + np.random.normal(0,1.2)), 2),
            })
    return pd.DataFrame(rows)


def train_weather_regressors(lat=None, lon=None, use_synthetic=False):
    print("\n" + "=" * 55)
    print("TRAINING WEATHER REGRESSORS")
    print("=" * 55)

    # ── Choose data source ──
    if use_synthetic:
        df = _synthetic_weather()
        source = "synthetic (Tamil Nadu normals)"
    else:
        # Look for NASA CSV matching lat/lon, or pick any available one
        if lat is not None and lon is not None:
            path = f"data/nasa_weather_{lat}_{lon}.csv"
        else:
            files = glob.glob("data/nasa_weather_*.csv")
            path  = files[0] if files else None

        if path and Path(path).exists():
            df     = pd.read_csv(path)
            source = f"NASA POWER — {path}"
        else:
            print("⚠️  No NASA CSV found. Using synthetic fallback.")
            print("   Run: python fetch_nasa_data.py <lat> <lon>  to get real data.")
            df     = _synthetic_weather()
            source = "synthetic (Tamil Nadu normals)"

    print(f"Source  : {source}")
    print(f"Dataset : {df.shape}  |  Years: {df['year'].min()}–{df['year'].max()}")

    features = ["month_sin", "month_cos", "year"]
    targets  = ["temp_avg", "rainfall", "humidity", "wind_speed"]

    # Add temp_max / temp_min if available (NASA data has them)
    if "temp_max" in df.columns:
        targets += ["temp_max", "temp_min"]

    models = {}
    print()
    for tgt in targets:
        if tgt not in df.columns:
            continue
        X = df[features]
        y = df[tgt]
        X_tr,X_te,y_tr,y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        m = Pipeline([
            ("sc", StandardScaler()),
            ("reg", GradientBoostingRegressor(
                n_estimators=300, learning_rate=0.04,
                max_depth=5, subsample=0.8, random_state=42
            ))
        ])
        m.fit(X_tr, y_tr)
        yh = m.predict(X_te)
        print(f"  {tgt:<14}  MAE={mean_absolute_error(y_te,yh):.3f}  R²={r2_score(y_te,yh):.4f}")
        models[tgt] = m

    joblib.dump(models, "models/weather_regressors.pkl")

    # ── Save location metadata so Flask knows what data it's using ──
    meta = {
        "lat":    lat,
        "lon":    lon,
        "source": source,
        "has_real_data": not use_synthetic and "NASA" in source,
    }
    joblib.dump(meta, "models/location_meta.pkl")

    print("\n✅ Saved weather_regressors.pkl + location_meta.pkl")
    return models


# ════════════════════════════════════════════════
# 3. SANITY CHECK
# ════════════════════════════════════════════════
def sanity_check(crop_pipe, le, weather_models):
    print("\n" + "=" * 55)
    print("SANITY CHECK — June predictions")
    print("=" * 55)
    month, year = 6, 2025
    feats = pd.DataFrame([[
        math.sin(2*math.pi*month/12),
        math.cos(2*math.pi*month/12),
        year
    ]], columns=["month_sin","month_cos","year"])

    june = {}
    for tgt, mdl in weather_models.items():
        june[tgt] = round(mdl.predict(feats)[0], 2)
        print(f"  {tgt:<14}: {june[tgt]}")

    crop_in = pd.DataFrame([[
        60, 45, 40,
        june.get("temp_avg", 31),
        june.get("humidity", 78),
        6.5,
        june.get("rainfall", 85),
    ]], columns=["N","P","K","temperature","humidity","ph","rainfall"])

    proba = crop_pipe.predict_proba(crop_in)[0]
    top3  = np.argsort(proba)[::-1][:3]
    print("\n  Top 3 crops for June:")
    for i in top3:
        print(f"    {le.classes_[i]:<20} {proba[i]*100:.1f}%")


# ════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════
if __name__ == "__main__":
    use_syn = "--synthetic" in sys.argv
    lat = float(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] not in ("--synthetic",) else None
    lon = float(sys.argv[2]) if len(sys.argv) > 2 else None

    crop_pipe, le     = train_crop_classifier()
    weather_models    = train_weather_regressors(lat, lon, use_synthetic=use_syn)
    sanity_check(crop_pipe, le, weather_models)

    print("\n🎉 All models ready. Run: python app.py")
