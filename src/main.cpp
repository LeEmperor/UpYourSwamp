#include <Arduino.h>

#ifdef TAURINO_BUILD
// ==================== Multi-Motor Control (RAMPS 1.4) ====================
#include <AccelStepper.h>
#include <Servo.h>

// X-Axis Pins
#define X_STEP_PIN 54
#define X_DIR_PIN 55
#define X_ENABLE_PIN 38

// Y-Axis Pins
#define Y_STEP_PIN 60
#define Y_DIR_PIN 61
#define Y_ENABLE_PIN 56

// E0 Extruder Pins
#define E0_STEP_PIN 26
#define E0_DIR_PIN 28
#define E0_ENABLE_PIN 24

// E1 Extruder Pins
#define E1_STEP_PIN 36
#define E1_DIR_PIN 34
#define E1_ENABLE_PIN 30

#define LED_PIN 13

// Servo pin options (RAMPS servo headers + pin 9) - all active simultaneously
const uint8_t SERVO_PINS[] = {4, 5, 6, 9, 11};
#define SERVO_PINS_COUNT 5

#define STEPS_PER_REV 200
#define MICROSTEPS 16
#define STEPS_PER_DEGREE ((STEPS_PER_REV * MICROSTEPS) / 360.0)

// Motor indices
#define MOTOR_X  0
#define MOTOR_Y  1
#define MOTOR_E0 2
#define MOTOR_E1 3
#define NUM_MOTORS 4

const char* MOTOR_NAMES[NUM_MOTORS] = {"X", "Y", "E0", "E1"};

// Motor Objects
AccelStepper stepperX(AccelStepper::DRIVER, X_STEP_PIN, X_DIR_PIN);
AccelStepper stepperY(AccelStepper::DRIVER, Y_STEP_PIN, Y_DIR_PIN);
AccelStepper stepperE0(AccelStepper::DRIVER, E0_STEP_PIN, E0_DIR_PIN);
AccelStepper stepperE1(AccelStepper::DRIVER, E1_STEP_PIN, E1_DIR_PIN);

AccelStepper* motors[NUM_MOTORS] = {&stepperX, &stepperY, &stepperE0, &stepperE1};
const uint8_t ENABLE_PINS[NUM_MOTORS] = {X_ENABLE_PIN, Y_ENABLE_PIN, E0_ENABLE_PIN, E1_ENABLE_PIN};

bool simultaneousMode = false;
bool motorMoving[NUM_MOTORS] = {false, false, false, false};
bool motorEnabled[NUM_MOTORS] = {false, false, false, false};

// Servo Variables - All 5 pins active simultaneously
Servo servos[SERVO_PINS_COUNT];
int servoCurrentPos[SERVO_PINS_COUNT] = {90, 90, 90, 90, 90};
int servoTargetPos[SERVO_PINS_COUNT] = {90, 90, 90, 90, 90};
bool servoMoving[SERVO_PINS_COUNT] = {false, false, false, false, false};
int servoSpeed = 2;          

String inputBuffer = "";
String btInputBuffer = "";  // Bluetooth input buffer

// --- Dual Output Helpers (USB + Bluetooth) ---

void printBoth(const char* msg) {
  Serial.print(msg);
  Serial1.print(msg);
}

void printlnBoth(const char* msg) {
  Serial.println(msg);
  Serial1.println(msg);
}

void printBoth(int val) {
  Serial.print(val);
  Serial1.print(val);
}

void printlnBoth(int val) {
  Serial.println(val);
  Serial1.println(val);
}

void printBoth(long val) {
  Serial.print(val);
  Serial1.print(val);
}

void printlnBoth(long val) {
  Serial.println(val);
  Serial1.println(val);
}

// --- Helper Functions ---

int parseMotorName(const String& name) {
  if (name == "X")  return MOTOR_X;
  if (name == "Y")  return MOTOR_Y;
  if (name == "E0") return MOTOR_E0;
  if (name == "E1") return MOTOR_E1;
  return -1;
}

// Remove all non-printable characters from command
String sanitizeCommand(String cmd) {
  String result = "";
  for (unsigned int i = 0; i < cmd.length(); i++) {
    char c = cmd.charAt(i);
    // Keep only printable ASCII (space through tilde)
    if (c >= 32 && c <= 126) {
      result += c;
    }
  }
  result.trim();
  return result;
}

