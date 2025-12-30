// ════════════════════════════════════════════════════════════════════
// ĐỒ ÁN: HỆ THỐNG IOT CẢNH BÁO Ô NHIỄM KHÔNG KHÍ VÀ TIẾNG ỒN
// ════════════════════════════════════════════════════════════════════
// Thiết bị:
//   - Arduino UNO R3
//   - MQ-135: Cảm biến chất lượng không khí
//   - MQ-7: Cảm biến CO (Carbon Monoxide)
//   - GP2Y1010AU0F: Cảm biến bụi PM2.5
//   - KY-038: Cảm biến tiếng ồn
//   - LCD 16x2 I2C: Màn hình hiển thị
//   - LED (Đỏ, Vàng, Xanh): Đèn cảnh báo
//   - Buzzer: Còi báo động
//   - ESP8266: Module WiFi (gửi data lên Blynk)
// ════════════════════════════════════════════════════════════════════

#include <LiquidCrystal_I2C.h>

// ══════════════════ CẤU HÌNH CHÂN CẢM BIẾN ══════════════════
// Trong mô phỏng: dùng Potentiometer thay cho cảm biến thật
const int PIN_MQ135 = A0;      // Cảm biến chất lượng không khí (Air Quality)
const int PIN_MQ7 = A1;        // Cảm biến CO (Carbon Monoxide)
const int PIN_DUST = A2;       // Cảm biến bụi PM2.5 (GP2Y1010AU0F)
const int PIN_SOUND = A3;      // Cảm biến tiếng ồn (KY-038)

// ══════════════════ CẤU HÌNH CHÂN OUTPUT ══════════════════
const int LED_GREEN = 5;       // LED Xanh - An toàn
const int LED_YELLOW = 6;      // LED Vàng - Cảnh báo
const int LED_RED = 7;         // LED Đỏ - Nguy hiểm
const int BUZZER = 8;          // Buzzer cảnh báo
const int LED_DUST = 9;        // LED điều khiển cảm biến bụi (GP2Y1010AU0F)

// ══════════════════ NGƯỠNG CẢNH BÁO ══════════════════
// Cảm biến MQ-135 (Air Quality Index)
const float AIR_GOOD = 50;       // Tốt
const float AIR_MODERATE = 100;  // Trung bình
const float AIR_UNHEALTHY = 200; // Không lành mạnh
const float AIR_HAZARDOUS = 300; // Nguy hại

// Cảm biến MQ-7 (CO - ppm)
const float CO_SAFE = 9;         // An toàn (WHO indoor)
const float CO_WARNING = 35;     // Cảnh báo
const float CO_DANGER = 100;     // Nguy hiểm

// Cảm biến GP2Y1010AU0F (Bụi PM2.5 - µg/m³)
const float DUST_GOOD = 35;      // Tốt (WHO)
const float DUST_MODERATE = 75;  // Trung bình
const float DUST_UNHEALTHY = 150;// Không lành mạnh

// Cảm biến KY-038 (Tiếng ồn - dB)
const float NOISE_QUIET = 55;    // Yên tĩnh
const float NOISE_MODERATE = 70; // Trung bình
const float NOISE_LOUD = 85;     // Ồn (có hại thính giác)

// ══════════════════ LCD I2C ══════════════════
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ══════════════════ BIẾN TOÀN CỤC ══════════════════
unsigned long lastLCDUpdate = 0;
unsigned long lastSerialPrint = 0;
unsigned long lastBuzzerBeep = 0;
int displayPage = 0;
const int NUM_PAGES = 5;

// Biến lưu giá trị cảm biến
float airQuality = 0;
float coLevel = 0;
float dustLevel = 0;
float noiseLevel = 0;
int alertLevel = 0;

// ══════════════════ CUSTOM CHARACTERS ══════════════════
byte warningChar[] = {
  B00100,
  B00100,
  B01110,
  B01110,
  B11111,
  B11111,
  B00100,
  B00000
};

byte safeChar[] = {
  B00000,
  B00001,
  B00010,
  B10100,
  B01000,
  B00000,
  B00000,
  B00000
};

