"""
🚀 FULL SYSTEM SIMULATION
==========================
Mô phỏng TOÀN BỘ hệ thống IoT + AI + Blynk Cloud

Luồng xử lý:
1. Giả lập sensor đọc dữ liệu
2. Gửi lên Blynk Cloud (V0-V4)
3. AI dự đoán giá trị tương lai
4. Gửi kết quả AI lên Blynk (V5-V8)
5. Hiển thị dashboard

Chạy: python full_simulation.py
"""

import requests
import time
import random
import math
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════════════════════
#                    CẤU HÌNH BLYNK CLOUD
# ══════════════════════════════════════════════════════════════════════

BLYNK_TOKEN = "zBEZC5F7mKjnyTmB-dkDqZZrt2HT1Sog"
BLYNK_SERVER = "https://blynk.cloud/external/api"

# Virtual Pins mapping
PINS = {
    'air': 'v0',        # Air Quality Index (MQ-135)
    'co': 'v1',         # CO Level ppm (MQ-7)
    'dust': 'v2',       # PM2.5 ug/m3 (GP2Y1010AU0F)
    'noise': 'v3',      # Noise dB (KY-038)
    'alert': 'v4',      # Current Alert Level (0/1/2)
    'ai_air': 'v5',     # AI Predicted Air Quality
    'ai_co': 'v6',      # AI Predicted CO
    'ai_alert': 'v7',   # AI Predicted Alert Level
    'ai_status': 'v8',  # AI Status Message
}

# ══════════════════════════════════════════════════════════════════════
#                    NGƯỠNG CẢNH BÁO
# ══════════════════════════════════════════════════════════════════════

THRESHOLDS = {
    'air': {'good': 50, 'moderate': 100, 'unhealthy': 200},
    'co': {'safe': 9, 'warning': 35, 'danger': 100},
    'dust': {'good': 35, 'moderate': 75, 'unhealthy': 150},
    'noise': {'quiet': 55, 'moderate': 70, 'loud': 85}
}

# ══════════════════════════════════════════════════════════════════════
#                    LỊCH SỬ DỮ LIỆU (cho AI)
# ══════════════════════════════════════════════════════════════════════

history = {
    'air': [random.uniform(40, 80) for _ in range(24)],
    'co': [random.uniform(2, 8) for _ in range(24)],
    'dust': [random.uniform(20, 50) for _ in range(24)],
    'noise': [random.uniform(40, 60) for _ in range(24)]
}

# ══════════════════════════════════════════════════════════════════════
#                    HÀM GỬI DATA LÊN BLYNK
# ══════════════════════════════════════════════════════════════════════

def send_to_blynk(pin, value):
    """Gửi 1 giá trị lên Blynk Cloud"""
    try:
        url = f"{BLYNK_SERVER}/update?token={BLYNK_TOKEN}&{pin}={value}"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        return False

def send_batch_to_blynk(data_dict):
    """Gửi nhiều giá trị cùng lúc"""
    try:
        params = "&".join([f"{pin}={value}" for pin, value in data_dict.items()])
        url = f"{BLYNK_SERVER}/update?token={BLYNK_TOKEN}&{params}"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        return False

def get_from_blynk(pin):
    """Đọc giá trị từ Blynk Cloud"""
    try:
        url = f"{BLYNK_SERVER}/get?token={BLYNK_TOKEN}&{pin}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()[0]
        return None
    except:
        return None

# ══════════════════════════════════════════════════════════════════════
#                    GIẢ LẬP CẢM BIẾN
# ══════════════════════════════════════════════════════════════════════