void stopAllMotors() {
  for (int i = 0; i < NUM_MOTORS; i++) {
    motors[i]->stop();  // Immediate stop
    motors[i]->disableOutputs();  // Force de-energize to stop whirring/holding
    motorEnabled[i] = false;
    motorMoving[i] = false;
  }
  for (int i = 0; i < SERVO_PINS_COUNT; i++) {
    servoMoving[i] = false;
  }
  digitalWrite(LED_PIN, LOW);
  printlnBoth("\nOK: Forced stop - all motors halted and de-energized");
}

void resetAllMotors() {
  stopAllMotors();  // First force stop everything
  for (int i = 0; i < NUM_MOTORS; i++) {
    motors[i]->setCurrentPosition(0);  // Erase/zero position state
  }
  for (int i = 0; i < SERVO_PINS_COUNT; i++) {
    servoCurrentPos[i] = 90;  // Reset to initial position
    servoTargetPos[i] = 90;
    servos[i].write(90);
  }
  printlnBoth("\nOK: All motor states erased and reset to initial");
}

void reportStatus() {
  printlnBoth("\n=== Motor Status ===");
  printBoth("Mode: ");
  printlnBoth(simultaneousMode ? "SIMULTANEOUS" : "SEQUENTIAL");
  for (int i = 0; i < NUM_MOTORS; i++) {
    printBoth(MOTOR_NAMES[i]);
    printBoth(": pos=");
    printBoth(motors[i]->currentPosition());
    printBoth(", enabled=");
    printlnBoth(motorEnabled[i] ? "yes" : "no");
  }
  printlnBoth("Servos:");
  for (int i = 0; i < SERVO_PINS_COUNT; i++) {
    printBoth("  Pin ");
    printBoth((int)SERVO_PINS[i]);
    printBoth(": ");
    printlnBoth(servoCurrentPos[i]);
  }
  printlnBoth("====================");
}

void printHelp() {
  printlnBoth("\n=== COMMANDS ===");
  printlnBoth("X/Y/E0/E1 <CW/CCW> <degrees>");
  printlnBoth("XY <CW/CCW> <degrees>   (X+Y synced)");
  printlnBoth("ALL <CW/CCW> <degrees>  (all steppers)");
  printlnBoth("SERVO <0-180>        (all servos)");
  printlnBoth("SERVO <pin> <0-180>  (single servo)");
  printlnBoth("MODE SIM / MODE SEQ");
  printlnBoth("STOP                 (forced stop all)");
  printlnBoth("RESET                (erase/reset states)");
  printlnBoth("STATUS / HELP");
  printlnBoth("================");
}

// --- Movement Logic ---

void moveMotorBlocking(int motorIdx, bool cw, int degrees) {
  int steps = (int)(degrees * STEPS_PER_DEGREE);
  printBoth("\nDEBUG: Blocking move ");
  printlnBoth(MOTOR_NAMES[motorIdx]);
  motors[motorIdx]->enableOutputs();  // Ensure enabled
  motorEnabled[motorIdx] = true;
  digitalWrite(LED_PIN, HIGH);
  motors[motorIdx]->move(cw ? steps : -steps);
  while (motors[motorIdx]->run()) { }
  digitalWrite(LED_PIN, LOW);
  motors[motorIdx]->disableOutputs();  // Disable after move
  motorEnabled[motorIdx] = false;
  printBoth("\nOK: Moved "); printlnBoth(MOTOR_NAMES[motorIdx]);
}

void startMotorMove(int motorIdx, bool cw, int degrees) {
  // In sim mode, check if any other is moving to avoid overload
  bool canStart = true;
  for (int i = 0; i < NUM_MOTORS; i++) {
    if (i != motorIdx && motorMoving[i]) {
      canStart = false;
      break;
    }
  }
  if (!canStart) {
    printlnBoth("\nERROR: Wait for current moves to finish in SIM mode");
    return;
  }
  int steps = (int)(degrees * STEPS_PER_DEGREE);
  printBoth("\nDEBUG: Starting ");
  printlnBoth(MOTOR_NAMES[motorIdx]);
  motors[motorIdx]->enableOutputs();
  motorEnabled[motorIdx] = true;
  motors[motorIdx]->move(cw ? steps : -steps);
  motorMoving[motorIdx] = true;
  printBoth("\nSTARTED: "); printlnBoth(MOTOR_NAMES[motorIdx]);
}

void runAllMotors() {
  bool anyMoving = false;
  for (int i = 0; i < NUM_MOTORS; i++) {
    if (motorMoving[i]) {
      motors[i]->run();
      if (!motors[i]->isRunning()) {
        motorMoving[i] = false;
        motors[i]->disableOutputs();  // Disable when done
        motorEnabled[i] = false;
        printBoth("\nFINISHED: "); printlnBoth(MOTOR_NAMES[i]);
      } else {
        anyMoving = true;
      }
    }
  }
  digitalWrite(LED_PIN, anyMoving ? HIGH : LOW);
}

