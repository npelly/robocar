// www.arduino.cc/en/Main/ArduinoMotorShieldR3

#define LEFT_WHEEL_DIRECTION 12
#define RIGHT_WHEEL_DIRECTION 13
#define LEFT_WHEEL_PWM 3
#define RIGHT_WHEEL_PWM 11
#define LEFT_WHEEL_BRAKE 9
#define RIGHT_WHEEL_BRAKE 8

char input[6];
int  index = 0;
unsigned long lastCommand;

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
        Serial.println("ERROR");
      }
      index = 0;
    }
  }
  
  if (millis() - lastCommand > 5000UL) {
    Serial.println("TIMEOUT");
    lastCommand = millis();
    stop();
  }
}

void execute() {  
  int leftDirection = charToDirection(input[0]);
  int rightDirection = charToDirection(input[3]);
  int leftSpeed = hexCharsToInt(&input[1], 2);
  int rightSpeed = hexCharsToInt(&input[4], 2);
  Serial.println(leftDirection);
  Serial.println(leftSpeed);
  Serial.println(rightDirection);
  Serial.println(rightSpeed);

  if (leftDirection == -1 || rightDirection == -1 || leftSpeed == -1 || rightSpeed == -1) {
    Serial.println("ERROR");
    return;
  }
  
  analogWrite(LEFT_WHEEL_PWM, leftSpeed);
  digitalWrite(LEFT_WHEEL_DIRECTION, leftDirection ? HIGH : LOW);
  analogWrite(RIGHT_WHEEL_PWM, rightSpeed);
  digitalWrite(RIGHT_WHEEL_DIRECTION, rightDirection ? LOW : HIGH);  // right wheel reversed
  
  Serial.println("OK");
  
  lastCommand = millis();
}

/**
 *  +1 forward
 *   0 reverse
 *  -1 error
 */
int charToDirection(char c) {
  switch (c) {
    case 'F': case 'f': return 1;
    case 'R': case 'r': return 0;
    default:  return -1;
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

