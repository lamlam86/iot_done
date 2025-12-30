"""
🤖 SIMULATION VỚI AI THẬT (CatBoost Model)
==========================================
Script này:
1. Giả lập sensor data
2. Gửi đến Flask AI Server (server.py)
3. Nhận prediction từ model CatBoost THẬT
4. Gửi lên Blynk Cloud

CÁCH CHẠY:
1. Mở Terminal 1: python server.py (chạy AI server)
2. Mở Terminal 2: python simulation_real_ai.py (chạy script này)
"""

import requests
import time
import random
import numpy as np
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#                    CẤU HÌNH
# ═══════════════════════════════════════════════════════════════

BLYNK_TOKEN = "zBEZC5F7mKjnyTmB-dkDqZZrt2HT1Sog"
BLYNK_API = "https://blynk.cloud/external/api"
AI_SERVER = "http://localhost:5000/predict"  # Flask server

# Lịch sử data (cần cho feature engineering)
history_co = [random.uniform(1, 5) for _ in range(48)]
history_c6h6 = [random.uniform(5, 15) for _ in range(48)]

# ═══════════════════════════════════════════════════════════════
#                    FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════

def create_features(co_value, c6h6_value, hour):
    """
    Tạo 27 features giống như khi train model
    """
    global history_co, history_c6h6
    
    # Cập nhật history
    history_co.append(co_value)
    history_co.pop(0)
    history_c6h6.append(c6h6_value)
    history_c6h6.pop(0)
    
    # Lấy giá trị từ history
    co_lag_1hr = history_co[-2] if len(history_co) > 1 else co_value
    co_lag_24hr = history_co[-25] if len(history_co) > 24 else co_value
    c6h6_lag_1hr = history_c6h6[-2] if len(history_c6h6) > 1 else c6h6_value
    c6h6_lag_24hr = history_c6h6[-25] if len(history_c6h6) > 24 else c6h6_value
    
    # Rolling features
    co_roll_mean_3hr = np.mean(history_co[-4:-1]) if len(history_co) > 3 else co_value
    c6h6_roll_mean_3hr = np.mean(history_c6h6[-4:-1]) if len(history_c6h6) > 3 else c6h6_value
    co_roll_mean_24hr = np.mean(history_co[-25:-1]) if len(history_co) > 24 else co_value
    co_roll_std_24hr = np.std(history_co[-25:-1]) if len(history_co) > 24 else 0.5
    co_roll_max_24hr = max(history_co[-25:-1]) if len(history_co) > 24 else co_value
    c6h6_roll_mean_24hr = np.mean(history_c6h6[-25:-1]) if len(history_c6h6) > 24 else c6h6_value
    c6h6_roll_std_24hr = np.std(history_c6h6[-25:-1]) if len(history_c6h6) > 24 else 1.0
    c6h6_roll_max_24hr = max(history_c6h6[-25:-1]) if len(history_c6h6) > 24 else c6h6_value
    
    # Difference features
    co_diff_1hr = co_value - co_lag_1hr
    co_diff_24hr = co_value - co_lag_24hr
    c6h6_diff_1hr = c6h6_value - c6h6_lag_1hr
    c6h6_diff_24hr = c6h6_value - c6h6_lag_24hr
    
    # Cyclical time features
    hour_sin = np.sin(2 * np.pi * hour / 24.0)
    hour_cos = np.cos(2 * np.pi * hour / 24.0)
    day_of_week = datetime.now().weekday()
    day_sin = np.sin(2 * np.pi * day_of_week / 7.0)
    day_cos = np.cos(2 * np.pi * day_of_week / 7.0)
    
    # Interaction features
    c6h6_diff_x_hour_sin = c6h6_diff_1hr * hour_sin
    c6h6_diff_x_hour_cos = c6h6_diff_1hr * hour_cos
    co_diff_x_hour_sin = co_diff_1hr * hour_sin
    co_diff_x_hour_cos = co_diff_1hr * hour_cos
    
    # State features
    is_daytime = 1 if 7 <= hour <= 20 else 0
    is_morning_rush = 1 if 7 <= hour <= 9 else 0
    is_evening_rush = 1 if 17 <= hour <= 19 else 0
    
    # Trả về dict với 27 features
    return {
        'hour_sin': hour_sin,
        'hour_cos': hour_cos,
        'day_sin': day_sin,
        'day_cos': day_cos,
        'CO_lag_1hr': co_lag_1hr,
        'CO_lag_24hr': co_lag_24hr,
        'C6H6_lag_1hr': c6h6_lag_1hr,
        'C6H6_lag_24hr': c6h6_lag_24hr,
        'CO_roll_mean_3hr': co_roll_mean_3hr,
        'C6H6_roll_mean_3hr': c6h6_roll_mean_3hr,
        'CO_roll_mean_24hr': co_roll_mean_24hr,
        'CO_roll_std_24hr': co_roll_std_24hr,
        'CO_roll_max_24hr': co_roll_max_24hr,
        'C6H6_roll_mean_24hr': c6h6_roll_mean_24hr,
        'C6H6_roll_std_24hr': c6h6_roll_std_24hr,
        'C6H6_roll_max_24hr': c6h6_roll_max_24hr,
        'CO_diff_1hr': co_diff_1hr,
        'CO_diff_24hr': co_diff_24hr,
        'C6H6_diff_1hr': c6h6_diff_1hr,
        'C6H6_diff_24hr': c6h6_diff_24hr,
        'C6H6_diff_x_hour_sin': c6h6_diff_x_hour_sin,
        'C6H6_diff_x_hour_cos': c6h6_diff_x_hour_cos,
        'CO_diff_x_hour_sin': co_diff_x_hour_sin,
        'CO_diff_x_hour_cos': co_diff_x_hour_cos,
        'is_daytime': is_daytime,
        'is_morning_rush': is_morning_rush,
        'is_evening_rush': is_evening_rush
    }

