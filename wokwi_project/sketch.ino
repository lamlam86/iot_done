// ============================================================
// 🌍 IOT AIR QUALITY & NOISE MONITOR - WOKWI SIMULATION
// ============================================================
// Đề tài: Hệ thống IoT cảnh báo ô nhiễm không khí và tiếng ồn
// Mô phỏng trên Wokwi trước khi có phần cứng thật
// ============================================================

#include <LiquidCrystal_I2C.h>

// ============== CẤU HÌNH CHÂN ==============
// Cảm biến (dùng Potentiometer để giả lập)
const int PIN_MQ135 = A0;    // Cảm biến chất lượng không khí
const int PIN_MQ7 = A1;      // Cảm biến CO
const int PIN_DUST = A2;     // Cảm biến bụi PM2.5
const int PIN_SOUND = A3;    // Cảm biến tiếng ồn

// LED cảnh báo
const int LED_GREEN = 5;     // An toàn
const int LED_YELLOW = 6;    // Chú ý
const int LED_RED = 7;       // Nguy hiểm

// Buzzer
const int BUZZER = 8;

// ============== NGƯỠNG CẢNH BÁO ==============
// CO (ppm)
const float CO_SAFE = 2.0;
const float CO_WARNING = 4.0;
const float CO_DANGER = 9.0;

// Air Quality Index
const float AIR_SAFE = 50;
const float AIR_WARNING = 100;
const float AIR_DANGER = 200;

// Dust PM2.5 (µg/m³)
const float DUST_SAFE = 35;
const float DUST_WARNING = 75;
const float DUST_DANGER = 150;

// Noise (dB)
const float NOISE_SAFE = 55;
const float NOISE_WARNING = 70;
const float NOISE_DANGER = 85;

// ============== LCD ==============
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ============== BIẾN TOÀN CỤC ==============
int displayMode = 0;  // Chế độ hiển thị LCD
unsigned long lastDisplayChange = 0;
const int DISPLAY_INTERVAL = 3000;  // Đổi màn hình mỗi 3 giây

// ============== SETUP ==============
void setup() {
  Serial.begin(9600);
  
  // Khởi tạo LCD
  lcd.init();
  lcd.backlight();
  lcd.clear();
  
  // Hiển thị màn hình chào
  lcd.setCursor(0, 0);
  lcd.print("  AIR QUALITY   ");
  lcd.setCursor(0, 1);
  lcd.print("    MONITOR     ");
  
  // Setup LED pins
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  
  // Tắt tất cả LED
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_RED, LOW);
  
  // Serial Monitor
  Serial.println("╔═══════════════════════════════════════════╗");
  Serial.println("║   IOT AIR QUALITY & NOISE MONITOR         ║");
  Serial.println("║   Simulation Mode - Wokwi                 ║");
  Serial.println("╚═══════════════════════════════════════════╝");
  Serial.println();
  Serial.println("Dieu chinh Potentiometer de thay doi gia tri!");
  Serial.println("- POT1 (A0): Air Quality");
  Serial.println("- POT2 (A1): CO Level");
  Serial.println("- POT3 (A2): Dust PM2.5");
  Serial.println("- POT4 (A3): Noise Level");
  Serial.println();
  
  delay(2000);
  lcd.clear();
}

// ============== ĐỌC CẢM BIẾN ==============
float readAirQuality() {
  int raw = analogRead(PIN_MQ135);
  return map(raw, 0, 1023, 0, 500);  // 0-500 AQI
}

float readCO() {
  int raw = analogRead(PIN_MQ7);
  return raw * 10.0 / 1023.0;  // 0-10 ppm
}

float readDust() {
  int raw = analogRead(PIN_DUST);
  return map(raw, 0, 1023, 0, 300);  // 0-300 µg/m³
}

float readNoise() {
  int raw = analogRead(PIN_SOUND);
  return map(raw, 0, 1023, 30, 100);  // 30-100 dB
}

// ============== XÁC ĐỊNH MỨC CẢNH BÁO ==============
int getAlertLevel(float co, float air, float dust, float noise) {
  // Level 2: DANGER (Nguy hiểm)
  if (co >= CO_DANGER || air >= AIR_DANGER || dust >= DUST_DANGER || noise >= NOISE_DANGER) {
    return 2;
  }
  // Level 1: WARNING (Cảnh báo)
  if (co >= CO_WARNING || air >= AIR_WARNING || dust >= DUST_WARNING || noise >= NOISE_WARNING) {
    return 1;
  }
  // Level 0: SAFE (An toàn)
  return 0;
}

// ============== ĐIỀU KHIỂN LED ==============
void updateLEDs(int level) {
  digitalWrite(LED_GREEN, level == 0 ? HIGH : LOW);
  digitalWrite(LED_YELLOW, level == 1 ? HIGH : LOW);
  digitalWrite(LED_RED, level == 2 ? HIGH : LOW);
}

// ============== ĐIỀU KHIỂN BUZZER ==============
void updateBuzzer(int level) {
  if (level == 2) {
    // Nguy hiểm: Buzzer kêu liên tục
    tone(BUZZER, 2000, 200);
  } else if (level == 1) {
    // Cảnh báo: Buzzer kêu nhẹ
    static unsigned long lastBeep = 0;
    if (millis() - lastBeep > 5000) {
      tone(BUZZER, 1000, 100);
      lastBeep = millis();
    }
  } else {
    noTone(BUZZER);
  }
}

