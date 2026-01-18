// XIAO ESP32-S3/Sense: built-in LED is usually on GPIO 21
#ifndef LED_BUILTIN
#define LED_BUILTIN 21
#endif

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
}
