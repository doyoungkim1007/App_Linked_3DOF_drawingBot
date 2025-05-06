#include "WizFi360.h"
#include <Servo.h>
#include <math.h>

/* Baudrate */
#define SERIAL_BAUDRATE   115200
#define SERIAL3_BAUDRATE  115200

char ssid[] = "U+Net04FB";       // your network SSID (name)
char pass[] = "DDBB036677";         // your network password
int status = WL_IDLE_STATUS;  // the Wifi radio's status

char server[] = "192.168.219.104";

unsigned long lastConnectionTime = 0;         // last time you connected to the server, in milliseconds
const unsigned long postingInterval = 3000L; // delay between updates, in milliseconds

// Initialize the Ethernet client object
WiFiClient client;

// 서보 모터 객체 선언
Servo servo1;
Servo servo2;
Servo servo3; //z축

const int servo1Pin = 9;
const int servo2Pin = 10;
const int servo3Pin = 11;

const float link1 = 95.0;  // 첫 번째 링크 길이
const float link2 = 125.0; // 두 번째 링크 길이

void setup() {
  // 서보 모터 핀 연결
  servo1.attach(servo1Pin);
  servo2.attach(servo2Pin);
  servo3.attach(servo3Pin); // z축 서보 핀 연결

  // 초기 위치 설정
  int initialAngle1 = 0;
  int initialAngle2 = 0;
  int initialAngle3 = 12;
  servo1.write(initialAngle1);
  servo2.write(initialAngle2);
  servo3.write(initialAngle3);

  // initialize serial for debugging
  Serial.begin(SERIAL_BAUDRATE);
  // initialize serial for WizFi360 module
  Serial3.begin(SERIAL3_BAUDRATE);
  // initialize WizFi360 module
  WiFi.init(&Serial3);

  // check for the presence of the shield
  if (WiFi.status() == WL_NO_SHIELD) {
    Serial.println("WiFi shield not present");
    // don't continue
    while (true);
  }

  // attempt to connect to WiFi network
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to WPA SSID: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network
    status = WiFi.begin(ssid, pass);
    delay(5000);
  }

  // you're connected now, so print out the data
  Serial.println("You're connected to the network");

  printWifiStatus();
}

void loop() {
  if (millis() - lastConnectionTime > postingInterval) {
    String to_draw = check_drawing();

    if (to_draw != "none") {
      int pathSize = 0;
      while (millis() - lastConnectionTime < postingInterval) { }
      int **coordinates = receive_coordinates(to_draw, pathSize);

      if (pathSize != 0) {
        // 경로를 따라 점 이동
        for (int i = 0; i < pathSize; i++) {
          int x = coordinates[i][0];
          int y = coordinates[i][1];
          if (x == 10000 && y == 10000) {
            delay(200);
            move2Z(18); // 펜 올리기
          } else if (x == -10000 && y == -10000) {
            delay(200);
            move2Z(10); // 펜 내리기
          } else {
            moveTo(x, y);
          }
          delay(100);
        }
        remove_data();
      }

      // 동적 메모리 해제
      for (int i = 0; i < pathSize; i++) {
        free(coordinates[i]);
      }
      free(coordinates);
    }
  }
}

float toDegrees(float radians) {
  return radians * 180.0 / PI;
} // 라디안을 각도로 변환하는 함수
float toRadians(float degrees) {
  return degrees * PI / 180.0;
} // 각도를 라디안으로 변환하는 함수

