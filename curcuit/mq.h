#ifndef MQ_H
#define MQ_H

#include <Arduino.h>

long readVcc() {
  ADMUX = _BV(REFS0) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
  delay(2);
  ADCSRA |= _BV(ADSC);
  while (bit_is_set(ADCSRA, ADSC));
  int result = ADC;
  long vcc = 1125300L / result;
  return vcc; 
}

// ============================================
// GP2Y1014AU PM2.5 Dust Sensor Class
// ============================================
class GP2Y1014AU {
  private:
    int _ledPin;      // Digital pin to control IR LED
    int _analogPin;   // Analog pin to read dust density
    float _vcc;       // Operating voltage
    
    // Timing constants (microseconds)
    static const int SAMPLING_TIME = 280;    // Time to wait before reading
    static const int DELTA_TIME = 40;        // Time to keep LED on after reading
    static const int SLEEP_TIME = 9680;      // Time to sleep between readings
    
  public:
    GP2Y1014AU(int ledPin, int analogPin, float vcc = 5.0)
      : _ledPin(ledPin), _analogPin(analogPin), _vcc(vcc) {}
    
    void begin() {
      pinMode(_ledPin, OUTPUT);
      digitalWrite(_ledPin, LOW);  // LED off initially (active LOW)
    }
    
    // Returns dust density in μg/m³
    float getDustDensity() {
      // Turn on IR LED (active LOW through transistor or direct)
      digitalWrite(_ledPin, LOW);
      delayMicroseconds(SAMPLING_TIME);
      
      // Read analog value
      int rawADC = analogRead(_analogPin);
      
      delayMicroseconds(DELTA_TIME);
      digitalWrite(_ledPin, HIGH);  // Turn off LED
      delayMicroseconds(SLEEP_TIME);
      
      // Convert to voltage
      float voltage = rawADC * (_vcc / 1023.0);
      
      // Convert voltage to dust density (μg/m³)
      // Linear equation from datasheet: y = 0.17x - 0.1
      // Rearranged: dustDensity = (voltage - 0.9) / 0.005
      // Alternative formula commonly used:
      float dustDensity = (voltage * 0.17 - 0.1) * 1000.0;
      
      // Ensure non-negative value
      if (dustDensity < 0) dustDensity = 0;
      
      return dustDensity;
    }
    
    // Returns raw voltage for debugging
    float getVoltage() {
      digitalWrite(_ledPin, LOW);
      delayMicroseconds(SAMPLING_TIME);
      int rawADC = analogRead(_analogPin);
      delayMicroseconds(DELTA_TIME);
      digitalWrite(_ledPin, HIGH);
      delayMicroseconds(SLEEP_TIME);
      
      return rawADC * (_vcc / 1023.0);
    }
};

class MQ135 {
  private:
    int _pin;
    float _R0; float _A; float _B;

  public:
    MQ135(int pin, float R0 = 14, float A = 770.24181, float B = -4.065)
      : _pin(pin), _R0(R0), _A(A), _B(B) {}

    float getPPM() {
      float vcc = readVcc() / 1000.0;                 
      int adc = analogRead(_pin);
      float vout = (adc / 1023.0) * vcc;
      float RL = 1.0;                                 
      float Rs = RL * (vcc / vout - 1);
      float ratio = Rs / _R0;
      Serial.println(ratio);
      return _A * pow(ratio, _B);
    }
};

class MQ3 {
  private:
    int _pin;
    float _R0; float _A; float _B;

  public:
    MQ3(int pin, float R0 = 0.23, float A = 4.1376, float B = -2.6610)
      : _pin(pin), _R0(R0), _A(A), _B(B) {}

    float getPPB() {
      float vcc = readVcc() / 1000.0;                 
      int adc = analogRead(_pin);
      float vout = (adc / 1023.0) * vcc;
      float RL = 1.0;                                 
      float Rs = RL * (vcc / vout - 1);
      float ratio = Rs / _R0;
      Serial.println(ratio);
      return (_A * pow(ratio, _B))*1000;
    }
};
#endif