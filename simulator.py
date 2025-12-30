"""
🔬 SIMULATOR - Mô phỏng hệ thống IoT Air Quality
Chạy file này để test Blynk Dashboard mà không cần phần cứng!
"""

import requests
import time
import random
import math
from datetime import datetime

# ============================================
# CẤU HÌNH BLYNK - THAY BẰNG TOKEN CỦA BẠN!
# ============================================
BLYNK_AUTH_TOKEN = "zBEZC5F7mKjnyTmB-dkDqZZrt2HT1Soga"  # Token của bạn
BLYNK_SERVER = "https://blynk.cloud/external/api"

# ============================================
# HÀM GỬI DATA LÊN BLYNK
# ============================================
def send_to_blynk(pin, value):
    """Gửi giá trị lên Blynk Virtual Pin"""
    url = f"{BLYNK_SERVER}/update?token={BLYNK_AUTH_TOKEN}&{pin}={value}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Lỗi gửi {pin}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False

# ============================================
# MÔ PHỎNG GIÁ TRỊ CẢM BIẾN
# ============================================
def simulate_sensor_values(hour):
    """
    Mô phỏng giá trị cảm biến theo thời gian trong ngày
    - Giờ cao điểm (7-9h, 17-19h): Ô nhiễm cao hơn
    - Ban đêm: Ô nhiễm thấp hơn
    """
    
    # Base values
    base_co = 1.5
    base_air_quality = 100
    base_dust = 30
    base_noise = 40
    
    # Thêm pattern theo giờ (giờ cao điểm ô nhiễm hơn)
    if 7 <= hour <= 9:  # Morning rush
        rush_factor = 1.8
    elif 17 <= hour <= 19:  # Evening rush
        rush_factor = 2.2
    elif 0 <= hour <= 5:  # Late night - clean
        rush_factor = 0.5
    else:
        rush_factor = 1.0
    
    # Thêm random variation
    random_factor = random.uniform(0.8, 1.2)
    
    # Tính giá trị cuối cùng
    co_level = base_co * rush_factor * random_factor + random.uniform(-0.3, 0.3)
    air_quality = base_air_quality * rush_factor * random_factor + random.uniform(-20, 20)
    dust_pm25 = base_dust * rush_factor * random_factor + random.uniform(-10, 10)
    noise_level = base_noise + random.uniform(-5, 15) + (10 if 8 <= hour <= 22 else 0)
    
    # Đảm bảo giá trị hợp lệ
    co_level = max(0.1, min(co_level, 15))
    air_quality = max(10, min(air_quality, 400))
    dust_pm25 = max(5, min(dust_pm25, 300))
    noise_level = max(20, min(noise_level, 90))
    
    return {
        'co': round(co_level, 2),
        'air_quality': round(air_quality, 1),
        'dust': round(dust_pm25, 1),
        'noise': round(noise_level, 1)
    }

def get_alert_status(co, air_quality, dust, noise):
    """Xác định mức cảnh báo (0=Safe, 1=Warning, 2=Danger)"""
    if co > 4 or air_quality > 200 or dust > 100 or noise > 80:
        return 2  # Danger
    elif co > 2 or air_quality > 100 or dust > 50 or noise > 65:
        return 1  # Warning
    else:
        return 0  # Safe

def print_status(values, alert):
    """In trạng thái ra console"""
    alert_text = ["🟢 AN TOÀN", "🟡 CHÚ Ý", "🔴 NGUY HIỂM"][alert]
    
    print("\n" + "="*60)
    print(f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print(f"  💨 CO Level:      {values['co']:>6} ppm")
    print(f"  🌫️  Air Quality:   {values['air_quality']:>6} PPM")
    print(f"  🌪️  Dust PM2.5:    {values['dust']:>6} µg/m³")
    print(f"  🔊 Noise Level:   {values['noise']:>6} dB")
    print("-"*60)
    print(f"  📊 Alert Status:  {alert_text}")
    print("="*60)

# ============================================
# MAIN SIMULATION LOOP
# ============================================
def run_simulation():
    """Chạy mô phỏng liên tục"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     🔬 IOT AIR QUALITY SIMULATOR                          ║
    ║     Mô phỏng dữ liệu cảm biến gửi lên Blynk              ║
    ╠═══════════════════════════════════════════════════════════╣
    ║     Nhấn Ctrl+C để dừng                                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    print(f"🔑 Token: {BLYNK_AUTH_TOKEN[:10]}...")
    print(f"🌐 Server: {BLYNK_SERVER}")
    print("\n⏳ Bắt đầu mô phỏng...\n")
    
    # Test kết nối
    print("🔌 Kiểm tra kết nối Blynk...")
    if send_to_blynk("v0", 0):
        print("✅ Kết nối Blynk thành công!\n")
    else:
        print("❌ Không thể kết nối Blynk. Kiểm tra Token!")
        return
    
    cycle = 0
    while True:
        try:
            cycle += 1
            current_hour = datetime.now().hour
            
            # Mô phỏng giá trị cảm biến
            values = simulate_sensor_values(current_hour)
            alert = get_alert_status(
                values['co'], 
                values['air_quality'], 
                values['dust'], 
                values['noise']
            )
            
            # Gửi lên Blynk
            print(f"\n📤 Gửi data lên Blynk (Cycle #{cycle})...")
            
            send_to_blynk("v0", values['co'])
            send_to_blynk("v1", values['air_quality'])
            send_to_blynk("v2", values['dust'])
            send_to_blynk("v3", values['noise'])
            send_to_blynk("v5", alert)
            
            # In trạng thái
            print_status(values, alert)
            
            # Đợi 5 giây rồi gửi tiếp
            print("\n⏳ Đợi 5 giây...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Đã dừng mô phỏng!")
            break

# ============================================
# CHẠY CHƯƠNG TRÌNH
# ============================================
if __name__ == "__main__":
    run_simulation()
