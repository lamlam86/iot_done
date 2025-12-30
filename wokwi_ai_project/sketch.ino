// ════════════════════════════════════════════════════════════════════════════
// ĐỒ ÁN: HỆ THỐNG IOT CẢNH BÁO Ô NHIỄM KHÔNG KHÍ VÀ TIẾNG ỒN
// TÍCH HỢP AI DỰ ĐOÁN
// ════════════════════════════════════════════════════════════════════════════
// Mô phỏng trên Wokwi - Có tính năng AI Prediction giả lập
// Khi có phần cứng thật: ESP8266 sẽ gửi lên server Python để AI dự đoán
// ════════════════════════════════════════════════════════════════════════════

#include <LiquidCrystal_I2C.h>

// ══════════════════ CHÂN CẢM BIẾN ══════════════════
const int PIN_MQ135 = A0;      // Chất lượng không khí (Air Quality Index)
const int PIN_MQ7 = A1;        // CO - Carbon Monoxide
const int PIN_DUST = A2;       // Bụi PM2.5
const int PIN_SOUND = A3;      // Tiếng ồn

// ══════════════════ CHÂN OUTPUT ══════════════════
const int LED_GREEN = 5;       // An toàn
const int LED_YELLOW = 6;      // Cảnh báo
const int LED_RED = 7;         // Nguy hiểm
const int BUZZER = 8;          // Còi

// ══════════════════ NGƯỠNG CẢNH BÁO ══════════════════
const float AIR_WARNING = 100, AIR_DANGER = 200;
const float CO_WARNING = 9, CO_DANGER = 35;
const float DUST_WARNING = 50, DUST_DANGER = 100;
const float NOISE_WARNING = 65, NOISE_DANGER = 85;

// ══════════════════ LCD ══════════════════
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ══════════════════ BIẾN TOÀN CỤC ══════════════════
float air, co, dust, noise;
int alertLevel;
unsigned long lastLCD = 0, lastSerial = 0, lastBuzz = 0, lastAI = 0;
int page = 0;

// ══════════════════ BIẾN AI PREDICTION ══════════════════
float ai_air_predict, ai_co_predict;
int ai_alert_predict;
String ai_recommendation;

// ══════════════════ LỊCH SỬ DATA (cho AI) ══════════════════
float air_history[24];
float co_history[24];
int history_index = 0;

// ════════════════════════════════════════════════════════════════════════════
//                                 SETUP
// ════════════════════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  
  // Khởi tạo history
  for(int i = 0; i < 24; i++) {
    air_history[i] = 50;
    co_history[i] = 2;
  }
  
  // Màn hình khởi động
  lcd.setCursor(0, 0);
  lcd.print("  DO AN IOT AI  ");
  lcd.setCursor(0, 1);
  lcd.print("Air&Noise+AI Pred");
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Loading AI Model");
  lcd.setCursor(0, 1);
  for(int i = 0; i < 16; i++) {
    lcd.print(".");
    delay(100);
  }
  delay(500);
  
  // In header
  Serial.println();
  Serial.println(F("╔══════════════════════════════════════════════════════════════════════╗"));
  Serial.println(F("║     🌍 HE THONG IOT CANH BAO O NHIEM + 🤖 AI PREDICTION              ║"));
  Serial.println(F("╠══════════════════════════════════════════════════════════════════════╣"));
  Serial.println(F("║  THIET BI:                                                           ║"));
  Serial.println(F("║    • MQ-135:     Cam bien chat luong khong khi (A0)                  ║"));
  Serial.println(F("║    • MQ-7:       Cam bien CO - Carbon Monoxide (A1)                  ║"));
  Serial.println(F("║    • GP2Y1010:   Cam bien bui PM2.5 (A2)                             ║"));
  Serial.println(F("║    • KY-038:     Cam bien tieng on (A3)                              ║"));
  Serial.println(F("║    • LCD 16x2:   Man hinh hien thi                                   ║"));
  Serial.println(F("║    • LED R/Y/G:  Den canh bao                                        ║"));
  Serial.println(F("║    • Buzzer:     Coi bao dong                                        ║"));
  Serial.println(F("╠══════════════════════════════════════════════════════════════════════╣"));
  Serial.println(F("║  🤖 AI FEATURES:                                                     ║"));
  Serial.println(F("║    • Du doan chat luong khong khi 1 gio toi                          ║"));
  Serial.println(F("║    • Phat hien xu huong (trend detection)                            ║"));
  Serial.println(F("║    • Khuyen nghi hanh dong (recommendation)                          ║"));
  Serial.println(F("║    • Canh bao thong minh (smart alert)                               ║"));
  Serial.println(F("╠══════════════════════════════════════════════════════════════════════╣"));
  Serial.println(F("║  Xoay POT de thay doi gia tri cam bien!                              ║"));
  Serial.println(F("╚══════════════════════════════════════════════════════════════════════╝"));
  Serial.println();
  
  lcd.clear();
}