// Move all steppers simultaneously (blocking)
void moveAllMotorsBlocking(bool cw, int degrees) {
  int steps = (int)(degrees * STEPS_PER_DEGREE);
  digitalWrite(LED_PIN, HIGH);
  for (int i = 0; i < NUM_MOTORS; i++) {
    motors[i]->enableOutputs();
    motorEnabled[i] = true;
    motors[i]->move(cw ? steps : -steps);
  }
  bool anyRunning = true;
  while (anyRunning) {
    anyRunning = false;
    for (int i = 0; i < NUM_MOTORS; i++) {
      if (motors[i]->run()) anyRunning = true;
    }
  }
  digitalWrite(LED_PIN, LOW);
  for (int i = 0; i < NUM_MOTORS; i++) {
    motors[i]->disableOutputs();
    motorEnabled[i] = false;
  }
  printlnBoth("\nOK: Moved all steppers");
}

// Move X and Y steppers synchronized (blocking)
void moveXYBlocking(bool cw, int degrees) {
  int steps = (int)(degrees * STEPS_PER_DEGREE);
  digitalWrite(LED_PIN, HIGH);
  motors[MOTOR_X]->enableOutputs();
  motorEnabled[MOTOR_X] = true;
  motors[MOTOR_Y]->enableOutputs();
  motorEnabled[MOTOR_Y] = true;
  motors[MOTOR_X]->move(cw ? steps : -steps);
  motors[MOTOR_Y]->move(cw ? steps : -steps);

  bool anyRunning = true;
  while (anyRunning) {
    anyRunning = false;
    if (motors[MOTOR_X]->run()) anyRunning = true;
    if (motors[MOTOR_Y]->run()) anyRunning = true;
  }
  digitalWrite(LED_PIN, LOW);
  motors[MOTOR_X]->disableOutputs();
  motorEnabled[MOTOR_X] = false;
  motors[MOTOR_Y]->disableOutputs();
  motorEnabled[MOTOR_Y] = false;
  printlnBoth("\nOK: Moved X and Y together");
}

// Start X and Y steppers synchronized (non-blocking)
void startXYMove(bool cw, int degrees) {
  int steps = (int)(degrees * STEPS_PER_DEGREE);
  motors[MOTOR_X]->enableOutputs();
  motorEnabled[MOTOR_X] = true;
  motors[MOTOR_Y]->enableOutputs();
  motorEnabled[MOTOR_Y] = true;
  motors[MOTOR_X]->move(cw ? steps : -steps);
  motors[MOTOR_Y]->move(cw ? steps : -steps);
  motorMoving[MOTOR_X] = true;
  motorMoving[MOTOR_Y] = true;
  printlnBoth("\nSTARTED: X and Y together");
}

// Start all steppers (non-blocking)
void startAllMotorsMove(bool cw, int degrees) {
  int steps = (int)(degrees * STEPS_PER_DEGREE);
  for (int i = 0; i < NUM_MOTORS; i++) {
    motors[i]->enableOutputs();
    motorEnabled[i] = true;
    motors[i]->move(cw ? steps : -steps);
    motorMoving[i] = true;
  }
  printlnBoth("\nSTARTED: All steppers");
}

// Start move for all servos
void startServoMoveAll(int targetAngle) {
  targetAngle = constrain(targetAngle, 0, 180);
  for (int i = 0; i < SERVO_PINS_COUNT; i++) {
    servoTargetPos[i] = targetAngle;
    servoMoving[i] = true;
  }
  printBoth("\nSTARTED: All servos to "); printlnBoth(targetAngle);
}

// Start move for single servo by pin number
void startServoMoveSingle(int pin, int targetAngle) {
  targetAngle = constrain(targetAngle, 0, 180);
  for (int i = 0; i < SERVO_PINS_COUNT; i++) {
    if (SERVO_PINS[i] == pin) {
      servoTargetPos[i] = targetAngle;
      servoMoving[i] = true;
      printBoth("\nSTARTED: Servo pin ");
      printBoth(pin);
      printBoth(" to ");
      printlnBoth(targetAngle);
      return;
    }
  }
  printlnBoth("\nERROR: Invalid servo pin");
}

