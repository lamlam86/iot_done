# Progress Tracker: IoT Air Quality Prediction System
*Version: 1.0*
*Updated: 2025-12-30*

## Project Status
Overall Completion: **85%**

## What Works

### Data Pipeline ✅
- `clean3.csv`: 9,357 hourly samples (March 2004 - April 2005)
- Feature engineering: 27 features fully implemented
- Unit conversion: ppm→mg/m³, ppb→µg/m³
- Historical synthesis: Load matching Month/Day from previous year

### ML Models ✅
- **CO(GT) Model**: R²=0.836, MAE=0.361, RMSE=0.539
- **C6H6(GT) Model**: R²=0.818, MAE=1.664, RMSE=2.590
- Hyperparameter tuning: 50 Optuna trials completed
- Models saved: `catboost_co_model.pkl`, `catboost_c6h6_model.pkl`

### API Server ✅
- Flask server: `server.py` on port 5000
- Endpoints: `/` (health), `/predict` (POST)
- Input: 27 features as JSON
- Output: CO and C6H6 predictions

### Hardware ✅
- Circuit design: Arduino + MQ135 + MQ3 + ESP8266
- Arduino code: `curcuit/curcuit.ino` with MQ library
- ESP8266 code: Blynk integration on V0, V1
- Schematics available: `curcuit/layout.png`, `curcuit/schematic.png`

### Visualization ✅
- `metric_R2.png`: R² scores bar chart
- `metric_MAE_RMSE.png`: Error metrics comparison
- `train_val_loss.png`: Training/validation loss curves
- `residual_analysis.png`: Error analysis by hour/weekday

## What's In Progress

### Production Deployment - 30%
- Server.py tested locally
- Cần setup trên cloud (Heroku/Railway/VPS)
- Cần configure domain/SSL

### Automation - 20%
- datapipe.py script ready
- Cần cron job để chạy mỗi giờ
- Cần alerting khi prediction thất bại

## What's Left To Build

### Priority 1 (High)
- [ ] Deploy Flask server lên production
- [ ] Setup cron/scheduler cho data pipeline
- [ ] Implement proper logging system
- [ ] Add input validation trên API

### Priority 2 (Medium)
- [ ] Calibrate MQ sensors với reference values
- [ ] Build Blynk dashboard với gauges/charts
- [ ] Add confidence intervals cho predictions
- [ ] Implement batch prediction endpoint

### Priority 3 (Low)
- [ ] Mobile notification khi pollution high
- [ ] Historical data storage (database)
- [ ] Model retraining pipeline
- [ ] Multi-sensor network support

## Known Issues

### Issue 1: Evening Rush Errors
- **Severity**: Medium
- **Description**: MAE tăng cao vào 19-21h
- **Root cause**: High variability trong evening rush hour
- **Status**: Documented, accepted limitation

### Issue 2: ESP8266 Empty File
- **Severity**: Low
- **Description**: `curcuit/esp8266.ino` is empty
- **Workaround**: Use `esp8266/esp8266/esp8266.ino` instead
- **Status**: Needs cleanup

### Issue 3: Hardcoded Blynk Token
- **Severity**: Medium
- **Description**: Token exposed trong source code
- **Fix needed**: Move to environment variable
- **Status**: Open

### Issue 4: Sensor Calibration
- **Severity**: Medium
- **Description**: MQ sensor R0 values are defaults
- **Impact**: Real-world readings may be off
- **Status**: Needs field calibration

## Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| Data Cleaning | Complete | ✅ Done |
| Model Training | R² > 0.80 | ✅ Achieved (0.82-0.84) |
| API Development | Working endpoint | ✅ Done |
| Hardware Prototype | Sensors + WiFi | ✅ Done |
| Production Deploy | Live server | ⏳ In Progress |
| Full Integration | End-to-end working | 🔜 Pending |

## Performance Metrics Summary

```
┌───────────────┬──────────────┬──────────────┐
│    Metric     │    CO(GT)    │   C6H6(GT)   │
├───────────────┼──────────────┼──────────────┤
│ R² Score      │    0.836     │    0.818     │
│ MAE           │    0.361     │    1.664     │
│ RMSE          │    0.539     │    2.590     │
│ Best Iteration│    ~800-900  │    ~600-700  │
└───────────────┴──────────────┴──────────────┘
```

## Training Configuration
- Train set: 70% (~6,550 samples)
- Validation set: 15% (~1,400 samples)
- Test set: 15% (~1,400 samples)
- Optuna trials: 50
- Best learning rate: 0.0307
- Best depth: 5

---

*This document tracks what works, what's in progress, and what's left to build.*
