"""
🤖 AI SERVER SIMULATION
========================
Mô phỏng server AI dự đoán chất lượng không khí

Chạy: python ai_server_simulation.py
"""

import random
import time
import math
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════════════════════
#                         CẤU HÌNH
# ══════════════════════════════════════════════════════════════════════

# Ngưỡng cảnh báo
THRESHOLDS = {
    'air': {'good': 50, 'moderate': 100, 'unhealthy': 200, 'hazardous': 300},
    'co': {'safe': 9, 'warning': 35, 'danger': 100},
    'dust': {'good': 35, 'moderate': 75, 'unhealthy': 150},
    'noise': {'quiet': 55, 'moderate': 70, 'loud': 85}
}

# Lịch sử dữ liệu (giả lập 24 giờ)
history = {
    'air': [random.uniform(40, 80) for _ in range(24)],
    'co': [random.uniform(2, 8) for _ in range(24)],
    'dust': [random.uniform(20, 50) for _ in range(24)],
    'noise': [random.uniform(40, 60) for _ in range(24)]
}

# ══════════════════════════════════════════════════════════════════════
#                      CÁC HÀM AI
# ══════════════════════════════════════════════════════════════════════

def calculate_trend(data):
    """Tính xu hướng từ dữ liệu lịch sử"""
    recent = sum(data[-6:]) / 6  # 6 giờ gần nhất
    older = sum(data[:6]) / 6     # 6 giờ đầu
    return recent - older

def calculate_moving_average(data, window=6):
    """Tính trung bình động"""
    return sum(data[-window:]) / window

def predict_next_hour(current_value, history_data, hour_of_day):
    """
    🤖 AI Prediction Algorithm
    
    Dự đoán giá trị sau 1 giờ dựa trên:
    1. Giá trị hiện tại
    2. Xu hướng (trend)
    3. Mẫu theo giờ trong ngày
    4. Trung bình động
    """
    # 1. Tính xu hướng
    trend = calculate_trend(history_data)
    
    # 2. Hệ số theo giờ (giờ cao điểm ô nhiễm hơn)
    hour_factor = 1.0
    if 7 <= hour_of_day <= 9:      # Giờ cao điểm sáng
        hour_factor = 1.3
    elif 17 <= hour_of_day <= 19:  # Giờ cao điểm chiều
        hour_factor = 1.5
    elif 0 <= hour_of_day <= 5:    # Đêm khuya
        hour_factor = 0.7
    
    # 3. Trung bình động
    ma = calculate_moving_average(history_data)
    
    # 4. Tính dự đoán
    # Kết hợp: current + trend * 0.3 + (current - ma) * 0.2 + random noise
    prediction = current_value + (trend * 0.3) + ((current_value - ma) * 0.2)
    prediction *= hour_factor
    prediction += random.uniform(-5, 5)  # Noise
    
    return max(0, prediction)

def get_alert_level(air, co, dust, noise):
    """Xác định mức cảnh báo"""
    if (air >= THRESHOLDS['air']['unhealthy'] or 
        co >= THRESHOLDS['co']['danger'] or
        dust >= THRESHOLDS['dust']['unhealthy'] or 
        noise >= THRESHOLDS['noise']['loud']):
        return 2, "🔴 NGUY HIỂM"
    
    if (air >= THRESHOLDS['air']['moderate'] or 
        co >= THRESHOLDS['co']['warning'] or
        dust >= THRESHOLDS['dust']['moderate'] or 
        noise >= THRESHOLDS['noise']['moderate']):
        return 1, "🟡 CẢNH BÁO"
    
    return 0, "🟢 AN TOÀN"

def generate_recommendation(current, predicted, alert_level):
    """Tạo khuyến nghị dựa trên AI"""
    recommendations = []
    
    # So sánh xu hướng
    if predicted['air'] > current['air'] * 1.2:
        recommendations.append("⚠️ Chất lượng KK sẽ xấu đi! Nên đóng cửa sổ.")
    
    if predicted['co'] > current['co'] * 1.3:
        recommendations.append("⚠️ CO sẽ tăng! Kiểm tra thông gió.")
    
    if alert_level == 2:
        recommendations.append("🚨 Hạn chế ra ngoài trong 1-2 giờ tới!")
        recommendations.append("🏠 Nên ở trong nhà, bật máy lọc không khí.")
    elif alert_level == 1:
        recommendations.append("📊 Theo dõi tình hình, có thể sẽ cải thiện.")
    else:
        if predicted['air'] < current['air']:
            recommendations.append("✅ Xu hướng cải thiện! Có thể mở cửa thông gió.")
        else:
            recommendations.append("✅ Duy trì tình trạng tốt.")
    
    return recommendations

def simulate_sensor_data(hour):
    """Mô phỏng dữ liệu từ cảm biến"""
    # Base values
    base_air = 60
    base_co = 3
    base_dust = 30
    base_noise = 45
    
    # Hệ số theo giờ
    if 7 <= hour <= 9:
        factor = 1.8
    elif 17 <= hour <= 19:
        factor = 2.0
    elif 0 <= hour <= 5:
        factor = 0.5
    else:
        factor = 1.0
    
    return {
        'air': base_air * factor * random.uniform(0.8, 1.2),
        'co': base_co * factor * random.uniform(0.8, 1.2),
        'dust': base_dust * factor * random.uniform(0.8, 1.2),
        'noise': base_noise + random.uniform(-10, 20) + (10 if 8 <= hour <= 22 else 0)
    }

# ══════════════════════════════════════════════════════════════════════
#                      HIỂN THỊ
# ══════════════════════════════════════════════════════════════════════