// ════════════════════════════════════════════════════════════════════════════
//                           ĐỌC CẢM BIẾN
// ════════════════════════════════════════════════════════════════════════════
void readSensors() {
  air = map(analogRead(PIN_MQ135), 0, 1023, 0, 500);
  co = analogRead(PIN_MQ7) * 50.0 / 1023.0;  // 0-50 ppm
  dust = map(analogRead(PIN_DUST), 0, 1023, 0, 300);
  noise = map(analogRead(PIN_SOUND), 0, 1023, 30, 110);
}

// ════════════════════════════════════════════════════════════════════════════
//                         TÍNH MỨC CẢNH BÁO
// ════════════════════════════════════════════════════════════════════════════
int calculateAlert(float a, float c, float d, float n) {
  if(a >= AIR_DANGER || c >= CO_DANGER || d >= DUST_DANGER || n >= NOISE_DANGER) return 2;
  if(a >= AIR_WARNING || c >= CO_WARNING || d >= DUST_WARNING || n >= NOISE_WARNING) return 1;
  return 0;
}

// ════════════════════════════════════════════════════════════════════════════
//                    🤖 AI PREDICTION (Simulated)
// ════════════════════════════════════════════════════════════════════════════
void runAIPrediction() {
  // Cập nhật history
  air_history[history_index] = air;
  co_history[history_index] = co;
  history_index = (history_index + 1) % 24;
  
  // ══════════ TÍNH TRUNG BÌNH VÀ TREND ══════════
  float air_avg = 0, co_avg = 0;
  float air_recent = 0, co_recent = 0;
  
  for(int i = 0; i < 24; i++) {
    air_avg += air_history[i];
    co_avg += co_history[i];
  }
  air_avg /= 24;
  co_avg /= 24;
  
  // 6 giá trị gần nhất
  for(int i = 0; i < 6; i++) {
    int idx = (history_index - 1 - i + 24) % 24;
    air_recent += air_history[idx];
    co_recent += co_history[idx];
  }
  air_recent /= 6;
  co_recent /= 6;
  
  // ══════════ TÍNH XU HƯỚNG (TREND) ══════════
  float air_trend = air_recent - air_avg;
  float co_trend = co_recent - co_avg;
  
  // ══════════ DỰ ĐOÁN GIÁ TRỊ SAU 1 GIỜ ══════════
  // Công thức đơn giản: value + trend * factor + noise
  ai_air_predict = air + (air_trend * 0.5) + random(-10, 10);
  ai_co_predict = co + (co_trend * 0.3) + random(-2, 2) / 10.0;
  
  // Đảm bảo giá trị hợp lệ
  ai_air_predict = constrain(ai_air_predict, 0, 500);
  ai_co_predict = constrain(ai_co_predict, 0, 50);
  
  // ══════════ TÍNH MỨC CẢNH BÁO DỰ ĐOÁN ══════════
  ai_alert_predict = calculateAlert(ai_air_predict, ai_co_predict, dust, noise);
  
  // ══════════ TẠO KHUYẾN NGHỊ ══════════
  if(ai_alert_predict == 2) {
    if(ai_co_predict > co) {
      ai_recommendation = "CO se tang! Mo cua thong gio!";
    } else if(ai_air_predict > air) {
      ai_recommendation = "KK se xau! Han che ra ngoai!";
    } else {
      ai_recommendation = "O nhiem cao! Can hanh dong!";
    }
  } else if(ai_alert_predict == 1) {
    if(air_trend > 0) {
      ai_recommendation = "Xu huong tang. Theo doi!";
    } else {
      ai_recommendation = "Muc trung binh. Chu y!";
    }
  } else {
    if(air_trend < -10) {
      ai_recommendation = "Dang cai thien! Tot!";
    } else {
      ai_recommendation = "On dinh. Moi thu tot!";
    }
  }
}

// ════════════════════════════════════════════════════════════════════════════
//                           ĐIỀU KHIỂN LED
// ════════════════════════════════════════════════════════════════════════════
void updateLEDs() {
  digitalWrite(LED_GREEN, alertLevel == 0);
  digitalWrite(LED_YELLOW, alertLevel == 1);
  digitalWrite(LED_RED, alertLevel == 2);
}

