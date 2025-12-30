// ============================================
// ESP8266 + LED + Blynk WiFi Control
// ============================================

// Thay đổi thông tin Blynk của bạn ở đây
#define BLYNK_TEMPLATE_ID "TMPL6BxuCtIum"           // Thay bằng Template ID của bạn
#define BLYNK_TEMPLATE_NAME "Air Quality Prediction" // Thay bằng Template Name của bạn
#define BLYNK_AUTH_TOKEN "tEueg4kzgsG7-RWTIhQF2FpeTrp5ORKE" // Thay bằng Auth Token của bạn

// Bật debug qua Serial
#define BLYNK_PRINT Serial

#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>

// Thông tin WiFi - THAY ĐỔI THEO WIFI CỦA BẠN
char ssid[] = "zantum";      // Tên WiFi
char pass[] = "12345678";    // Mật khẩu WiFi

// Định nghĩa chân LED
#define LED_PIN 2  // GPIO2 = D4 trên NodeMCU ESP8266

// Biến lưu trạng thái LED
int ledState = LOW;

// ============================================
// Hàm xử lý khi nhận tín hiệu từ Blynk (V0)
// ============================================
BLYNK_WRITE(V0) {
  // Đọc giá trị từ Virtual Pin V0 (0 hoặc 1)
  int value = param.asInt();
  
  // Điều khiển LED
  // Lưu ý: LED_BUILTIN trên ESP8266 hoạt động ngược (LOW = sáng, HIGH = tắt)
  if (value == 1) {
    digitalWrite(LED_PIN, LOW);   // Bật LED (active LOW)
    ledState = HIGH;
    Serial.println("LED: BẬT");
  } else {
    digitalWrite(LED_PIN, HIGH);  // Tắt LED
    ledState = LOW;
    Serial.println("LED: TẮT");
  }
}

// ============================================
// Hàm xử lý khi kết nối Blynk thành công
// ============================================
BLYNK_CONNECTED() {
  Serial.println("Đã kết nối Blynk!");
  // Đồng bộ trạng thái từ server khi kết nối
  Blynk.syncVirtual(V0);
}

// ============================================
// Setup
// ============================================
void setup() {
  // Khởi tạo Serial để debug
  Serial.begin(115200);
  delay(100);
  
  Serial.println();
  Serial.println("========================================");
  Serial.println("ESP8266 + LED + Blynk");
  Serial.println("========================================");
  
  // Cấu hình chân LED là OUTPUT
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);  // Tắt LED ban đầu (active LOW)
  
  // Kết nối WiFi và Blynk
  Serial.print("Đang kết nối WiFi: ");
  Serial.println(ssid);
  
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  
  Serial.println("Kết nối thành công!");
  Serial.print("Địa chỉ IP: ");
  Serial.println(WiFi.localIP());
}

// ============================================
// Loop
// ============================================
void loop() {
  // Chạy Blynk
  Blynk.run();
}
