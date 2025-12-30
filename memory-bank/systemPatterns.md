# System Patterns: IoT Air Quality Prediction System
*Version: 1.0*
*Updated: 2025-12-30*

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      HARDWARE LAYER                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐   │
│  │ MQ135   │───▶│ Arduino │───▶│ ESP8266 │───▶│ Blynk Cloud │   │
│  │ (CO)    │    │   UNO   │    │  WiFi   │    │   (V0, V1)  │   │
│  └─────────┘    │         │    └─────────┘    └─────────────┘   │
│  ┌─────────┐    │  A0,A1  │                                      │
│  │  MQ3    │───▶│  Pins   │                                      │
│  │ (C6H6)  │    └─────────┘                                      │
│  └─────────┘                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SOFTWARE LAYER                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ datapipe.py │───▶│ server.py   │───▶│ Prediction Response │  │
│  │ (Pipeline)  │    │ (Flask API) │    │ CO, C6H6 for T+1    │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│         │                  │                                     │
│         ▼                  ▼                                     │
│  ┌─────────────┐    ┌─────────────┐                             │
│  │ clean3.csv  │    │ .pkl models │                             │
│  │ (History)   │    │ CO, C6H6    │                             │
│  └─────────────┘    └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Hardware Components
- **MQ135 Sensor**: Đo CO trên pin A0
  - R0 (calibration) = 14
  - Công thức: PPM = 770.24 × (Rs/R0)^(-4.065)
  
- **MQ3 Sensor**: Đo C6H6 trên pin A1
  - R0 (calibration) = 0.23
  - Công thức: PPB = 4.1376 × (Rs/R0)^(-2.661) × 1000

- **ESP8266**: WiFi module, giao tiếp qua SoftwareSerial (Pin 12-TX, Pin 13-RX)

### 2. Software Components
- **main.py / test.py**: Training script với CatBoost + Optuna tuning
- **server.py**: Flask API server (port 5000)
- **datapipe.py**: Automated data pipeline
- **mq.h**: Arduino library cho MQ sensors

## Data Flow

```
[Sensor] → [Arduino] → CSV format: "val1,val2\n"
    ↓
[ESP8266] → Parse và gửi lên Blynk (V0, V1)
    ↓
[datapipe.py] → Fetch từ Blynk API mỗi giờ
    ↓
[Feature Engineering] → Tạo 27 features từ history + new data
    ↓
[Flask API] → Load model, predict, return JSON
```

## Design Patterns in Use

### Time Series Feature Engineering
- **Lag Features**: Shift 1hr, 24hr để capture immediate và daily patterns
- **Rolling Windows**: Mean, std, max over 3hr và 24hr
- **Cyclical Encoding**: Sin/cos transformation cho Hour và Day of Week
- **Interaction Features**: Diff × cyclical để capture rate of change theo thời gian

### Chronological Data Split
```python
# 70% Train, 15% Validation, 15% Test
# KHÔNG shuffle - giữ thứ tự thời gian
n_train = int(N * 0.70)
n_val = int(N * 0.15)
n_test = N - n_train - n_val
```

### Early Stopping Pattern
```python
best_params = {
    'iterations': 3000,
    'early_stopping_rounds': 200,  # Stop if no improvement
    ...
}
```

## Key Technical Decisions

### 1. CatBoost over other algorithms
- **Rationale**: Handles missing values, fast inference, no need for categorical encoding
- **Alternative considered**: XGBoost, LightGBM

### 2. Separate models for CO and C6H6
- **Rationale**: Different dynamics, allows independent tuning
- **Models saved**: `catboost_co_model.pkl`, `catboost_c6h6_model.pkl`

### 3. Historical data synthesis for pipeline
- **Rationale**: Sensor chỉ có T (current), cần 48+ points cho features
- **Solution**: Lấy data từ năm trước (same Month/Day) trong `clean3.csv`

### 4. Unit conversion at pipeline level
- **Rationale**: Model trained on mg/m³ và µg/m³, sensor outputs ppm và ppb
- **Location**: Trong `fetch_and_average_data()` của `datapipe.py`

## Component Relationships

```
┌──────────────────────────────────────────────────────────────┐
│                    TRAINING FLOW                              │
│                                                               │
│  clean3.csv → Feature Engineering → CatBoost → .pkl models   │
│       │              │                   │                    │
│       │              │                   └── Optuna tuning    │
│       │              │                                        │
│       │              └── 27 features (see techContext.md)     │
│       │                                                       │
│       └── 9,357 hourly samples (2004-2005)                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    INFERENCE FLOW                             │
│                                                               │
│  Blynk API → datapipe.py → Flask /predict → JSON response    │
│       │           │              │                            │
│       │           │              └── Load .pkl models         │
│       │           │                                           │
│       │           └── Engineer same 27 features               │
│       │                                                       │
│       └── V0 (CO ppm), V1 (C6H6 ppb)                         │
└──────────────────────────────────────────────────────────────┘
```

---

*This document captures the system architecture and design patterns used in the project.*
