#include "MQ.h"
#include <SoftwareSerial.h>

// RX on Pin 2, TX on Pin 3 
// Connect Pin 12 to ESP8266 RX (via voltage divider)
// Connect Pin 13 to ESP8266 TX
SoftwareSerial espSerial(13, 12); 

// Gas sensors
MQ135 mq135(A0);          // CO2 sensor on A0
MQ3 mq3(A1);              // C6H6 (Benzene) sensor on A1

// Dust sensor GP2Y1014AU
// LED Pin: D7, Analog Pin: A2
#define DUST_LED_PIN 7
#define DUST_ANALOG_PIN A2
GP2Y1014AU dustSensor(DUST_LED_PIN, DUST_ANALOG_PIN);

void setup() {
  Serial.begin(9600);    // For debugging on PC
  espSerial.begin(9600); // For sending data to ESP8266
  
  // Initialize dust sensor
  dustSensor.begin();
}

void loop() {
  float valueMQ135 = mq135.getPPM();
  float valueMQ3 = mq3.getPPB();
  float valuePM25 = dustSensor.getDustDensity();  // PM2.5 in μg/m³

  // Print to PC Monitor (Human readable)
  Serial.print("MQ135: "); Serial.print(valueMQ135);
  Serial.print(" | MQ3: "); Serial.print(valueMQ3, 10);
  Serial.print(" | PM2.5: "); Serial.print(valuePM25);
  Serial.println(" ug/m3");

  // Send to ESP8266 (Machine readable CSV format: "val1,val2,val3\n")
  espSerial.print(valueMQ135);
  espSerial.print(",");
  espSerial.print(valueMQ3);
  espSerial.print(",");
  espSerial.println(valuePM25);

  delay(1000);
}