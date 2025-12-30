from flask import Flask, request, jsonify
import joblib
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
MODEL_CO_FILE = 'catboost_co_model.pkl'
MODEL_C6H6_FILE = 'catboost_c6h6_model.pkl'

# Confirmed 27 features from your training script
FEATURE_COLS = [
    'hour_sin', 'hour_cos', 
    'day_sin', 'day_cos',
    'CO_lag_1hr', 'CO_lag_24hr',
    'C6H6_lag_1hr', 'C6H6_lag_24hr',
    'CO_roll_mean_3hr', 'C6H6_roll_mean_3hr',
    'CO_roll_mean_24hr', 'CO_roll_std_24hr', 'CO_roll_max_24hr',
    'C6H6_roll_mean_24hr', 'C6H6_roll_std_24hr', 'C6H6_roll_max_24hr',
    'CO_diff_1hr', 'CO_diff_24hr',
    'C6H6_diff_1hr', 'C6H6_diff_24hr',
    'C6H6_diff_x_hour_sin', 'C6H6_diff_x_hour_cos',
    'CO_diff_x_hour_sin', 'CO_diff_x_hour_cos',
    'is_daytime',
    'is_morning_rush',
    'is_evening_rush'
]

def load_models():
    try:
        model_co = joblib.load(MODEL_CO_FILE)
        model_c6h6 = joblib.load(MODEL_C6H6_FILE)
        return model_co, model_c6h6
    except Exception as e:
        print(f"Error loading models: {e}")
        return None, None

model_co, model_c6h6 = load_models()

def featurize_single_input(data: dict) -> pd.DataFrame:
    # This server expects the CLIENT (your pipeline) to have pre-calculated all 27 features.
    try:
        df_input = pd.DataFrame([data])
        return df_input[FEATURE_COLS]
    except KeyError as e:
        raise ValueError(f"Missing required feature: {e}. The model expects all 27 features.")

@app.route('/predict', methods=['POST'])
def predict():
    if model_co is None or model_c6h6 is None:
        return jsonify({'error': 'Models not loaded. Check server logs.'}), 500
        
    try:
        json_data = request.json
        X_predict = featurize_single_input(json_data)

        co_pred = model_co.predict(X_predict)[0]
        c6h6_pred = model_c6h6.predict(X_predict)[0]
        
        response = {
            'CO(GT)_prediction': float(co_pred),
            'C6H6(GT)_prediction': float(c6h6_pred)
        }
        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        return jsonify({'error': 'An internal server error occurred during prediction.'}), 500

@app.route('/')
def health_check():
    return jsonify({'status': 'ok', 'message': 'Prediction Service Running'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)