// ════════════════════════════════════════════════════════════════════
//                              SETUP
// ════════════════════════════════════════════════════════════════════
void setup() {
  // Khởi tạo Serial
  Serial.begin(9600);
  
  // Khởi tạo LCD
  lcd.init();
  lcd.backlight();
  lcd.createChar(0, warningChar);
  lcd.createChar(1, safeChar);
  
  // Cấu hình chân OUTPUT
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(LED_DUST, OUTPUT);
  
  // Tắt tất cả output ban đầu
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_RED, LOW);
  digitalWrite(BUZZER, LOW);
  
  // Màn hình chào
  showWelcomeScreen();
  
  // In thông tin khởi động
  printStartupInfo();
}

// ════════════════════════════════════════════════════════════════════
//                           MÀN HÌNH CHÀO
// ════════════════════════════════════════════════════════════════════
void showWelcomeScreen() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  DO AN IOT     ");
  lcd.setCursor(0, 1);
  lcd.print(" Air & Noise    ");
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Canh bao o nhiem");
  lcd.setCursor(0, 1);
  lcd.print("Khong khi&Tieng on");
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Dang khoi dong..");
  for (int i = 0; i < 16; i++) {
    lcd.setCursor(i, 1);
    lcd.print("=");
    delay(100);
  }
  delay(500);
  lcd.clear();
}

// ════════════════════════════════════════════════════════════════════
//                      IN THÔNG TIN KHỞI ĐỘNG
// ════════════════════════════════════════════════════════════════════
void printStartupInfo() {
  Serial.println();
  Serial.println(F("╔════════════════════════════════════════════════════════════╗"));
  Serial.println(F("║     HE THONG IOT CANH BAO O NHIEM KHONG KHI & TIENG ON    ║"));
  Serial.println(F("╠════════════════════════════════════════════════════════════╣"));
  Serial.println(F("║  Thiet bi:                                                 ║"));
  Serial.println(F("║    - MQ-135: Cam bien chat luong khong khi (A0)           ║"));
  Serial.println(F("║    - MQ-7:   Cam bien CO - Carbon Monoxide (A1)           ║"));
  Serial.println(F("║    - GP2Y1010AU0F: Cam bien bui PM2.5 (A2)                ║"));
  Serial.println(F("║    - KY-038: Cam bien tieng on (A3)                       ║"));
  Serial.println(F("║    - LCD 16x2 I2C: Man hinh hien thi                      ║"));
  Serial.println(F("║    - LED (R/Y/G): Den canh bao                            ║"));
  Serial.println(F("║    - Buzzer: Coi bao dong                                 ║"));
  Serial.println(F("╠════════════════════════════════════════════════════════════╣"));
  Serial.println(F("║  Huong dan mo phong:                                       ║"));
  Serial.println(F("║    - Xoay POT1 (A0): Thay doi Air Quality (0-500)         ║"));
  Serial.println(F("║    - Xoay POT2 (A1): Thay doi CO Level (0-200 ppm)        ║"));
  Serial.println(F("║    - Xoay POT3 (A2): Thay doi Dust PM2.5 (0-500 ug/m3)    ║"));
  Serial.println(F("║    - Xoay POT4 (A3): Thay doi Noise (30-120 dB)           ║"));
  Serial.println(F("╚════════════════════════════════════════════════════════════╝"));
  Serial.println();
}

// ════════════════════════════════════════════════════════════════════
//                         ĐỌC CẢM BIẾN
// ════════════════════════════════════════════════════════════════════

// Đọc MQ-135 - Chất lượng không khí
float readMQ135() {
  int raw = analogRead(PIN_MQ135);
  // Chuyển đổi sang AQI (0-500)
  float aqi = map(raw, 0, 1023, 0, 500);
  return aqi;
}

// Đọc MQ-7 - Nồng độ CO
float readMQ7() {
  int raw = analogRead(PIN_MQ7);
  // Chuyển đổi sang ppm (0-200)
  float ppm = raw * 200.0 / 1023.0;
  return ppm;
}