// ════════════════════════════════════════════════════════════════════════════
//                          ĐIỀU KHIỂN BUZZER
// ════════════════════════════════════════════════════════════════════════════
void updateBuzzer() {
  if(alertLevel == 2 && millis() - lastBuzz > 500) {
    tone(BUZZER, 2000, 200);
    lastBuzz = millis();
  } else if(alertLevel == 1 && millis() - lastBuzz > 3000) {
    tone(BUZZER, 1000, 100);
    lastBuzz = millis();
  } else if(alertLevel == 0) {
    noTone(BUZZER);
  }
}

// ════════════════════════════════════════════════════════════════════════════
//                            CẬP NHẬT LCD
// ════════════════════════════════════════════════════════════════════════════
void updateLCD() {
  if(millis() - lastLCD > 3000) {
    page = (page + 1) % 7;  // 7 trang (thêm 2 trang AI)
    lastLCD = millis();
    lcd.clear();
  }
  
  lcd.setCursor(0, 0);
  
  switch(page) {
    case 0:  // Air Quality
      lcd.print("MQ-135 Air:");
      lcd.setCursor(0, 1);
      lcd.print("AQI:"); lcd.print((int)air);
      lcd.print(air < 100 ? " TOT" : (air < 200 ? " TB" : " XAU!"));
      break;
      
    case 1:  // CO Level
      lcd.print("MQ-7 CO:");
      lcd.setCursor(0, 1);
      lcd.print(co, 1); lcd.print("ppm ");
      lcd.print(co < 9 ? "OK" : (co < 35 ? "!" : "NGUY!"));
      break;
      
    case 2:  // Dust
      lcd.print("GP2Y Dust PM2.5:");
      lcd.setCursor(0, 1);
      lcd.print((int)dust); lcd.print("ug/m3 ");
      lcd.print(dust < 50 ? "TOT" : (dust < 100 ? "TB" : "CAO!"));
      break;
      
    case 3:  // Noise
      lcd.print("KY-038 Noise:");
      lcd.setCursor(0, 1);
      lcd.print((int)noise); lcd.print("dB ");
      lcd.print(noise < 65 ? "YEN" : (noise < 85 ? "TB" : "ON!"));
      break;
      
    case 4:  // Status
      lcd.print("==TRANG THAI==");
      lcd.setCursor(0, 1);
      lcd.print(alertLevel == 0 ? "  AN TOAN :)  " : 
               (alertLevel == 1 ? " CANH BAO !   " : " NGUY HIEM !! "));
      break;
      
    case 5:  // AI Prediction
      lcd.print("*AI DU DOAN 1H*");
      lcd.setCursor(0, 1);
      lcd.print("Air:"); lcd.print((int)ai_air_predict);
      lcd.print(" CO:"); lcd.print(ai_co_predict, 1);
      break;
      
    case 6:  // AI Recommendation
      lcd.print("*AI KHUYEN NGHI*");
      lcd.setCursor(0, 1);
      // Cuộn text nếu dài
      lcd.print(ai_recommendation.substring(0, 16));
      break;
  }
}

