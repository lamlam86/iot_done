// ============================================
// ARDUINO - Test giao tiếp Serial với ESP8266
// ============================================
// Upload code này lên Arduino UNO/Nano

#include <SoftwareSerial.h>

// Định nghĩa chân Serial
// Pin 13: RX (nhận từ ESP8266 TX)
// Pin 12: TX (gửi đến ESP8266 RX - qua voltage divider!)
SoftwareSerial espSerial(13, 12);

int counter = 0;

void setup() {
  // Serial để debug trên máy tính
  Serial.begin(9600);
  
  // Serial để giao tiếp với ESP8266
  espSerial.begin(9600);
  
  Serial.println("========================================");
  Serial.println("Arduino - Test ket noi voi ESP8266");
  Serial.println("========================================");
  
  // Chờ 2 giây để ESP8266 khởi động
  delay(2000);
}

void loop() {
  // Gửi data đến ESP8266 mỗi 2 giây
  counter++;
  
  String message = "Hello ESP! Count: " + String(counter);
  
  // Gửi đến ESP8266
  espSerial.println(message);
  
  // In ra Serial Monitor
  Serial.print("Gui den ESP8266: ");
  Serial.println(message);
  
  // Kiểm tra xem có data từ ESP8266 không
  if (espSerial.available()) {
    String response = espSerial.readStringUntil('\n');
    Serial.print("Nhan tu ESP8266: ");
    Serial.println(response);
  }
  
  delay(2000);
}
