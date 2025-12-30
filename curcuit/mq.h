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