// Đọc GP2Y1010AU0F - Bụi PM2.5
float readDustSensor() {
  // Bật LED của cảm biến bụi
  digitalWrite(LED_DUST, LOW);
  delayMicroseconds(280);
  
  int raw = analogRead(PIN_DUST);
  
  delayMicroseconds(40);
  digitalWrite(LED_DUST, HIGH);
  delayMicroseconds(9680);
  
  // Chuyển đổi sang µg/m³ (0-500)
  float dust = map(raw, 0, 1023, 0, 500);
  return dust;
}

// Đọc KY-038 - Tiếng ồn
float readSoundSensor() {
  // Đọc nhiều mẫu và lấy peak
  int maxSound = 0;
  for (int i = 0; i < 50; i++) {
    int sample = analogRead(PIN_SOUND);
    if (sample > maxSound) {
      maxSound = sample;
    }
    delayMicroseconds(200);
  }
  
  // Chuyển đổi sang dB (30-120)
  float db = map(maxSound, 0, 1023, 30, 120);
  return db;
}

// ════════════════════════════════════════════════════════════════════
//                      XÁC ĐỊNH MỨC CẢNH BÁO
// ════════════════════════════════════════════════════════════════════
int calculateAlertLevel(float air, float co, float dust, float noise) {
  int level = 0;  // 0=Safe, 1=Warning, 2=Danger
  
  // Kiểm tra từng cảm biến
  // MQ-135 (Air Quality)
  if (air >= AIR_HAZARDOUS) level = max(level, 2);
  else if (air >= AIR_UNHEALTHY) level = max(level, 2);
  else if (air >= AIR_MODERATE) level = max(level, 1);
  
  // MQ-7 (CO)
  if (co >= CO_DANGER) level = max(level, 2);
  else if (co >= CO_WARNING) level = max(level, 2);
  else if (co >= CO_SAFE) level = max(level, 1);
  
  // Dust PM2.5
  if (dust >= DUST_UNHEALTHY) level = max(level, 2);
  else if (dust >= DUST_MODERATE) level = max(level, 1);
  else if (dust >= DUST_GOOD) level = max(level, 1);
  
  // Noise
  if (noise >= NOISE_LOUD) level = max(level, 2);
  else if (noise >= NOISE_MODERATE) level = max(level, 1);
  
  return level;
}

// ════════════════════════════════════════════════════════════════════
//                         ĐIỀU KHIỂN LED
// ════════════════════════════════════════════════════════════════════
void updateLEDs(int level) {
  switch (level) {
    case 0:  // AN TOÀN
      digitalWrite(LED_GREEN, HIGH);
      digitalWrite(LED_YELLOW, LOW);
      digitalWrite(LED_RED, LOW);
      break;
    case 1:  // CẢNH BÁO
      digitalWrite(LED_GREEN, LOW);
      digitalWrite(LED_YELLOW, HIGH);
      digitalWrite(LED_RED, LOW);
      break;
    case 2:  // NGUY HIỂM
      digitalWrite(LED_GREEN, LOW);
      digitalWrite(LED_YELLOW, LOW);
      digitalWrite(LED_RED, HIGH);
      break;
  }
}

// ════════════════════════════════════════════════════════════════════
//                        ĐIỀU KHIỂN BUZZER
// ════════════════════════════════════════════════════════════════════
void updateBuzzer(int level) {
  unsigned long currentTime = millis();
  
  switch (level) {
    case 0:  // An toàn - Tắt buzzer
      noTone(BUZZER);
      break;
      
    case 1:  // Cảnh báo - Beep mỗi 3 giây
      if (currentTime - lastBuzzerBeep >= 3000) {
        tone(BUZZER, 1000, 200);
        lastBuzzerBeep = currentTime;
      }
      break;
      
    case 2:  // Nguy hiểm - Beep liên tục
      if (currentTime - lastBuzzerBeep >= 500) {
        tone(BUZZER, 2000, 300);
        lastBuzzerBeep = currentTime;
      }
      break;
  }
}

