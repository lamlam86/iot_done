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
    // Read the incoming line: "12.34,5.67"
    String data = Serial.readStringUntil('\n');
    
    // Find the comma separator
    int commaIndex = data.indexOf(',');
    
    if (commaIndex > 0) {
      // Split the string
      String val1_str = data.substring(0, commaIndex);
      String val2_str = data.substring(commaIndex + 1);
      
      // Convert to floats
      float mq135_val = val1_str.toFloat();
      float mq3_val = val2_str.toFloat();
      
      // Send to Blynk
      Blynk.virtualWrite(V0, mq135_val);
      Blynk.virtualWrite(V1, mq3_val);
    }
  }
}