# ═══════════════════════════════════════════════════════════════
#                    GỌI AI SERVER
# ═══════════════════════════════════════════════════════════════

def get_ai_prediction(features):
    """
    Gửi features đến Flask AI Server và nhận prediction
    """
    try:
        response = requests.post(AI_SERVER, json=features, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ AI Server error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Không kết nối được AI Server! Chạy 'python server.py' trước.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
#                    GỬI LÊN BLYNK
# ═══════════════════════════════════════════════════════════════

def send_to_blynk(data):
    try:
        params = "&".join([f"{k}={v}" for k, v in data.items()])
        url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&{params}"
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except:
        return False

# ═══════════════════════════════════════════════════════════════
#                    GIẢ LẬP SENSOR
# ═══════════════════════════════════════════════════════════════

def simulate_sensors(hour):
    factor = 1.8 if 7 <= hour <= 9 else (2.0 if 17 <= hour <= 19 else (0.5 if hour <= 5 else 1.0))
    
    # CO: 0.5 - 10 mg/m³ (thực tế)
    co = round(2.5 * factor * random.uniform(0.7, 1.3), 2)
    
    # C6H6 (Benzene): 2 - 30 µg/m³ (thực tế)
    c6h6 = round(10 * factor * random.uniform(0.8, 1.2), 2)
    
    # Air Quality Index (tính từ CO và C6H6)
    air = round(50 + co * 10 + c6h6 * 2 + random.uniform(-10, 10), 1)
    
    # Dust và Noise
    dust = round(30 * factor * random.uniform(0.8, 1.2), 1)
    noise = round(50 + random.uniform(-15, 25), 1)
    
    return {
        'air': air,
        'co': co,
        'c6h6': c6h6,
        'dust': dust,
        'noise': noise
    }

# ═══════════════════════════════════════════════════════════════
#                    MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🤖 SIMULATION VỚI AI THẬT (CatBoost Model)                        ║
║                                                                      ║
║   ⚠️  Đảm bảo đã chạy: python server.py (trong terminal khác)       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print("🔄 Kiểm tra kết nối AI Server...")
    test_features = create_features(3.0, 10.0, 12)
    test_result = get_ai_prediction(test_features)
    
    if test_result:
        print("✅ AI Server đã kết nối!")
        print(f"   Test prediction: CO={test_result.get('predicted_CO', 'N/A')}, C6H6={test_result.get('predicted_C6H6', 'N/A')}")
    else:
        print("❌ AI Server chưa chạy!")
        print("   👉 Mở terminal khác và chạy: python server.py")
        print("   👉 Sau đó chạy lại script này")
        return
    
    print("\n🚀 Bắt đầu simulation với AI THẬT...\n")
    time.sleep(2)
    
    while True:
        try:
            hour = datetime.now().hour
            
            # 1. Giả lập sensor
            sensor = simulate_sensors(hour)
            
            # 2. Tính alert level
            alert = 2 if (sensor['air'] >= 200 or sensor['co'] >= 10) else (1 if (sensor['air'] >= 100 or sensor['co'] >= 5) else 0)
            
            # 3. Tạo features cho AI
            features = create_features(sensor['co'], sensor['c6h6'], hour)
            
            # 4. 🤖 GỌI AI SERVER THẬT
            ai_result = get_ai_prediction(features)
            
            if ai_result:
                ai_co = round(ai_result.get('predicted_CO', 0), 2)
                ai_c6h6 = round(ai_result.get('predicted_C6H6', 0), 2)
                ai_air = round(50 + ai_co * 10 + ai_c6h6 * 2, 1)
                ai_alert = 2 if (ai_air >= 200 or ai_co >= 10) else (1 if (ai_air >= 100 or ai_co >= 5) else 0)
            else:
                ai_co, ai_c6h6, ai_air, ai_alert = 0, 0, 0, 0
            
            # 5. Gửi lên Blynk
            blynk_ok = send_to_blynk({
                'v0': sensor['air'],
                'v1': sensor['co'],
                'v2': sensor['dust'],
                'v3': sensor['noise'],
                'v4': alert,
                'v5': ai_air,
                'v6': ai_co,
                'v7': ai_alert
            })
            
            # 6. Hiển thị
            status_icon = "🟢" if alert == 0 else ("🟡" if alert == 1 else "🔴")
            ai_icon = "🟢" if ai_alert == 0 else ("🟡" if ai_alert == 1 else "🔴")
            
            print(f"{'═'*70}")
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | Blynk: {'✅' if blynk_ok else '❌'} | AI Server: {'✅' if ai_result else '❌'}")
            print(f"{'─'*70}")
            print(f"📊 SENSOR DATA:")
            print(f"   Air={sensor['air']:.0f} | CO={sensor['co']:.2f} mg/m³ | C6H6={sensor['c6h6']:.2f} µg/m³")
            print(f"   Dust={sensor['dust']:.0f} µg/m³ | Noise={sensor['noise']:.0f} dB | {status_icon}")
            print(f"{'─'*70}")
            print(f"🤖 AI PREDICTION (CatBoost Model THẬT):")
            print(f"   Predicted CO: {ai_co:.2f} mg/m³")
            print(f"   Predicted C6H6: {ai_c6h6:.2f} µg/m³")
            print(f"   Predicted Air: {ai_air:.0f} | {ai_icon}")
            print(f"{'═'*70}\n")
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n🛑 Đã dừng simulation!")
            break

if __name__ == "__main__":
    main()
