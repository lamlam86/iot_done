"""
🔬 LOCAL SIMULATOR - Mô phỏng hệ thống IoT Air Quality
Chạy KHÔNG CẦN kết nối Blynk - Test logic hệ thống
"""

import time
import random
from datetime import datetime, timedelta

# ============================================
# MÔ PHỎNG GIÁ TRỊ CẢM BIẾN
# ============================================
def simulate_sensor_values(hour):
    """
    Mô phỏng giá trị cảm biến theo thời gian trong ngày
    """
    # Base values
    base_co = 1.5
    base_air_quality = 100
    base_dust = 30
    base_noise = 40
    
    # Pattern theo giờ
    if 7 <= hour <= 9:  # Morning rush
        rush_factor = 1.8
        period = "🌅 Giờ cao điểm sáng"
    elif 17 <= hour <= 19:  # Evening rush
        rush_factor = 2.2
        period = "🌆 Giờ cao điểm chiều"
    elif 0 <= hour <= 5:  # Late night
        rush_factor = 0.5
        period = "🌙 Đêm khuya"
    elif 10 <= hour <= 16:  # Daytime
        rush_factor = 1.2
        period = "☀️ Ban ngày"
    else:
        rush_factor = 1.0
        period = "🕐 Bình thường"
    
    # Random variation
    random_factor = random.uniform(0.85, 1.15)
    
    # Tính giá trị
    co_level = base_co * rush_factor * random_factor + random.uniform(-0.2, 0.2)
    air_quality = base_air_quality * rush_factor * random_factor + random.uniform(-15, 15)
    dust_pm25 = base_dust * rush_factor * random_factor + random.uniform(-8, 8)
    noise_level = base_noise + random.uniform(-5, 10) + (15 if 8 <= hour <= 22 else 0)
    
    # Clamp values
    co_level = max(0.1, min(co_level, 15))
    air_quality = max(10, min(air_quality, 400))
    dust_pm25 = max(5, min(dust_pm25, 300))
    noise_level = max(20, min(noise_level, 90))
    
    return {
        'co': round(co_level, 2),
        'air_quality': round(air_quality, 1),
        'dust': round(dust_pm25, 1),
        'noise': round(noise_level, 1),
        'period': period
    }

def get_alert_status(co, air_quality, dust, noise):
    """Xác định mức cảnh báo"""
    if co > 4 or air_quality > 200 or dust > 100 or noise > 80:
        return 2, "🔴 NGUY HIỂM", "Cần hành động ngay!"
    elif co > 2 or air_quality > 100 or dust > 50 or noise > 65:
        return 1, "🟡 CHÚ Ý", "Nên hạn chế tiếp xúc"
    else:
        return 0, "🟢 AN TOÀN", "Chất lượng không khí tốt"

def create_gauge(value, max_val, width=20):
    """Tạo thanh gauge đơn giản"""
    filled = int((value / max_val) * width)
    filled = min(filled, width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}]"

def print_dashboard(values, alert_level, alert_text, alert_msg, cycle):
    """In dashboard ra console"""
    
    print("\033[2J\033[H")  # Clear screen
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║           🌍 IOT AIR QUALITY MONITOR - SIMULATION                 ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    now = datetime.now()
    print(f"    ⏰ Thời gian: {now.strftime('%Y-%m-%d %H:%M:%S')}    📍 Cycle: #{cycle}")
    print(f"    📅 {values['period']}")
    print()
    
    # CO Level
    co_gauge = create_gauge(values['co'], 10)
    co_status = "🟢" if values['co'] < 2 else ("🟡" if values['co'] < 4 else "🔴")
    print(f"    💨 CO Level:       {values['co']:>6.2f} ppm    {co_gauge} {co_status}")
    
    # Air Quality
    aq_gauge = create_gauge(values['air_quality'], 300)
    aq_status = "🟢" if values['air_quality'] < 100 else ("🟡" if values['air_quality'] < 200 else "🔴")
    print(f"    🌫️  Air Quality:    {values['air_quality']:>6.1f} PPM    {aq_gauge} {aq_status}")
    
    # Dust PM2.5
    dust_gauge = create_gauge(values['dust'], 200)
    dust_status = "🟢" if values['dust'] < 50 else ("🟡" if values['dust'] < 100 else "🔴")
    print(f"    🌪️  Dust PM2.5:     {values['dust']:>6.1f} µg/m³  {dust_gauge} {dust_status}")
    
    # Noise
    noise_gauge = create_gauge(values['noise'], 100)
    noise_status = "🟢" if values['noise'] < 65 else ("🟡" if values['noise'] < 80 else "🔴")
    print(f"    🔊 Noise Level:    {values['noise']:>6.1f} dB     {noise_gauge} {noise_status}")
    
    print()
    print("    ─────────────────────────────────────────────────────────────")
    print()
    print(f"    📊 TRẠNG THÁI TỔNG:  {alert_text}")
    print(f"    💬 {alert_msg}")
    print()
    
    # LED Status
    led_r = "🔴" if alert_level == 2 else "⚫"
    led_y = "🟡" if alert_level == 1 else "⚫"
    led_g = "🟢" if alert_level == 0 else "⚫"
    buzzer = "🔔 ON" if alert_level == 2 else "🔕 OFF"
    
    print(f"    LED Status: {led_g} {led_y} {led_r}     Buzzer: {buzzer}")
    print()
    
    # Blynk Virtual Pins
    print("    ┌─────────────────────────────────────────────────────────┐")
    print("    │  📱 BLYNK VIRTUAL PINS (sẽ gửi lên cloud)              │")
    print("    ├─────────────────────────────────────────────────────────┤")
    print(f"    │  V0 (CO):         {values['co']:>8.2f}                         │")
    print(f"    │  V1 (Air):        {values['air_quality']:>8.1f}                         │")
    print(f"    │  V2 (Dust):       {values['dust']:>8.1f}                         │")
    print(f"    │  V3 (Noise):      {values['noise']:>8.1f}                         │")
    print(f"    │  V5 (Alert):      {alert_level:>8}                         │")
    print("    └─────────────────────────────────────────────────────────┘")
    print()
    print("    ⏳ Cập nhật sau 3 giây... (Nhấn Ctrl+C để dừng)")

def run_simulation():
    """Main simulation loop"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║     🔬 IOT AIR QUALITY SIMULATOR (LOCAL MODE)                     ║
    ║     Mô phỏng KHÔNG CẦN phần cứng, KHÔNG CẦN Blynk                ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║     ✅ Test logic cảm biến                                        ║
    ║     ✅ Test ngưỡng cảnh báo                                       ║
    ║     ✅ Test LED/Buzzer simulation                                 ║
    ║     ✅ Xem data sẽ gửi lên Blynk                                  ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║     Nhấn Ctrl+C để dừng                                           ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    input("    Nhấn Enter để bắt đầu mô phỏng...")
    
    cycle = 0
    while True:
        try:
            cycle += 1
            current_hour = datetime.now().hour
            
            # Simulate values
            values = simulate_sensor_values(current_hour)
            alert_level, alert_text, alert_msg = get_alert_status(
                values['co'], 
                values['air_quality'], 
                values['dust'], 
                values['noise']
            )
            
            # Display dashboard
            print_dashboard(values, alert_level, alert_text, alert_msg, cycle)
            
            # Wait
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n\n    🛑 Đã dừng mô phỏng!")
            print("    ✅ Hệ thống hoạt động bình thường!\n")
            break

if __name__ == "__main__":
    run_simulation()