// ============== CẬP NHẬT LCD ==============
void updateLCD(float co, float air, float dust, float noise, int level) {
  // Tự động chuyển màn hình
  if (millis() - lastDisplayChange > DISPLAY_INTERVAL) {
    displayMode = (displayMode + 1) % 4;
    lastDisplayChange = millis();
    lcd.clear();
  }
  
  lcd.setCursor(0, 0);
  
  switch (displayMode) {
    case 0:  // CO & Air Quality
      lcd.print("CO:");
      lcd.print(co, 1);
      lcd.print("ppm ");
      if (co < CO_SAFE) lcd.print("OK");
      else if (co < CO_WARNING) lcd.print("!");
      else lcd.print("!!");
      
      lcd.setCursor(0, 1);
      lcd.print("Air:");
      lcd.print((int)air);
      lcd.print(" ");
      if (air < AIR_SAFE) lcd.print("GOOD");
      else if (air < AIR_WARNING) lcd.print("MOD");
      else lcd.print("BAD!");
      break;
      
    case 1:  // Dust & Noise
      lcd.print("Dust:");
      lcd.print((int)dust);
      lcd.print("ug/m3");
      
      lcd.setCursor(0, 1);
      lcd.print("Noise:");
      lcd.print((int)noise);
      lcd.print("dB ");
      if (noise < NOISE_SAFE) lcd.print("OK");
      else lcd.print("!");
      break;
      
    case 2:  // Status
      lcd.print("=== STATUS ===");
      lcd.setCursor(0, 1);
      if (level == 0) {
        lcd.print("  ALL SAFE :)   ");
      } else if (level == 1) {
        lcd.print(" ! WARNING !    ");
      } else {
        lcd.print("!! DANGER !!    ");
      }
      break;
      
    case 3:  // Blynk pins
      lcd.print("V0:");
      lcd.print(co, 1);
      lcd.print(" V1:");
      lcd.print((int)air);
      
      lcd.setCursor(0, 1);
      lcd.print("V2:");
      lcd.print((int)dust);
      lcd.print(" V3:");
      lcd.print((int)noise);
      break;
  }
}

// ============== IN SERIAL ==============
void printSerial(float co, float air, float dust, float noise, int level) {
  Serial.println("────────────────────────────────────────────");
  Serial.print("│ CO:    ");
  Serial.print(co, 2);
  Serial.print(" ppm\t");
  if (co < CO_SAFE) Serial.println("[OK]");
  else if (co < CO_WARNING) Serial.println("[!]");
  else Serial.println("[DANGER!]");
  
  Serial.print("│ Air:   ");
  Serial.print(air, 1);
  Serial.print(" AQI\t");
  if (air < AIR_SAFE) Serial.println("[GOOD]");
  else if (air < AIR_WARNING) Serial.println("[MODERATE]");
  else Serial.println("[UNHEALTHY!]");
  
  Serial.print("│ Dust:  ");
  Serial.print(dust, 1);
  Serial.print(" µg/m³\t");
  if (dust < DUST_SAFE) Serial.println("[OK]");
  else if (dust < DUST_WARNING) Serial.println("[!]");
  else Serial.println("[HIGH!]");
  
  Serial.print("│ Noise: ");
  Serial.print(noise, 1);
  Serial.print(" dB\t");
  if (noise < NOISE_SAFE) Serial.println("[QUIET]");
  else if (noise < NOISE_WARNING) Serial.println("[MODERATE]");
  else Serial.println("[LOUD!]");
  
  Serial.println("├────────────────────────────────────────────");
  Serial.print("│ STATUS: ");
  if (level == 0) Serial.println("🟢 SAFE - All clear!");
  else if (level == 1) Serial.println("🟡 WARNING - Attention needed!");
  else Serial.println("🔴 DANGER - Take action now!");
  
  Serial.println("├────────────────────────────────────────────");
  Serial.println("│ >> Data for Blynk Cloud:");
  Serial.print("│    V0="); Serial.print(co);
  Serial.print(", V1="); Serial.print(air);
  Serial.print(", V2="); Serial.print(dust);
  Serial.print(", V3="); Serial.print(noise);
  Serial.print(", V5="); Serial.println(level);
  Serial.println("────────────────────────────────────────────");
  Serial.println();
}

// ============== MAIN LOOP ==============
void loop() {
  // Đọc giá trị cảm biến
  float co = readCO();
  float air = readAirQuality();
  float dust = readDust();
  float noise = readNoise();
  
  // Xác định mức cảnh báo
  int alertLevel = getAlertLevel(co, air, dust, noise);
  
  // Cập nhật LED
  updateLEDs(alertLevel);
  
  // Cập nhật Buzzer
  updateBuzzer(alertLevel);
  
  // Cập nhật LCD
  updateLCD(co, air, dust, noise, alertLevel);
  
  // In ra Serial Monitor
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 2000) {
    printSerial(co, air, dust, noise, alertLevel);
    lastPrint = millis();
  }
  
  delay(100);
}