def simulate_sensors(hour):
    """
    Giả lập dữ liệu từ 4 cảm biến
    - Thay đổi theo giờ trong ngày (giờ cao điểm ô nhiễm hơn)
    - Thêm random noise
    """
    # Hệ số theo giờ
    if 7 <= hour <= 9:      # Giờ cao điểm sáng
        factor = 1.8
    elif 17 <= hour <= 19:  # Giờ cao điểm chiều
        factor = 2.0
    elif 11 <= hour <= 13:  # Giờ trưa
        factor = 1.3
    elif 0 <= hour <= 5:    # Đêm khuya
        factor = 0.5
    else:
        factor = 1.0
    
    # Base values + factor + noise
    air = 60 * factor * random.uniform(0.8, 1.2)
    co = 4 * factor * random.uniform(0.7, 1.3)
    dust = 35 * factor * random.uniform(0.8, 1.2)
    noise = 50 + random.uniform(-15, 25) + (15 if 8 <= hour <= 22 else -10)
    
    return {
        'air': round(air, 1),
        'co': round(co, 2),
        'dust': round(dust, 1),
        'noise': round(noise, 1)
    }

# ══════════════════════════════════════════════════════════════════════
#                    TÍNH MỨC CẢNH BÁO
# ══════════════════════════════════════════════════════════════════════

def calculate_alert(air, co, dust, noise):
    """Tính mức cảnh báo: 0=An toàn, 1=Cảnh báo, 2=Nguy hiểm"""
    if (air >= THRESHOLDS['air']['unhealthy'] or 
        co >= THRESHOLDS['co']['danger'] or
        dust >= THRESHOLDS['dust']['unhealthy'] or 
        noise >= THRESHOLDS['noise']['loud']):
        return 2
    
    if (air >= THRESHOLDS['air']['moderate'] or 
        co >= THRESHOLDS['co']['warning'] or
        dust >= THRESHOLDS['dust']['moderate'] or 
        noise >= THRESHOLDS['noise']['moderate']):
        return 1
    
    return 0

# ══════════════════════════════════════════════════════════════════════
#                    🤖 AI PREDICTION
# ══════════════════════════════════════════════════════════════════════

def ai_predict(current_data, hour):
    """
    🤖 AI Prediction Algorithm
    
    Dự đoán giá trị sau 1 giờ dựa trên:
    1. Giá trị hiện tại
    2. Xu hướng từ lịch sử (trend)
    3. Mẫu theo giờ trong ngày
    4. Rolling average
    """
    global history
    
    # Cập nhật history
    for key in history:
        history[key].pop(0)
        history[key].append(current_data[key])
    
    # Tính trend
    def get_trend(data):
        recent = sum(data[-6:]) / 6
        older = sum(data[:6]) / 6
        return recent - older
    
    # Hệ số giờ tiếp theo
    next_hour = (hour + 1) % 24
    if 7 <= next_hour <= 9:
        hour_factor = 1.4
    elif 17 <= next_hour <= 19:
        hour_factor = 1.6
    elif 0 <= next_hour <= 5:
        hour_factor = 0.6
    else:
        hour_factor = 1.0
    
    # Dự đoán
    air_trend = get_trend(history['air'])
    co_trend = get_trend(history['co'])
    
    ai_air = current_data['air'] + (air_trend * 0.4)
    ai_air = ai_air * (hour_factor / (1.8 if 7 <= hour <= 9 else 2.0 if 17 <= hour <= 19 else 1.0))
    ai_air += random.uniform(-8, 8)
    
    ai_co = current_data['co'] + (co_trend * 0.3)
    ai_co = ai_co * (hour_factor / (1.8 if 7 <= hour <= 9 else 2.0 if 17 <= hour <= 19 else 1.0))
    ai_co += random.uniform(-0.5, 0.5)
    
    # Clamp values
    ai_air = max(10, min(400, ai_air))
    ai_co = max(0.5, min(80, ai_co))
    
    # Alert prediction
    ai_alert = calculate_alert(ai_air, ai_co, current_data['dust'], current_data['noise'])
    
    # Status message
    if ai_alert == 2:
        status = "NGUY HIEM!"
    elif ai_alert == 1:
        status = "CANH BAO"
    else:
        status = "AN TOAN"
    
    return {
        'ai_air': round(ai_air, 1),
        'ai_co': round(ai_co, 2),
        'ai_alert': ai_alert,
        'status': status
    }

# ══════════════════════════════════════════════════════════════════════
#                    HIỂN THỊ DASHBOARD
# ══════════════════════════════════════════════════════════════════════

def get_status_icon(level):
    if level == 0: return "🟢"
    if level == 1: return "🟡"
    return "🔴"

