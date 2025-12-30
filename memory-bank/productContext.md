# Product Context: IoT Air Quality Prediction System
*Version: 1.0*
*Updated: 2025-12-30*

## Problem Statement
Ô nhiễm không khí, đặc biệt là CO (Carbon Monoxide) và C6H6 (Benzene), gây ra các vấn đề sức khỏe nghiêm trọng. Cần có hệ thống:
- Giám sát liên tục nồng độ các chất ô nhiễm
- Dự báo trước để người dùng có thể chuẩn bị/phòng tránh
- Chi phí thấp, dễ triển khai cho cá nhân/gia đình

## User Personas

### Home User
- Demographics: Gia đình có trẻ nhỏ hoặc người già
- Goals: Biết chất lượng không khí trong nhà để bảo vệ sức khỏe
- Pain Points: Không có cách đo lường, không biết khi nào nên mở/đóng cửa sổ

### Urban Commuter
- Demographics: Người làm việc văn phòng ở thành phố lớn
- Goals: Biết thời điểm tránh ra ngoài khi ô nhiễm cao
- Pain Points: Ô nhiễm cao vào giờ cao điểm, cần dự báo để lên kế hoạch

## User Experience Goals
- Real-time monitoring qua Blynk app (V0: CO, V1: C6H6)
- Dự báo 1 giờ trước với độ chính xác cao (R² > 0.80)
- Đơn giản hóa việc lắp đặt phần cứng (DIY friendly)

## Key Features
- **Real-time Sensing**: Đọc giá trị từ MQ135 và MQ3 mỗi giây, gửi lên cloud mỗi phút
- **Historical Synthesis**: Tổng hợp 48 giờ dữ liệu lịch sử để tạo features
- **Feature Engineering**: 27 features bao gồm lag, rolling, cyclical, interaction
- **Prediction API**: Flask endpoint `/predict` trả về dự đoán CO và C6H6

## Target Pollutants

### CO (Carbon Monoxide)
- **Nguồn**: Khí thải xe cộ, đốt cháy không hoàn toàn
- **Đơn vị gốc từ sensor**: ppm (parts per million)
- **Đơn vị model**: mg/m³
- **Conversion factor**: 1.145 (ppm → mg/m³)
- **Ngưỡng WHO**: 9 ppm (trung bình 8 giờ)

### C6H6 (Benzene)
- **Nguồn**: Khí thải xe, nhiên liệu hóa thạch, công nghiệp
- **Đơn vị gốc từ sensor**: ppb (parts per billion)
- **Đơn vị model**: µg/m³
- **Conversion factor**: 3.195 (ppb → µg/m³)
- **Ngưỡng WHO**: 1.7 µg/m³ (trung bình năm)

## Success Metrics
- **Model R²**: Target > 0.80 (Achieved: CO=0.836, C6H6=0.818)
- **MAE CO**: Target < 0.40 (Achieved: 0.361)
- **MAE C6H6**: Target < 2.0 (Achieved: 1.664)
- **System uptime**: Target > 99%

---

*This document explains why the project exists and what problems it solves.*
