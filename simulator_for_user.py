"""
🔬 IOT AIR QUALITY SIMULATOR
============================
Copy file này về máy tính và chạy: python simulator_for_user.py

Yêu cầu: Python 3.x (đã cài)
"""

import time
import random
from datetime import datetime

print("""
╔═══════════════════════════════════════════════════════════════════╗
║           🌍 IOT AIR QUALITY MONITOR - SIMULATION                 ║
║                                                                   ║
║   Mô phỏng hệ thống cảm biến chất lượng không khí & tiếng ồn     ║
║   Nhấn Ctrl+C để dừng                                             ║
╚═══════════════════════════════════════════════════════════════════╝
""")

input("Nhấn Enter để bắt đầu...")

cycle = 0
while True:
    try:
        cycle += 1
        hour = datetime.now().hour
        
        # Xác định thời điểm trong ngày
        if 7 <= hour <= 9:
            factor = 2.0
            period = "🚗 Giờ cao điểm sáng (7-9h)"
        elif 17 <= hour <= 19:
            factor = 2.2
            period = "🚗 Giờ cao điểm chiều (17-19h)"  
        elif 0 <= hour <= 5:
            factor = 0.5
            period = "🌙 Đêm khuya (0-5h)"
        else:
            factor = 1.0
            period = "☀️ Bình thường"
        
        # Mô phỏng giá trị cảm biến
        co = round(1.5 * factor * random.uniform(0.7, 1.3), 2)
        air = round(100 * factor * random.uniform(0.7, 1.3), 1)
        dust = round(30 * factor * random.uniform(0.7, 1.3), 1)
        noise = round(45 + random.uniform(-10, 20), 1)
        
        # Xác định mức cảnh báo
        if co > 4 or air > 200 or dust > 100 or noise > 80:
            alert = "🔴 NGUY HIỂM - Cần hành động ngay!"
            level = 2
            led = "⚫ ⚫ 🔴"
            buzzer = "🔔 BẬT"
        elif co > 2 or air > 100 or dust > 50 or noise > 65:
            alert = "🟡 CHÚ Ý - Nên hạn chế tiếp xúc"
            level = 1
            led = "⚫ 🟡 ⚫"
            buzzer = "🔕 TẮT"
        else:
            alert = "🟢 AN TOÀN - Chất lượng không khí tốt"
            level = 0
            led = "🟢 ⚫ ⚫"
            buzzer = "🔕 TẮT"
        
        # Hiển thị dashboard
        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Cycle #{cycle}  |  ⏰ {datetime.now().strftime('%H:%M:%S')}  |  {period}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   💨 CO Level:      {co:>7.2f} ppm      {'🟢' if co < 2 else '🟡' if co < 4 else '🔴'} {'(An toàn < 2)' if co < 2 else '(Cao!)' if co > 4 else '(Chú ý)'}
   🌫️  Air Quality:   {air:>7.1f} PPM      {'🟢' if air < 100 else '🟡' if air < 200 else '🔴'} {'(An toàn < 100)' if air < 100 else '(Cao!)' if air > 200 else '(Chú ý)'}
   🌪️  Dust PM2.5:    {dust:>7.1f} µg/m³   {'🟢' if dust < 50 else '🟡' if dust < 100 else '🔴'} {'(An toàn < 50)' if dust < 50 else '(Cao!)' if dust > 100 else '(Chú ý)'}
   🔊 Noise Level:   {noise:>7.1f} dB      {'🟢' if noise < 65 else '🟡' if noise < 80 else '🔴'} {'(An toàn < 65)' if noise < 65 else '(Cao!)' if noise > 80 else '(Chú ý)'}

┌─────────────────────────────────────────────────────────────────────┐
│  📊 TRẠNG THÁI: {alert:<50} │
├─────────────────────────────────────────────────────────────────────┤
│  🚨 LED: {led}              Buzzer: {buzzer}                       │
└─────────────────────────────────────────────────────────────────────┘

   📱 Data sẽ gửi lên Blynk Cloud:
      V0 (CO) = {co}
      V1 (Air Quality) = {air}
      V2 (Dust PM2.5) = {dust}
      V3 (Noise) = {noise}
      V5 (Alert Level) = {level}

⏳ Cập nhật sau 3 giây...
""")
        
        time.sleep(3)
        
    except KeyboardInterrupt:
        print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛑 ĐÃ DỪNG MÔ PHỎNG

✅ Hệ thống hoạt động bình thường!
✅ Khi có phần cứng, data sẽ được gửi lên Blynk Cloud
✅ Bạn sẽ nhận thông báo trên điện thoại khi ô nhiễm cao
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        break