def print_dashboard(sensor_data, alert, ai_result, blynk_status):
    """In dashboard ra terminal"""
    now = datetime.now()
    next_hour = now + timedelta(hours=1)
    
    # Clear screen (cross-platform)
    print("\033[2J\033[H", end="")
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║   🌍 HỆ THỐNG IOT CẢNH BÁO Ô NHIỄM KHÔNG KHÍ + 🤖 AI PREDICTION                 ║
║                                                                                  ║
║   📡 Mô phỏng Full System: Sensor → Blynk Cloud → AI → Dashboard                ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"   ⏰ Thời gian: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   ☁️  Blynk Cloud: {'✅ Connected' if blynk_status else '❌ Disconnected'}")
    print()
    
    print("""┌────────────────────────────────────────────────────────────────────────────────┐
│                         📊 DỮ LIỆU CẢM BIẾN REALTIME                           │
├────────────────────────────────────────────────────────────────────────────────┤""")
    
    # Sensor data
    air_status = "🟢 Tốt" if sensor_data['air'] < 100 else ("🟡 TB" if sensor_data['air'] < 200 else "🔴 Xấu")
    co_status = "🟢 OK" if sensor_data['co'] < 9 else ("🟡 Chú ý" if sensor_data['co'] < 35 else "🔴 Nguy!")
    dust_status = "🟢 Tốt" if sensor_data['dust'] < 50 else ("🟡 TB" if sensor_data['dust'] < 100 else "🔴 Cao!")
    noise_status = "🟢 Yên" if sensor_data['noise'] < 65 else ("🟡 TB" if sensor_data['noise'] < 85 else "🔴 Ồn!")
    
    print(f"│   💨 MQ-135 Air Quality:     {sensor_data['air']:>7.1f} AQI      {air_status:<20}       │")
    print(f"│   🏭 MQ-7 CO Level:          {sensor_data['co']:>7.2f} ppm      {co_status:<20}       │")
    print(f"│   🌫️  GP2Y Dust PM2.5:        {sensor_data['dust']:>7.1f} µg/m³    {dust_status:<20}       │")
    print(f"│   🔊 KY-038 Noise:           {sensor_data['noise']:>7.1f} dB       {noise_status:<20}       │")
    print(f"│                                                                                │")
    print(f"│   {get_status_icon(alert)} TRẠNG THÁI: {'AN TOÀN' if alert == 0 else ('CẢNH BÁO' if alert == 1 else 'NGUY HIỂM!'):<30}                       │")
    
    print("""├────────────────────────────────────────────────────────────────────────────────┤
│                         🤖 AI PREDICTION (1 GIỜ TỚI)                           │
├────────────────────────────────────────────────────────────────────────────────┤""")
    
    # AI prediction
    air_change = ai_result['ai_air'] - sensor_data['air']
    co_change = ai_result['ai_co'] - sensor_data['co']
    air_arrow = f"⬆️ +{air_change:.0f}" if air_change > 0 else f"⬇️ {air_change:.0f}"
    co_arrow = f"⬆️ +{co_change:.1f}" if co_change > 0 else f"⬇️ {co_change:.1f}"
    
    print(f"│   🔮 Dự đoán lúc {next_hour.strftime('%H:%M')}:                                                      │")
    print(f"│                                                                                │")
    print(f"│   💨 Air Quality:  {ai_result['ai_air']:>7.1f} AQI    ({air_arrow})                                │")
    print(f"│   🏭 CO Level:     {ai_result['ai_co']:>7.2f} ppm    ({co_arrow})                                │")
    print(f"│                                                                                │")
    print(f"│   {get_status_icon(ai_result['ai_alert'])} Cảnh báo dự đoán: {ai_result['status']:<30}                      │")
    
    # Recommendation
    if ai_result['ai_alert'] == 2:
        rec = "🚨 Hạn chế ra ngoài! Bật máy lọc không khí!"
    elif ai_result['ai_alert'] == 1:
        if air_change > 20:
            rec = "⚠️ Không khí sẽ xấu đi. Nên đóng cửa sổ."
        else:
            rec = "📊 Theo dõi tình hình. Có thể sẽ cải thiện."
    else:
        if air_change < -10:
            rec = "✅ Xu hướng cải thiện! Có thể mở cửa thông gió."
        else:
            rec = "✅ Mọi thứ ổn định. Tiếp tục theo dõi."
    
    print(f"│                                                                                │")
    print(f"│   💡 Khuyến nghị: {rec:<55}  │")
    
    print("""├────────────────────────────────────────────────────────────────────────────────┤
│                         ☁️  BLYNK CLOUD DATA                                   │
├────────────────────────────────────────────────────────────────────────────────┤""")
    
    print(f"│   📤 Sensor Data:                                                              │")
    print(f"│      V0 (Air)   = {sensor_data['air']:<10.1f}  V1 (CO)    = {sensor_data['co']:<10.2f}              │")
    print(f"│      V2 (Dust)  = {sensor_data['dust']:<10.1f}  V3 (Noise) = {sensor_data['noise']:<10.1f}              │")
    print(f"│      V4 (Alert) = {alert:<10}                                                  │")
    print(f"│                                                                                │")
    print(f"│   📤 AI Data:                                                                  │")
    print(f"│      V5 (AI Air)   = {ai_result['ai_air']:<10.1f}  V6 (AI CO)    = {ai_result['ai_co']:<10.2f}        │")
    print(f"│      V7 (AI Alert) = {ai_result['ai_alert']:<10}  V8 (AI Status) = {ai_result['status']:<10}        │")
    
    print("""└────────────────────────────────────────────────────────────────────────────────┘""")
    
    print("\n   ⏳ Cập nhật mỗi 5 giây... (Nhấn Ctrl+C để dừng)")
    print("   📱 Mở Blynk App để xem dashboard trên điện thoại!")

