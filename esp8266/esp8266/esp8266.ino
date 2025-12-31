#define BLYNK_TEMPLATE_ID "TMPL6BxuCtIum"
#define BLYNK_TEMPLATE_NAME "Air Quality Prediction"
#define BLYNK_AUTH_TOKEN "tEueg4kzgsG7-RWTIhQF2FpeTrp5ORKE"

#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>

char auth[] = BLYNK_AUTH_TOKEN;
char ssid[] = "zantum";
char pass[] = "12345678";

void setup() {
  Serial.begin(9600); 
  Blynk.begin(auth, ssid, pass);
}

void loop() {
  Blynk.run();
  
  if (Serial.available() > 0) {
    // Read the incoming line: "12.34,5.67,89.12"
    String data = Serial.readStringUntil('\n');
    
    // Find comma separators
    int firstComma = data.indexOf(',');
    int secondComma = data.indexOf(',', firstComma + 1);
    
    if (firstComma > 0 && secondComma > 0) {
      // Split the string into 3 values
      String val1_str = data.substring(0, firstComma);
      String val2_str = data.substring(firstComma + 1, secondComma);
      String val3_str = data.substring(secondComma + 1);
      
      // Convert to floats
      float mq135_val = val1_str.toFloat();  // CO2 (ppm)
      float mq3_val = val2_str.toFloat();    // C6H6 (ppb)
      float pm25_val = val3_str.toFloat();   // PM2.5 (μg/m³)
      
      // Send to Blynk
      Blynk.virtualWrite(V0, mq135_val);   // CO2
      Blynk.virtualWrite(V1, mq3_val);     // C6H6
      Blynk.virtualWrite(V2, pm25_val);    // PM2.5
    }
  }
}