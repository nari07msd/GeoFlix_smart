from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import joblib
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ==== Mock trend data ====
TREND_DB = {
    "New York": ["Broadway shows", "Street food", "Skyline views"],
    "London": ["Royal sights", "Underground art", "West End"],
    "Tokyo": ["Cherry blossoms", "Anime cafes", "Robot shows"],
    "Bangalore": ["Startup culture", "Tech events", "Cafe hopping"]
}

# ==== Load ML model ====
MODEL_PATH = "ml_model.pkl"
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

# ==== Constants ====
LOG_FILE = "ml_logs.csv"

# ==== Routes ====

@app.route("/trends")
def get_trend():
    city = request.args.get("city", "Unknown")
    trends = TREND_DB.get(city, ["Local culture", "City highlights", "Top restaurants"])
    return jsonify({
        "city": city,
        "trend": random.choice(trends)
    })


@app.route("/ml-recommend", methods=["POST"])
def ml_recommend():
    if not model:
        return jsonify({"error": "ML model not loaded"}), 500

    try:
        data = request.get_json()
        condition = data.get("condition", "Clear")
        temperature = data.get("temperature", 25)

        # Encode weather condition
        condition_map = {"Clear": 0, "Rain": 1, "Clouds": 2, "Snow": 3}
        condition_code = condition_map.get(condition, 0)

        # Predict category
        prediction = model.predict([[condition_code, temperature]])[0]

        # Log the request to CSV
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "condition": condition,
            "temperature": temperature,
            "predicted_category": prediction
        }

        df = pd.DataFrame([log_entry])
        if os.path.exists(LOG_FILE):
            df.to_csv(LOG_FILE, mode='a', header=False, index=False)
        else:
            df.to_csv(LOG_FILE, index=False)

        return jsonify({"category": prediction})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/dashboard")
def dashboard():
    if not os.path.exists(LOG_FILE):
        return jsonify({"message": "No analytics data yet."})

    df = pd.read_csv(LOG_FILE)
    summary = {
        "total_predictions": len(df),
        "most_common_category": df["predicted_category"].mode()[0] if not df.empty else None,
        "average_temperature": round(df["temperature"].mean(), 2),
        "condition_distribution": df["condition"].value_counts().to_dict()
    }
    return jsonify(summary)


if __name__ == "__main__":
    app.run(debug=True)