# ══════════════════════════════════════════════════════════════════════
#                         MAIN LOOP
# ══════════════════════════════════════════════════════════════════════

def main():
    print("\n🚀 Khởi động Full System Simulation...")
    print("📡 Kết nối Blynk Cloud...")
    time.sleep(1)
    
    # Test Blynk connection
    test_result = send_to_blynk('v0', 0)
    if test_result:
        print("✅ Kết nối Blynk thành công!")
    else:
        print("⚠️ Không kết nối được Blynk. Chạy offline mode...")
    
    print("🤖 Khởi tạo AI Model...")
    time.sleep(1)
    print("✅ Sẵn sàng!\n")
    time.sleep(1)
    
    cycle = 0
    
    while True:
        try:
            cycle += 1
            hour = datetime.now().hour
            
            # ══════════ BƯỚC 1: GIẢ LẬP CẢM BIẾN ══════════
            sensor_data = simulate_sensors(hour)
            
            # ══════════ BƯỚC 2: TÍNH ALERT ══════════
            alert = calculate_alert(
                sensor_data['air'], 
                sensor_data['co'], 
                sensor_data['dust'], 
                sensor_data['noise']
            )
            
            # ══════════ BƯỚC 3: GỬI SENSOR DATA LÊN BLYNK ══════════
            blynk_ok = send_batch_to_blynk({
                'v0': sensor_data['air'],
                'v1': sensor_data['co'],
                'v2': sensor_data['dust'],
                'v3': sensor_data['noise'],
                'v4': alert
            })
            
            # ══════════ BƯỚC 4: AI PREDICTION ══════════
            ai_result = ai_predict(sensor_data, hour)
            
            # ══════════ BƯỚC 5: GỬI AI DATA LÊN BLYNK ══════════
            send_batch_to_blynk({
                'v5': ai_result['ai_air'],
                'v6': ai_result['ai_co'],
                'v7': ai_result['ai_alert'],
                'v8': ai_result['status']
            })
            
            # ══════════ BƯỚC 6: HIỂN THỊ DASHBOARD ══════════
            print_dashboard(sensor_data, alert, ai_result, blynk_ok)
            
            # Đợi 5 giây
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Đã dừng simulation!")
            print("✅ Cảm ơn bạn đã sử dụng hệ thống!\n")
            break

if __name__ == "__main__":
    main()