def print_header():
    print("\033[2J\033[H")  # Clear screen
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     🤖 AI SERVER - HỆ THỐNG DỰ ĐOÁN CHẤT LƯỢNG KHÔNG KHÍ                    ║
║                                                                              ║
║     Mô phỏng server AI nhận dữ liệu từ IoT và dự đoán ô nhiễm               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

def print_dashboard(current, predicted, alert_current, alert_predicted, recommendations):
    now = datetime.now()
    next_hour = now + timedelta(hours=1)
    
    print(f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⏰ Thời gian: {now.strftime('%Y-%m-%d %H:%M:%S')}                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                         📊 DỮ LIỆU HIỆN TẠI                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    💨 Air Quality (MQ-135):    {current['air']:>7.1f} AQI    {get_status_icon(current['air'], 'air')}                        │
│    🏭 CO Level (MQ-7):         {current['co']:>7.2f} ppm    {get_status_icon(current['co'], 'co')}                        │
│    🌫️  Dust PM2.5 (GP2Y):       {current['dust']:>7.1f} µg/m³  {get_status_icon(current['dust'], 'dust')}                        │
│    🔊 Noise (KY-038):          {current['noise']:>7.1f} dB     {get_status_icon(current['noise'], 'noise')}                        │
│                                                                              │
│    📊 Trạng thái: {alert_current[1]:<30}                           │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                     🤖 AI PREDICTION ({next_hour.strftime('%H:%M')})                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    💨 Air Quality dự đoán:     {predicted['air']:>7.1f} AQI    {get_change_arrow(current['air'], predicted['air'])}                        │
│    🏭 CO Level dự đoán:        {predicted['co']:>7.2f} ppm    {get_change_arrow(current['co'], predicted['co'])}                        │
│                                                                              │
│    🔮 Cảnh báo dự đoán: {alert_predicted[1]:<30}                      │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                         💡 KHUYẾN NGHỊ AI                                    │
├──────────────────────────────────────────────────────────────────────────────┤""")
    
    for rec in recommendations[:4]:
        print(f"│    {rec:<72} │")
    
    print("""│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                        📱 DATA → BLYNK CLOUD                                 │
├──────────────────────────────────────────────────────────────────────────────┤""")
    print(f"│    V0={current['air']:.0f}  V1={current['co']:.1f}  V2={current['dust']:.0f}  V3={current['noise']:.0f}  V5={alert_current[0]}                            │")
    print(f"│    V6={predicted['air']:.0f} (AI)  V7={predicted['co']:.1f} (AI)  V8={alert_predicted[0]} (AI Alert)                      │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    print("\n    ⏳ Cập nhật sau 5 giây... (Nhấn Ctrl+C để dừng)")

def get_status_icon(value, sensor_type):
    thres = THRESHOLDS[sensor_type]
    if sensor_type == 'air':
        if value < thres['good']: return "🟢 Tốt"
        if value < thres['moderate']: return "🟡 TB"
        if value < thres['unhealthy']: return "🟠 Kém"
        return "🔴 Xấu!"
    elif sensor_type == 'co':
        if value < thres['safe']: return "🟢 OK"
        if value < thres['warning']: return "🟡 Chú ý"
        return "🔴 Nguy!"
    elif sensor_type == 'dust':
        if value < thres['good']: return "🟢 Tốt"
        if value < thres['moderate']: return "🟡 TB"
        return "🔴 Cao!"
    else:  # noise
        if value < thres['quiet']: return "🟢 Yên"
        if value < thres['moderate']: return "🟡 TB"
        return "🔴 Ồn!"

def get_change_arrow(current, predicted):
    diff = predicted - current
    pct = (diff / current) * 100 if current > 0 else 0
    if diff > 0:
        return f"⬆️ +{pct:.0f}%"
    elif diff < 0:
        return f"⬇️ {pct:.0f}%"
    return "➡️ 0%"

# ══════════════════════════════════════════════════════════════════════
#                         MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    print_header()
    print("    🚀 Khởi động AI Server...")
    print("    📊 Đang load model dự đoán...")
    time.sleep(2)
    print("    ✅ Sẵn sàng nhận dữ liệu từ IoT!\n")
    time.sleep(1)
    
    while True:
        try:
            # Lấy giờ hiện tại
            hour = datetime.now().hour
            
            # Mô phỏng nhận dữ liệu từ sensor
            current = simulate_sensor_data(hour)
            
            # Cập nhật history
            for key in history:
                history[key].pop(0)
                history[key].append(current[key])
            
            # 🤖 AI Prediction
            predicted = {
                'air': predict_next_hour(current['air'], history['air'], hour),
                'co': predict_next_hour(current['co'], history['co'], hour),
                'dust': current['dust'],  # Giữ nguyên
                'noise': current['noise']  # Giữ nguyên
            }
            
            # Tính alert level
            alert_current = get_alert_level(current['air'], current['co'], current['dust'], current['noise'])
            alert_predicted = get_alert_level(predicted['air'], predicted['co'], predicted['dust'], predicted['noise'])
            
            # Tạo khuyến nghị
            recommendations = generate_recommendation(current, predicted, alert_predicted[0])
            
            # Hiển thị
            print_header()
            print_dashboard(current, predicted, alert_current, alert_predicted, recommendations)
            
            # Đợi 5 giây
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n    🛑 Đã dừng AI Server!")
            print("    ✅ Cảm ơn bạn đã sử dụng hệ thống!\n")
            break

if __name__ == "__main__":
    main()