void moveTo(float x, float y) {
  float theta1_A, theta2_A;
  float theta1_B, theta2_B;

  // 역기구학 계산
  if (inverseKinematicsSet1(x, y, theta1_A, theta2_A) && inverseKinematicsSet2(x, y, theta1_B, theta2_B)) {
    // 각도를 서보 모터로 매핑 및 범위 제한
    int servoAngle1_A = constrain((int)theta1_A, 0, 180);
    int servoAngle2_A = constrain((int)theta2_A, 0, 180);
    int servoAngle1_B = constrain((int)theta1_B, 0, 180);
    int servoAngle2_B = constrain((int)theta2_B, 0, 180);

    // 두 세트의 각도 중 첫 번째 세트 각도 사용
    int servoAngle1 = servoAngle1_A;
    int servoAngle2 = 180 - servoAngle1_B;  // 180도에서 반전된 각도 사용
    
    // 서보 모터에 각도 쓰기
    servo1.write(servoAngle1);
    servo2.write(servoAngle2);

    // 현재 각도 출력
    Serial.print("Servo 1 Angle (theta1_A): ");
    Serial.print(servoAngle1);
    Serial.print("\tServo 2 Angle (theta1_A inverted): ");
    Serial.println(servoAngle2);

    // 정기구학으로 현재 펜 위치 계산 및 출력
    float currentX1, currentY1;
    forwardKinematics(theta1_A, theta2_A, currentX1, currentY1);
    
    Serial.print("Current Position (Set 1): (");
    Serial.print(currentX1);
    Serial.print(", ");
    Serial.print(currentY1);
    Serial.println(")");
  }
}// 좌표로 이동하는 함수

bool inverseKinematicsSet1(float x, float y, float &theta1, float &theta2) {
  float distance = sqrt(x * x + y * y);
  if (distance > (link1 + link2) || distance < abs(link1 - link2)) {
    return false; // 목표 위치에 도달할 수 없음
  }

  float cosTheta2 = (x * x + y * y - link1 * link1 - link2 * link2) / (2 * link1 * link2);
  float sinTheta2 = sqrt(1 - cosTheta2 * cosTheta2);
  theta2 = toDegrees(acos(cosTheta2));

  float k1 = link1 + link2 * cosTheta2;
  float k2 = link2 * sinTheta2;
  theta1 = toDegrees(atan2(y, x) - atan2(k2, k1));

  return true;
}// 역기구학 계산 함수 (세트 1)

bool inverseKinematicsSet2(float x, float y, float &theta1, float &theta2) {
  float distance = sqrt(x * x + y * y);
  if (distance > (link1 + link2) || distance < abs(link1 - link2)) {
    return false; // 목표 위치에 도달할 수 없음
  }

  float cosTheta2 = (x * x + y * y - link1 * link1 - link2 * link2) / (2 * link1 * link2);
  float sinTheta2 = sqrt(1 - cosTheta2 * cosTheta2);
  theta2 = toDegrees(-acos(cosTheta2));

  float k1 = link1 + link2 * cosTheta2;
  float k2 = link2 * sinTheta2;
  theta1 = toDegrees(atan2(y, x) + atan2(k2, k1));

  return true;
}// 역기구학 계산 함수 (세트 2)

void forwardKinematics(float theta1, float theta2, float &x, float &y) {
  theta1 = toRadians(theta1);
  theta2 = toRadians(theta2);
  float joint1X = link1 * cos(theta1);
  float joint1Y = link1 * sin(theta1);
  x = joint1X + link2 * cos(theta1 + theta2);
  y = joint1Y + link2 * sin(theta1 + theta2);
}// 정기구학 계산 함수

void move2Z(int angle) {
  servo3.write(angle);
}// z축 이동 함수

