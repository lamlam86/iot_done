# BƯỚC 1: Cài đặt Phần mềm

## 1.1 Arduino IDE

### Download
1. Truy cập: https://www.arduino.cc/en/software
2. Chọn phiên bản phù hợp với OS (Windows/Mac/Linux)
3. Download và cài đặt

### Cài Driver CH340 (cho Arduino clone)
- Windows: https://sparks.gogo.co.nz/ch340.html
- Mac: Tự động nhận
- Linux: Đã có sẵn

## 1.2 Cài đặt Board ESP8266

1. Mở Arduino IDE
2. Vào **File → Preferences**
3. Trong ô **Additional Board Manager URLs**, thêm:
   ```
   http://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
4. Vào **Tools → Board → Boards Manager**
5. Tìm **"esp8266"** và cài đặt **"ESP8266 by ESP8266 Community"**

## 1.3 Cài đặt Libraries cần thiết

Vào **Sketch → Include Library → Manage Libraries**, tìm và cài:

| Library | Phiên bản | Mục đích |
|---------|-----------|----------|
| **Blynk** | Latest | Kết nối Blynk Cloud |
| **LiquidCrystal_I2C** | Latest | Điều khiển LCD I2C |
| **SoftwareSerial** | (có sẵn) | Giao tiếp Serial với ESP8266 |

## 1.4 Cài đặt Python (cho Server)

### Windows
1. Download Python 3.10+: https://www.python.org/downloads/
2. **QUAN TRỌNG**: Tick ✅ "Add Python to PATH" khi cài

### Mac/Linux
```bash
# Mac
brew install python3

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip
```

### Kiểm tra cài đặt
```bash
python --version
pip --version
```

## 1.5 Cài đặt thư viện Python

```bash
pip install flask pandas numpy catboost joblib requests
```

---

✅ **Hoàn thành Bước 1** - Tiếp tục sang Bước 2: Lắp ráp phần cứng