// ════════════════════════════════════════════════════════════════════
//                         CẬP NHẬT LCD
// ════════════════════════════════════════════════════════════════════
void updateLCD() {
  unsigned long currentTime = millis();
  
  // Chuyển trang mỗi 3 giây
  if (currentTime - lastLCDUpdate >= 3000) {
    displayPage = (displayPage + 1) % NUM_PAGES;
    lastLCDUpdate = currentTime;
    lcd.clear();
  }
  
  switch (displayPage) {
    case 0:  // Trang 1: MQ-135 Air Quality
      lcd.setCursor(0, 0);
      lcd.print("MQ-135 Air:");
      lcd.setCursor(0, 1);
      lcd.print("AQI: ");
      lcd.print((int)airQuality);
      lcd.print(" ");
      if (airQuality < AIR_GOOD) lcd.print("TOT");
      else if (airQuality < AIR_MODERATE) lcd.print("TB");
      else if (airQuality < AIR_UNHEALTHY) lcd.print("KEM");
      else lcd.print("XAU!");
      break;
      
    case 1:  // Trang 2: MQ-7 CO Level
      lcd.setCursor(0, 0);
      lcd.print("MQ-7 CO:");
      lcd.setCursor(0, 1);
      lcd.print(coLevel, 1);
      lcd.print(" ppm ");
      if (coLevel < CO_SAFE) lcd.print("OK");
      else if (coLevel < CO_WARNING) lcd.print("!");
      else lcd.print("NGUY!");
      break;
      
    case 2:  // Trang 3: Dust PM2.5
      lcd.setCursor(0, 0);
      lcd.print("GP2Y Bui PM2.5:");
      lcd.setCursor(0, 1);
      lcd.print((int)dustLevel);
      lcd.print(" ug/m3 ");
      if (dustLevel < DUST_GOOD) lcd.print("TOT");
      else if (dustLevel < DUST_MODERATE) lcd.print("TB");
      else lcd.print("CAO!");
      break;
      
    case 3:  // Trang 4: Noise Level
      lcd.setCursor(0, 0);
      lcd.print("KY-038 Tieng on:");
      lcd.setCursor(0, 1);
      lcd.print((int)noiseLevel);
      lcd.print(" dB ");
      if (noiseLevel < NOISE_QUIET) lcd.print("YEN TINH");
      else if (noiseLevel < NOISE_MODERATE) lcd.print("TB");
      else lcd.print("ON!");
      break;
      
    case 4:  // Trang 5: Trạng thái tổng
      lcd.setCursor(0, 0);
      lcd.print("==TRANG THAI==");
      lcd.setCursor(0, 1);
      if (alertLevel == 0) {
        lcd.write(1);  // Safe character
        lcd.print(" AN TOAN ");
        lcd.write(1);
      } else if (alertLevel == 1) {
        lcd.write(0);  // Warning character
        lcd.print(" CANH BAO ");
        lcd.write(0);
      } else {
        lcd.write(0);
        lcd.print(" NGUY HIEM! ");
        lcd.write(0);
      }
      break;
  }
}