void printWifiStatus() {
  // print the SSID of the network you're attached to
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your WiFi shield's IP address
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength
  long rssi = WiFi.RSSI();
  Serial.print("Signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}

String check_drawing() {
  client.stop();
  String httpResponse = "";  // 웹서버에서 받은 값을 저장할 변수

  if (client.connect(server, 80)) {
    Serial.println("[WizFi360] Connecting to server...");
    client.println(F("GET /drawing_bot/check_drawing.php HTTP/1.1"));
    client.print("Host: ");
    client.println(server);
    client.println("Connection: close");
    client.println();

    unsigned long timeout = millis();
    while (client.connected() && millis() - timeout < 5000) {
      while (client.available()) {
        char c = client.read();
        Serial.write(c);
        httpResponse += c;
        timeout = millis(); // reset the timeout if data is available
      }
    }

    Serial.println("HTTP Response:");
    Serial.println(httpResponse);

    // Parse the response to find "draw=" and extract the value
    int startIndex = httpResponse.indexOf("draw=");
    if (startIndex != -1) {
      startIndex += 5; // move index past "draw="
      int endIndex = httpResponse.indexOf('&', startIndex);
      if (endIndex == -1) {
        endIndex = httpResponse.length();
      }
      httpResponse = httpResponse.substring(startIndex, endIndex);
    } else {
      httpResponse = "none";
    }

    Serial.println(httpResponse);
    if (httpResponse != "none" && httpResponse != "") {
      Serial.println("drawing");
    } else {
      Serial.println("none");
    }

    lastConnectionTime = millis();
  } else {
    // if you couldn't make a connection
    Serial.println("Connection failed");
  }

  if (httpResponse == "") {
    httpResponse = "none";
  }
  return httpResponse;
}

int** receive_coordinates(String name, int &pathSize) {
  Serial.println();
  client.stop();
  int** coordinates = nullptr;
  if (client.connect(server, 80)) {
    client.println("GET /drawing_bot/receive_coordinates.php?name=" + name + " HTTP/1.1");
    client.print("Host: ");
    client.println(server);
    client.println("Connection: close");
    client.println();

    unsigned long timeout = millis();
    String httpResponse = "";  // 웹서버에서 받은 값을 저장할 변수
    while (client.connected() && millis() - timeout < 5000) {
      while (client.available()) {
        char c = client.read();
        httpResponse += c;
        timeout = millis(); // reset the timeout if data is available
      }
    }

    Serial.println("HTTP Response:");
    Serial.println(httpResponse);

    pathSize = 0;
    if (httpResponse != "") {
      String str = httpResponse.substring(httpResponse.indexOf("coordinates=") + 12);
      str.replace("(", "");
      str.replace(")", "");
      str.replace(" ", ""); // 공백 제거
      
      // 콤마(,)를 기준으로 나누기
      int commaCount = 0;
      for (int i = 0; i < str.length(); i++) {
        if (str.charAt(i) == ',') {
          commaCount++;
        }
      }

      pathSize = (commaCount + 1) / 2;
      coordinates = (int**)malloc(pathSize * sizeof(int*));
      for (int i = 0; i < pathSize; i++) {
        coordinates[i] = (int*)malloc(2 * sizeof(int));
      }

      int row = 0;
      int col = 0;
      String temp = "";

      for (int i = 0; i < str.length(); i++) {
        char c = str.charAt(i);
        if (c != ',') {
          temp += c;
        }
        else {
          coordinates[row][col] = temp.toInt();
          temp = "";
          col++;
          if (col == 2) {
            col = 0;
            row++;
          }
        }
      }
      // 마지막 좌표 저장
      if (temp != "") {
        coordinates[row][col] = temp.toInt();
      }

      // 변환된 배열 출력
      for (int i = 0; i < pathSize; i++) {
        for (int j = 0; j < 2; j++) {
          Serial.print(coordinates[i][j]);
          Serial.print(" ");
        }
        Serial.println();
      }
    }
    lastConnectionTime = millis();
  }
  else {
    // if you couldn't make a connection
    Serial.println("Connection failed");
  }

  if (coordinates == nullptr) {
    coordinates = (0, 120);
  }
  return coordinates;
}

void remove_data() {
  if (client.connect(server, 80)) {
    client.println("GET /drawing_bot/remove_data.php? HTTP/1.1");
    client.print("Host: ");
    client.println(server);
    client.println("Connection: close");
    client.println();
  }
}
