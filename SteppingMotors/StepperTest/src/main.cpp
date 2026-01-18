#include <Arduino.h>
#include <AccelStepper.h>
#include <Servo.h>

// put function declarations here:
int myFunction(int, int);

Servo servo;

void setup() {
  // put your setup code here, to run once:
  int result = myFunction(2, 3);
  servo.attach(11);
}

int val = 90;
int dir = -1;

bool on = true;

void loop() {
  servo.write(val);
  val += 5*dir;
  if (val >= 135 || val <= 45) {
    dir = -dir;
  }
  digitalWrite(13, on ? HIGH : LOW);
  on = !on;
  delay(1000);
}

// put function definitions here:
int myFunction(int x, int y) {
  return x + y;
}