// ════════════════════════════════════════════════════════════════════════════
//                         IN RA SERIAL MONITOR
// ════════════════════════════════════════════════════════════════════════════
void printSerial() {
  if(millis() - lastSerial < 2000) return;
  lastSerial = millis();
  
  Serial.println(F("┌──────────────────────────────────────────────────────────────────────┐"));
  Serial.println(F("│                    📊 SENSOR DATA (REALTIME)                         │"));
  Serial.println(F("├──────────────────────────────────────────────────────────────────────┤"));
  
  Serial.print(F("│  MQ-135 Air Quality: ")); Serial.print(air, 0); Serial.print(F(" AQI"));
  printPadding(45 - String(air, 0).length());
  Serial.print(air < 100 ? "[TOT]" : (air < 200 ? "[TB]" : "[XAU!]"));
  Serial.println(F("    │"));
  
  Serial.print(F("│  MQ-7 CO Level:      ")); Serial.print(co, 1); Serial.print(F(" ppm"));
  printPadding(45 - String(co, 1).length());
  Serial.print(co < 9 ? "[OK]" : (co < 35 ? "[CHU Y]" : "[NGUY!]"));
  Serial.println(F("  │"));
  
  Serial.print(F("│  GP2Y Dust PM2.5:    ")); Serial.print(dust, 0); Serial.print(F(" ug/m3"));
  printPadding(43 - String(dust, 0).length());
  Serial.print(dust < 50 ? "[TOT]" : (dust < 100 ? "[TB]" : "[CAO!]"));
  Serial.println(F("    │"));
  
  Serial.print(F("│  KY-038 Noise:       ")); Serial.print(noise, 0); Serial.print(F(" dB"));
  printPadding(46 - String(noise, 0).length());
  Serial.print(noise < 65 ? "[YEN]" : (noise < 85 ? "[TB]" : "[ON!]"));
  Serial.println(F("    │"));
  
  Serial.println(F("├──────────────────────────────────────────────────────────────────────┤"));
  Serial.print(F("│  TRANG THAI: "));
  if(alertLevel == 0) Serial.println(F("🟢 AN TOAN - Moi thu binh thuong!                   │"));
  else if(alertLevel == 1) Serial.println(F("🟡 CANH BAO - Can theo doi!                        │"));
  else Serial.println(F("🔴 NGUY HIEM - Can hanh dong ngay!                  │"));
  
  Serial.print(F("│  LED: "));
  Serial.print(alertLevel == 0 ? "🟢" : "⚫");
  Serial.print(alertLevel == 1 ? "🟡" : "⚫");
  Serial.print(alertLevel == 2 ? "🔴" : "⚫");
  Serial.print(F("   Buzzer: "));
  Serial.println(alertLevel == 0 ? "OFF                                       │" : 
                (alertLevel == 1 ? "BEEP/3s                                   │" : "BEEP/0.5s                                 │"));
  
  // AI Section
  Serial.println(F("├──────────────────────────────────────────────────────────────────────┤"));
  Serial.println(F("│                    🤖 AI PREDICTION (1 GIO TOI)                      │"));
  Serial.println(F("├──────────────────────────────────────────────────────────────────────┤"));
  
  Serial.print(F("│  Du doan Air Quality: ")); Serial.print(ai_air_predict, 0); Serial.print(F(" AQI"));
  float air_change = ai_air_predict - air;
  Serial.print(air_change >= 0 ? " (+" : " ("); Serial.print(air_change, 0); Serial.print(F(")"));
  printPadding(35 - String(ai_air_predict, 0).length() - String(air_change, 0).length());
  Serial.println(F("│"));
  
  Serial.print(F("│  Du doan CO Level:    ")); Serial.print(ai_co_predict, 1); Serial.print(F(" ppm"));
  float co_change = ai_co_predict - co;
  Serial.print(co_change >= 0 ? " (+" : " ("); Serial.print(co_change, 1); Serial.print(F(")"));
  printPadding(33 - String(ai_co_predict, 1).length() - String(co_change, 1).length());
  Serial.println(F("│"));
  
  Serial.print(F("│  Muc canh bao du doan: "));
  if(ai_alert_predict == 0) Serial.println(F("🟢 AN TOAN                               │"));
  else if(ai_alert_predict == 1) Serial.println(F("🟡 CANH BAO                              │"));
  else Serial.println(F("🔴 NGUY HIEM                             │"));
  
  Serial.print(F("│  💡 Khuyen nghi: ")); Serial.print(ai_recommendation);
  printPadding(50 - ai_recommendation.length());
  Serial.println(F("│"));
  
  // Blynk Data
  Serial.println(F("├──────────────────────────────────────────────────────────────────────┤"));
  Serial.println(F("│                    📱 DATA GUI LEN BLYNK CLOUD                       │"));
  Serial.println(F("├──────────────────────────────────────────────────────────────────────┤"));
  Serial.print(F("│  V0="));Serial.print(air,0);
  Serial.print(F(" V1="));Serial.print(co,1);
  Serial.print(F(" V2="));Serial.print(dust,0);
  Serial.print(F(" V3="));Serial.print(noise,0);
  Serial.print(F(" V5="));Serial.print(alertLevel);
  Serial.println(F("                          │"));
  Serial.print(F("│  V6="));Serial.print(ai_air_predict,0);
  Serial.print(F(" (AI Air) V7="));Serial.print(ai_co_predict,1);
  Serial.print(F(" (AI CO) V8="));Serial.print(ai_alert_predict);
  Serial.println(F(" (AI Alert)        │"));
  
  Serial.println(F("└──────────────────────────────────────────────────────────────────────┘"));
  Serial.println();
}

void printPadding(int n) {
  for(int i = 0; i < n; i++) Serial.print(" ");
}

// ════════════════════════════════════════════════════════════════════════════
//                              MAIN LOOP
// ════════════════════════════════════════════════════════════════════════════
void loop() {
  // 1. Đọc cảm biến
  readSensors();
  
  // 2. Tính mức cảnh báo
  alertLevel = calculateAlert(air, co, dust, noise);
  
  // 3. Chạy AI prediction (mỗi 5 giây)
  if(millis() - lastAI > 5000) {
    runAIPrediction();
    lastAI = millis();
  }
  
  // 4. Cập nhật outputs
  updateLEDs();
  updateBuzzer();
  updateLCD();
  
  // 5. In Serial
  printSerial();
  
  delay(100);
}
