/**
 * Robocar Motor Driver for Arduino.
 *
 * Compile:
 *  platformio run
 *
 * Install:
 *  platformio run --target upload
 */

#include "Arduino.h"

#define ENABLE_SERIAL_RESPONSE 0

// reference: www.arduino.cc/en/Main/ArduinoMotorShieldR3
#define LEFT_WHEEL_DIRECTION 12
#define RIGHT_WHEEL_DIRECTION 13
#define LEFT_WHEEL_PWM 3
#define RIGHT_WHEEL_PWM 11
#define LEFT_WHEEL_BRAKE 9
#define RIGHT_WHEEL_BRAKE 8
#define LEFT_WHEEL_SENSE A0
#define RIGHT_WHEEL_SENSE A1

char input[6];
int  index = 0;
unsigned long lastCommand;

int charToDirection(char c);
int hexCharsToInt(char* c, int n);
void stop();
void execute();

void setup() {
  delay(1000);  // recovery!

  pinMode(LEFT_WHEEL_DIRECTION, OUTPUT);
  pinMode(RIGHT_WHEEL_DIRECTION, OUTPUT);
  pinMode(LEFT_WHEEL_PWM, OUTPUT);
  pinMode(RIGHT_WHEEL_PWM, OUTPUT);

  Serial.begin(9600);

  lastCommand = millis();
}

void loop() {
  while (Serial.available()) {
    char c = (char) Serial.read();
    if (c != '\n' && index < 6) {
      input[index++] = c;
    } else if (c == '\n') {
      if (index == 6) {
        execute();
      } else {
        if (ENABLE_SERIAL_RESPONSE) Serial.println("ERROR");
      }
      index = 0;
    }
  }

  unsigned long timeNow = millis();
  if (timeNow - lastCommand > 5000UL) {
    if (ENABLE_SERIAL_RESPONSE) Serial.println("TIMEOUT");
    lastCommand = timeNow;
    stop();
  }
}

void execute() {
  int leftDirection = charToDirection(input[0]);
  int rightDirection = charToDirection(input[3]);
  int leftSpeed = hexCharsToInt(&input[1], 2);
  int rightSpeed = hexCharsToInt(&input[4], 2);

  if (leftDirection == -2 || rightDirection == -2 || leftSpeed == -1 || rightSpeed == -1) {
    if (ENABLE_SERIAL_RESPONSE) Serial.println("ERROR");
    return;
  }

  analogWrite(LEFT_WHEEL_PWM, leftSpeed);
  digitalWrite(LEFT_WHEEL_DIRECTION, leftDirection == -1 ? LOW : HIGH);
  digitalWrite(LEFT_WHEEL_BRAKE, leftDirection == 0 ? HIGH : LOW);
  analogWrite(RIGHT_WHEEL_PWM, rightSpeed);
  digitalWrite(RIGHT_WHEEL_DIRECTION, rightDirection == -1 ? HIGH : LOW);  // right wheel reversed
  digitalWrite(RIGHT_WHEEL_BRAKE, rightDirection == 0 ? HIGH : LOW);

  if (ENABLE_SERIAL_RESPONSE) Serial.println("OK");

  lastCommand = millis();
}

/**
 *  +1 forward
 *   0 brake
 *  -1 reverse
 *  -2 error
 */
int charToDirection(char c) {
  switch (c) {
    case 'F': case 'f': return 1;
    case 'B': case 'b': return 0;
    case 'R': case 'r': return -1;
    default:  return -2;
  }
}

/**
 *   [0, 255] speed
 *   -1       error
 */
int hexCharsToInt(char* c, int n) {
  int result = 0;
  for (; n > 0; n--) {
    result *= 16;
    if (*c >= '0' && *c <= '9') {
      result += *c - '0';
    } else if (*c >= 'A' && *c <= 'F') {
      result += *c - 'A' + 0xA;
    } else if (*c >= 'a' && *c <= 'f') {
      result += *c - 'a' + 0xA;
    } else {
      return -1;
    }
    c++;
  }
  return result;
}

void stop() {
  analogWrite(LEFT_WHEEL_PWM, 0);
  analogWrite(RIGHT_WHEEL_PWM, 0);
}
