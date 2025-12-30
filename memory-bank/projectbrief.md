# Project Brief: IoT Air Quality Prediction System
*Version: 1.0*
*Created: 2025-12-30*

## Project Overview
Hệ thống IoT dự đoán chất lượng không khí theo thời gian thực, kết hợp phần cứng cảm biến (Arduino + MQ sensors) với mô hình Machine Learning (CatBoost) để dự đoán nồng độ CO và C6H6 (Benzene) trong không khí trước 1 giờ.

## Core Requirements
- Thu thập dữ liệu từ cảm biến MQ135 (CO) và MQ3 (C6H6) qua Arduino
- Truyền dữ liệu qua WiFi bằng ESP8266 lên Blynk Cloud
- Xây dựng pipeline tự động lấy dữ liệu và tạo features
- Huấn luyện mô hình CatBoost để dự đoán nồng độ khí
- Triển khai Flask API server cho inference
- Dự đoán nồng độ khí cho giờ tiếp theo (T+1)

## Success Criteria
- R² Score > 0.80 cho cả CO và C6H6
- MAE cho CO(GT) < 0.40 mg/m³
- MAE cho C6H6(GT) < 2.0 µg/m³
- Pipeline tự động chạy mỗi giờ
- API response time < 500ms

## Scope

### In Scope
- Đo lường nồng độ CO (ppm → mg/m³)
- Đo lường nồng độ C6H6/Benzene (ppb → µg/m³)
- Dự đoán theo giờ dựa trên time-series features
- Web API cho real-time prediction
- Kết nối IoT qua Blynk Cloud

### Out of Scope
- Đo các loại khí khác (NOx, O3, etc.)
- Mobile app riêng (dùng Blynk app có sẵn)
- Long-term prediction (> 1 giờ)
- Multi-location deployment

## Key Components
1. **Hardware Layer**: Arduino + MQ135 + MQ3 + ESP8266
2. **Cloud Layer**: Blynk IoT Platform
3. **ML Pipeline**: CatBoost Regressor với 27 features
4. **API Layer**: Flask web server
5. **Data Pipeline**: `datapipe.py` automation script

## Data Source
UCI Air Quality Dataset - Italy (March 2004 - April 2005)
- ~9,357 hourly observations
- Đã được clean thành `clean3.csv`

---

*This document serves as the foundation for the project and informs all other memory files.*