void runServo() {
  bool anyMoving = false;
  for (int i = 0; i < SERVO_PINS_COUNT; i++) {
    if (!servoMoving[i]) continue;

    if (servoCurrentPos[i] == servoTargetPos[i]) {
      servoMoving[i] = false;
      continue;
    }

    anyMoving = true;
    if (servoCurrentPos[i] < servoTargetPos[i]) servoCurrentPos[i] += servoSpeed;
    else servoCurrentPos[i] -= servoSpeed;

    // Clamp to target if overshot
    if ((servoCurrentPos[i] > servoTargetPos[i] && servoCurrentPos[i] - servoTargetPos[i] < servoSpeed) ||
        (servoCurrentPos[i] < servoTargetPos[i] && servoTargetPos[i] - servoCurrentPos[i] < servoSpeed)) {
      servoCurrentPos[i] = servoTargetPos[i];
    }

    servos[i].write(servoCurrentPos[i]);
  }
  if (anyMoving) delay(15);
}

// Blocking move for all servos
void moveServoBlockingAll(int targetAngle) {
  targetAngle = constrain(targetAngle, 0, 180);
  bool anyMoving = true;
  while (anyMoving) {
    anyMoving = false;
    for (int i = 0; i < SERVO_PINS_COUNT; i++) {
      if (servoCurrentPos[i] != targetAngle) {
        anyMoving = true;
        if (servoCurrentPos[i] < targetAngle) servoCurrentPos[i]++;
        else servoCurrentPos[i]--;
        servos[i].write(servoCurrentPos[i]);
      }
    }
    delay(15);
  }
  printBoth("\nOK: All servos at "); printlnBoth(targetAngle);
}

// Blocking move for single servo
void moveServoBlockingSingle(int pin, int targetAngle) {
  targetAngle = constrain(targetAngle, 0, 180);
  int idx = -1;
  for (int i = 0; i < SERVO_PINS_COUNT; i++) {
    if (SERVO_PINS[i] == pin) { idx = i; break; }
  }
  if (idx == -1) {
    printlnBoth("\nERROR: Invalid servo pin");
    return;
  }
  while (servoCurrentPos[idx] != targetAngle) {
    if (servoCurrentPos[idx] < targetAngle) servoCurrentPos[idx]++;
    else servoCurrentPos[idx]--;
    servos[idx].write(servoCurrentPos[idx]);
    delay(15);
  }
  printBoth("\nOK: Servo pin ");
  printBoth(pin);
  printBoth(" at ");
  printlnBoth(targetAngle);
}

// --- Command Parser ---

