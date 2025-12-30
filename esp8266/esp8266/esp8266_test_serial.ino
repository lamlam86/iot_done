// ============================================
// ESP8266 - Test giao tiếp Serial với Arduino
// ============================================
// Upload code này lên ESP8266

void setup() {
  // Serial dùng chân TX (GPIO1) và RX (GPIO3)
  // Đây cũng là chân debug USB
  Serial.begin(9600);
  
  delay(1000);
  
  Serial.println();
  Serial.println("========================================");
  Serial.println("ESP8266 - Test ket noi voi Arduino");
  Serial.println("========================================");
}

void loop() {
  // Kiểm tra xem có data từ Arduino không
  if (Serial.available()) {
    // Đọc message từ Arduino
    String message = Serial.readStringUntil('\n');
    
    // In ra để debug
    Serial.print("Nhan tu Arduino: ");
    Serial.println(message);
    
    // Gửi phản hồi về Arduino
    Serial.println("ESP8266 OK!");
  }
}
