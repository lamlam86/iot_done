# Active Context: IoT Air Quality Prediction System
*Version: 1.0*
*Updated: 2025-12-30*
*Current RIPER Mode: RESEARCH*

## Current Focus
Dự án đã hoàn thành các components chính:
- ✅ Model training với CatBoost
- ✅ Flask API server
- ✅ Data pipeline automation
- ✅ Hardware circuit design
- ✅ ESP8266 + Blynk integration

## Recent Changes
- Model đã được train và tune với Optuna (50 trials)
- Best params đã được xác định và lưu
- Residual analysis hoàn thành (xem `residual_analysis.png`)
- Models đã được serialize thành `.pkl` files

## Active Decisions
- **Model Architecture**: 2 separate CatBoost models (1 cho CO, 1 cho C6H6)
- **Feature Set**: 27 features (confirmed stable)
- **Data Split**: 70/15/15 chronological split
- **Conversion**: Pipeline handles unit conversion (ppm→mg/m³, ppb→µg/m³)

## Next Steps
1. [ ] Deploy server.py on production (cloud/VPS)
2. [ ] Set up cron job cho datapipe.py (mỗi giờ)
3. [ ] Thêm logging và error handling
4. [ ] Tạo dashboard visualization trên Blynk app
5. [ ] Calibrate sensors với giá trị tham chiếu thực tế

## Current Challenges

### Challenge 1: Historical Data Dependency
- **Mô tả**: Pipeline cần 49 data points lịch sử để tạo features
- **Giải pháp hiện tại**: Synthesize từ clean3.csv (same Month/Day từ năm trước)
- **Rủi ro**: Mismatch nếu weather patterns khác biệt

### Challenge 2: Sensor Calibration
- **Mô tả**: R0 values trong mq.h là giá trị mặc định, chưa calibrate thực tế
- **Cần làm**: Calibrate trong clean air hoặc với reference gas

### Challenge 3: Error Patterns
- **Từ residual analysis**: 
  - MAE cao hơn vào giờ 19-21 (evening rush)
  - MAE cao hơn vào Friday
  - Có outliers với error > 3 cho CO

## Implementation Progress
- [✓] Data cleaning (AirQualityUCI.csv → clean3.csv)
- [✓] Feature engineering (27 features)
- [✓] Model training with Optuna tuning
- [✓] Model evaluation (R²=0.82-0.84)
- [✓] Flask API implementation
- [✓] Data pipeline script
- [✓] Arduino + ESP8266 code
- [ ] Production deployment
- [ ] Cron job setup
- [ ] Dashboard integration

## Key Files to Know
```
/workspace/
├── main.py          # Main training script with visualization
├── test.py          # Training with model saving
├── test2.py         # Alternative features (weekend rush)
├── server.py        # Flask prediction API
├── datapipe.py      # Automated data pipeline
├── clean3.csv       # Cleaned dataset
├── catboost_co_model.pkl     # Trained CO model
├── catboost_c6h6_model.pkl   # Trained C6H6 model
├── curcuit/
│   ├── curcuit.ino  # Arduino main code
│   ├── mq.h         # MQ sensor library
│   └── esp8266.ino  # (empty, use esp8266/esp8266/esp8266.ino)
└── esp8266/esp8266/esp8266.ino  # ESP8266 Blynk code
```

## Running the System

### Start Flask Server
```bash
cd /workspace
python server.py
# Server runs on http://0.0.0.0:5000
```

### Run Data Pipeline
```bash
cd /workspace
python datapipe.py
# Fetches from Blynk, creates features, sends to /predict
```

### Upload Arduino Code
1. Upload `curcuit/curcuit.ino` to Arduino
2. Upload `esp8266/esp8266/esp8266.ino` to ESP8266
3. Configure WiFi credentials in esp8266.ino

---

*This document captures the current state of work and immediate next steps.*