// ════════════════════════════════════════════════════════════════════
//                       IN RA SERIAL MONITOR
// ════════════════════════════════════════════════════════════════════
void printToSerial() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastSerialPrint >= 2000) {
    lastSerialPrint = currentTime;
    
    Serial.println(F("┌────────────────────────────────────────────────────────────┐"));
    Serial.print(F("│ "));
    Serial.print(F("MQ-135 (Air Quality): "));
    Serial.print(airQuality, 0);
    Serial.print(F(" AQI"));
    printSpaces(35 - 22 - String(airQuality, 0).length());
    if (airQuality < AIR_GOOD) Serial.println(F("[TOT]       │"));
    else if (airQuality < AIR_MODERATE) Serial.println(F("[TRUNG BINH]│"));
    else if (airQuality < AIR_UNHEALTHY) Serial.println(F("[KEM]       │"));
    else Serial.println(F("[XAU!]      │"));
    
    Serial.print(F("│ "));
    Serial.print(F("MQ-7 (CO Level):      "));
    Serial.print(coLevel, 1);
    Serial.print(F(" ppm"));
    printSpaces(35 - 22 - String(coLevel, 1).length());
    if (coLevel < CO_SAFE) Serial.println(F("[AN TOAN]   │"));
    else if (coLevel < CO_WARNING) Serial.println(F("[CHU Y!]    │"));
    else Serial.println(F("[NGUY HIEM!]│"));
    
    Serial.print(F("│ "));
    Serial.print(F("GP2Y1010 (Dust PM2.5):"));
    Serial.print(dustLevel, 0);
    Serial.print(F(" ug/m3"));
    printSpaces(35 - 23 - String(dustLevel, 0).length());
    if (dustLevel < DUST_GOOD) Serial.println(F("[TOT]       │"));
    else if (dustLevel < DUST_MODERATE) Serial.println(F("[TRUNG BINH]│"));
    else Serial.println(F("[CAO!]      │"));
    
    Serial.print(F("│ "));
    Serial.print(F("KY-038 (Noise Level): "));
    Serial.print(noiseLevel, 0);
    Serial.print(F(" dB"));
    printSpaces(35 - 22 - String(noiseLevel, 0).length());
    if (noiseLevel < NOISE_QUIET) Serial.println(F("[YEN TINH]  │"));
    else if (noiseLevel < NOISE_MODERATE) Serial.println(F("[TRUNG BINH]│"));
    else Serial.println(F("[ON!]       │"));
    
    Serial.println(F("├────────────────────────────────────────────────────────────┤"));
    Serial.print(F("│ TRANG THAI: "));
    if (alertLevel == 0) {
      Serial.println(F("🟢 AN TOAN - Moi thu binh thuong!            │"));
    } else if (alertLevel == 1) {
      Serial.println(F("🟡 CANH BAO - Can chu y!                     │"));
    } else {
      Serial.println(F("🔴 NGUY HIEM - Can hanh dong ngay!           │"));
    }
    
    Serial.println(F("├────────────────────────────────────────────────────────────┤"));
    Serial.print(F("│ LED: "));
    Serial.print(alertLevel == 0 ? "🟢" : "⚫");
    Serial.print(alertLevel == 1 ? "🟡" : "⚫");
    Serial.print(alertLevel == 2 ? "🔴" : "⚫");
    Serial.print(F("  |  Buzzer: "));
    Serial.print(alertLevel == 0 ? "OFF" : (alertLevel == 1 ? "BEEP/3s" : "BEEP/0.5s"));
    Serial.println(F("              │"));
    
    Serial.println(F("├────────────────────────────────────────────────────────────┤"));
    Serial.println(F("│ >> Data gui len Blynk Cloud:                               │"));
    Serial.print(F("│    V0 (Air): ")); Serial.print(airQuality, 0);
    Serial.print(F("  V1 (CO): ")); Serial.print(coLevel, 1);
    Serial.print(F("  V2 (Dust): ")); Serial.print(dustLevel, 0);
    Serial.print(F("  V3 (Noise): ")); Serial.print(noiseLevel, 0);
    Serial.println(F("    │"));
    Serial.print(F("│    V5 (Alert Level): ")); Serial.print(alertLevel);
    Serial.println(F("                                      │"));
    Serial.println(F("└────────────────────────────────────────────────────────────┘"));
    Serial.println();
  }
}

void printSpaces(int num) {
  for (int i = 0; i < num; i++) {
    Serial.print(" ");
  }
}

// ════════════════════════════════════════════════════════════════════
//                            MAIN LOOP
// ════════════════════════════════════════════════════════════════════
void loop() {
  // 1. Đọc tất cả cảm biến
  airQuality = readMQ135();
  coLevel = readMQ7();
  dustLevel = readDustSensor();
  noiseLevel = readSoundSensor();
  
  // 2. Tính mức cảnh báo
  alertLevel = calculateAlertLevel(airQuality, coLevel, dustLevel, noiseLevel);
  
  // 3. Cập nhật LED
  updateLEDs(alertLevel);
  
  // 4. Cập nhật Buzzer
  updateBuzzer(alertLevel);
  
  // 5. Cập nhật LCD
  updateLCD();
  
  // 6. In ra Serial Monitor
  printToSerial();
  
  // Delay nhỏ để ổn định
  delay(100);
}
