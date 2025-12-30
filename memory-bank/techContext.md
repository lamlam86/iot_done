# Technical Context: IoT Air Quality Prediction System
*Version: 1.0*
*Updated: 2025-12-30*

## Technology Stack

### Hardware
- **Arduino UNO**: Main microcontroller
- **MQ135 Gas Sensor**: CO detection (Analog A0)
- **MQ3 Gas Sensor**: Benzene/C6H6 detection (Analog A1)
- **ESP8266 WiFi Module**: Network connectivity

### Software/Backend
- **Python 3.x**: Main programming language
- **Flask**: REST API framework
- **CatBoost**: Gradient boosting ML library
- **Pandas/NumPy**: Data processing
- **Optuna**: Hyperparameter optimization
- **Matplotlib/Seaborn**: Visualization
- **Joblib**: Model serialization

### Cloud/IoT
- **Blynk Cloud**: IoT data platform
  - Template ID: `TMPL6BxuCtIum`
  - Virtual Pins: V0 (CO), V1 (C6H6)

## Dependencies (requirements.txt)
```
Flask
pandas
numpy
catboost
joblib
```

**Additional for training:**
```
optuna
matplotlib
seaborn
scikit-learn
requests
```

## Feature Engineering Details

### 27 Model Features
```python
FEATURE_COLS = [
    # Cyclical Time Features (4)
    'hour_sin', 'hour_cos',      # Hour of day encoded cyclically
    'day_sin', 'day_cos',        # Day of week encoded cyclically
    
    # Lag Features (4)
    'CO_lag_1hr',                # CO value 1 hour ago
    'CO_lag_24hr',               # CO value 24 hours ago
    'C6H6_lag_1hr',              # C6H6 value 1 hour ago
    'C6H6_lag_24hr',             # C6H6 value 24 hours ago
    
    # Rolling Window Features - 3hr (2)
    'CO_roll_mean_3hr',          # Mean CO over last 3 hours
    'C6H6_roll_mean_3hr',        # Mean C6H6 over last 3 hours
    
    # Rolling Window Features - 24hr (6)
    'CO_roll_mean_24hr',         # Mean CO over last 24 hours
    'CO_roll_std_24hr',          # Std CO over last 24 hours
    'CO_roll_max_24hr',          # Max CO over last 24 hours
    'C6H6_roll_mean_24hr',       # Mean C6H6 over last 24 hours
    'C6H6_roll_std_24hr',        # Std C6H6 over last 24 hours
    'C6H6_roll_max_24hr',        # Max C6H6 over last 24 hours
    
    # Difference/Momentum Features (4)
    'CO_diff_1hr',               # Change in CO from 1hr ago
    'CO_diff_24hr',              # Change in CO from 24hr ago
    'C6H6_diff_1hr',             # Change in C6H6 from 1hr ago
    'C6H6_diff_24hr',            # Change in C6H6 from 24hr ago
    
    # Interaction Features (4)
    'C6H6_diff_x_hour_sin',      # Rate of change × time of day
    'C6H6_diff_x_hour_cos',
    'CO_diff_x_hour_sin',
    'CO_diff_x_hour_cos',
    
    # State Features (3)
    'is_daytime',                # Hour 7-20: 1, else 0
    'is_morning_rush',           # Hour 7-9: 1, else 0
    'is_evening_rush'            # Hour 17-19: 1, else 0
]
```

### Feature Creation Formulas
```python
# Cyclical encoding
hour_sin = sin(2π × Hour / 24)
hour_cos = cos(2π × Hour / 24)
day_sin = sin(2π × DayOfWeek / 7)
day_cos = cos(2π × DayOfWeek / 7)

# Lag features (shift BEFORE rolling to avoid data leakage)
CO_lag_1hr = CO(GT).shift(1)
CO_roll_mean_3hr = CO(GT).shift(1).rolling(window=3).mean()

# Difference features
CO_diff_1hr = CO(GT).diff(1).shift(1)
```

## Model Configuration

### Best Hyperparameters (via Optuna)
```python
best_params = {
    'learning_rate': 0.03065092459457942,
    'depth': 5,
    'l2_leaf_reg': 1.869560153272358,
    'subsample': 0.7367462866287637,
    'iterations': 3000,
    'early_stopping_rounds': 200,
    'random_seed': 42,
    'verbose': False
}
```

### Model Performance (Test Set)
| Metric | CO(GT) | C6H6(GT) |
|--------|--------|----------|
| R² Score | 0.836 | 0.818 |
| MAE | 0.361 | 1.664 |
| RMSE | 0.539 | 2.590 |

### Feature Importance (Top 5)
**CO Model:**
1. CO_lag_1hr
2. CO_roll_mean_3hr
3. CO_lag_24hr
4. CO_diff_1hr
5. hour_sin

**C6H6 Model:**
1. C6H6_lag_1hr
2. C6H6_roll_mean_3hr
3. C6H6_lag_24hr
4. C6H6_diff_1hr
5. hour_cos

## API Endpoints

### Health Check
```
GET /
Response: {"status": "ok", "message": "Prediction Service Running"}
```

### Prediction
```
POST /predict
Content-Type: application/json
Body: {27 features as key-value pairs}
Response: {
    "CO(GT)_prediction": float,
    "C6H6(GT)_prediction": float
}
```

## Unit Conversion Constants
```python
# CO: ppm to mg/m³ (at 20°C, 1 atm)
# Formula: mg/m³ = ppm × M × 0.0409, M(CO) = 28.01
CO_CONVERSION_FACTOR = 1.145

# C6H6: ppb to µg/m³ (at 20°C, 1 atm)
# Formula: µg/m³ = ppb × M × 0.0409, M(C6H6) = 78.11
C6H6_CONVERSION_FACTOR = 3.195
```

## Hardware Circuit Configuration

### Arduino Pin Mapping
| Pin | Connected To | Function |
|-----|--------------|----------|
| A0 | MQ135 Signal | CO sensor analog input |
| A1 | MQ3 Signal | C6H6 sensor analog input |
| D12 | ESP8266 RX | Serial TX (via voltage divider) |
| D13 | ESP8266 TX | Serial RX |
| 5V | Sensors VCC | Power |
| GND | Sensors GND | Ground |

### MQ Sensor Calibration
```cpp
// MQ135 for CO
MQ135 mq135(A0);  // R0=14, A=770.24, B=-4.065

// MQ3 for C6H6
MQ3 mq3(A1);      // R0=0.23, A=4.1376, B=-2.661
```

## Data Files

| File | Description | Rows |
|------|-------------|------|
| AirQualityUCI.csv | Original UCI dataset | 9,471 |
| clean3.csv | Cleaned, processed data | 9,357 |
| catboost_co_model.pkl | Trained CO model | - |
| catboost_c6h6_model.pkl | Trained C6H6 model | - |

## Environment Variables
```bash
PORT=5000  # Flask server port
BLYNK_TOKEN=tEueg4kzgsG7-RWTIhQF2FpeTrp5ORKE
```

---

*This document describes the technologies used in the project and how they're configured.*