void processCommand(String cmd) {
  cmd = sanitizeCommand(cmd);
  cmd.toUpperCase();
  if (cmd.length() == 0) return;

  if (cmd == "STOP") { stopAllMotors(); return; }
  if (cmd == "RESET") { resetAllMotors(); return; }  // New reset command
  if (cmd == "STATUS") { reportStatus(); return; }
  if (cmd == "HELP") { printHelp(); return; }
  if (cmd == "MODE SEQ") { simultaneousMode = false; printlnBoth("\nOK: Mode Sequential"); return; }
  if (cmd == "MODE SIM") { simultaneousMode = true; printlnBoth("\nOK: Mode Simultaneous"); return; }

  // XY <CW/CCW> <degrees> - move X and Y synchronized
  if (cmd.startsWith("XY ")) {
    String args = cmd.substring(3);
    int space = args.indexOf(' ');
    if (space == -1) {
      printlnBoth("\nERROR: Use 'XY CW 90'");
      return;
    }
    String dir = args.substring(0, space);
    String degStr = args.substring(space + 1);
    int deg = degStr.toInt();
    if (deg == 0 && degStr != "0") {
      printlnBoth("\nERROR: Invalid degrees");
      return;
    }
    if (simultaneousMode) startXYMove(dir == "CW", deg);
    else moveXYBlocking(dir == "CW", deg);
    return;
  }

  // ALL <CW/CCW> <degrees> - move all steppers
  if (cmd.startsWith("ALL ")) {
    String args = cmd.substring(4);
    int space = args.indexOf(' ');
    if (space == -1) {
      printlnBoth("\nERROR: Use 'ALL CW 90'");
      return;
    }
    String dir = args.substring(0, space);
    String degStr = args.substring(space + 1);
    int deg = degStr.toInt();
    if (deg == 0 && degStr != "0") {
      printlnBoth("\nERROR: Invalid degrees");
      return;
    }
    if (simultaneousMode) startAllMotorsMove(dir == "CW", deg);
    else moveAllMotorsBlocking(dir == "CW", deg);
    return;
  }

  // SERVO commands - all pins active simultaneously
  if (cmd.startsWith("SERVO ")) {
    String args = cmd.substring(6);
    int space = args.indexOf(' ');

    if (space == -1) {
      // SERVO <angle> - move all servos
      String angleStr = args;
      int angle = angleStr.toInt();
      if (angle == 0 && angleStr != "0") {
        printlnBoth("\nERROR: Invalid angle");
        return;
      }
      if (simultaneousMode) startServoMoveAll(angle);
      else moveServoBlockingAll(angle);
    } else {
      // SERVO <pin> <angle> - move single servo
      String pinStr = args.substring(0, space);
      String angleStr = args.substring(space + 1);
      int pin = pinStr.toInt();
      int angle = angleStr.toInt();
      if (pin == 0 && pinStr != "0") {
        printlnBoth("\nERROR: Invalid pin");
        return;
      }
      if (angle == 0 && angleStr != "0") {
        printlnBoth("\nERROR: Invalid angle");
        return;
      }
      if (simultaneousMode) startServoMoveSingle(pin, angle);
      else moveServoBlockingSingle(pin, angle);
    }
    return;
  }

  // Stepper Parsing
  int firstSpace = cmd.indexOf(' ');
  int secondSpace = cmd.lastIndexOf(' ');
  if (firstSpace == -1 || secondSpace == firstSpace) {
    printlnBoth("\nERROR: Use 'X CW 90'");
    return;
  }

  String motorName = cmd.substring(0, firstSpace);
  String dir = cmd.substring(firstSpace + 1, secondSpace);
  String degStr = cmd.substring(secondSpace + 1);
  int deg = degStr.toInt();
  if (deg == 0 && degStr != "0") {
    printlnBoth("\nERROR: Invalid degrees");
    return;
  }
  int motorIdx = parseMotorName(motorName);
  if (motorIdx != -1) {
    if (simultaneousMode) startMotorMove(motorIdx, dir == "CW", deg);
    else moveMotorBlocking(motorIdx, dir == "CW", deg);
  } else {
    printlnBoth("\nERROR: Unknown motor. Use X, Y, E0, or E1");
  }
}

void setup() {
  Serial.begin(115200);       // USB Serial
  Serial1.begin(115200);      // Bluetooth via CC2650 (pins 18/19)
  pinMode(LED_PIN, OUTPUT);

  for (int i = 0; i < NUM_MOTORS; i++) {
    motors[i]->setMaxSpeed(1000);
    motors[i]->setAcceleration(500);
    motors[i]->setEnablePin(ENABLE_PINS[i]);
    motors[i]->setPinsInverted(false, false, true);
    motors[i]->enableOutputs();
    motorEnabled[i] = true;
  }

  // Attach all servo pins
  for (int i = 0; i < SERVO_PINS_COUNT; i++) {
    servos[i].attach(SERVO_PINS[i]);
    servos[i].write(servoCurrentPos[i]);
  }

  // Blink Ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH); delay(100);
    digitalWrite(LED_PIN, LOW); delay(100);
  }
  resetAllMotors();  // Start with erased/reset state
  printHelp();
  Serial.print("\n> ");
}

void loop() {
  // USB Serial input
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == 127 || c == '\b') {  // Handle backspace
      if (inputBuffer.length() > 0) {
        inputBuffer.remove(inputBuffer.length() - 1);
        Serial.print('\b');
        Serial.print(' ');
        Serial.print('\b');
      }
    } else if (c == '\n' || c == '\r' || c == ';') {
      if (inputBuffer.length() > 0) {
        processCommand(inputBuffer);
        inputBuffer = "";
        printBoth("\n> ");
      }
    } else {
      inputBuffer += c;
      Serial.print(c);
    }
  }

  // Bluetooth Serial1 input
  while (Serial1.available() > 0) {
    char c = Serial1.read();

    if (c == 127 || c == '\b') {  // Handle backspace
      if (btInputBuffer.length() > 0) {
        btInputBuffer.remove(btInputBuffer.length() - 1);
        Serial1.print('\b');
        Serial1.print(' ');
        Serial1.print('\b');
      }
    } else if (c == '\n' || c == '\r' || c == ';') {
      if (btInputBuffer.length() > 0) {
        processCommand(btInputBuffer);
        btInputBuffer = "";
        printBoth("\n> ");
      }
    } else {
      btInputBuffer += c;
      Serial1.print(c);
    }
  }

  if (simultaneousMode) {
    runAllMotors();
  }
  runServo();
}

#endif