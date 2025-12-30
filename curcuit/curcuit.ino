#include "MQ.h"
#include <SoftwareSerial.h>

// RX on Pin 2, TX on Pin 3 
// Connect Pin 12 to ESP8266 RX (via voltage divider)
// Connect Pin 13 to ESP8266 TX
SoftwareSerial espSerial(13, 12); 

MQ135 mq135(A0);
MQ3 mq3(A1);

void setup() {
  Serial.begin(9600);    // For debugging on PC
  espSerial.begin(9600); // For sending data to ESP8266
}

void loop() {
  float valueMQ135 = mq135.getPPM();
  float valueMQ3 = mq3.getPPB();

  // Print to PC Monitor (Human readable)
  Serial.print("MQ135: "); Serial.print(valueMQ135);
  Serial.print(" | MQ3: "); Serial.println(valueMQ3,10);

  // Send to ESP8266 (Machine readable CSV format: "val1,val2\n")
  espSerial.print(valueMQ135);
  espSerial.print(",");
  espSerial.println(valueMQ3);

  delay(1000);
}