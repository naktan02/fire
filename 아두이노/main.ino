#include <ESP8266WiFi.h> // ESP32인 경우 <WiFi.h> 사용
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// 와이파이 설정
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// 파이썬 서버 주소 (PC IP 주소 확인 필수, ipconfig/ifconfig)
// 예: http://192.168.0.10:5000/direction/0  <- 끝에 숫자는 도트 ID
String serverUrl = "http://192.168.0.5:5000/direction/0"; 

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;

    http.begin(client, serverUrl);
    int httpCode = http.GET();

    if (httpCode > 0) {
      String payload = http.getString();
      // Serial.println(payload); // 디버깅용

      // JSON 파싱
      StaticJsonDocument<200> doc;
      deserializeJson(doc, payload);
      
      const char* dir = doc["direction"]; // "UP", "DOWN", "LEFT", "RIGHT", "STOP"
      
      Serial.print("Direction: ");
      Serial.println(dir);

      // 여기에 도트 매트릭스 제어 코드 추가
      updateDotMatrix(dir);
    }
    http.end();
  }
  delay(500); // 0.5초마다 갱신
}

void updateDotMatrix(const char* dir) {
  // 매트릭스에 화살표 그리는 로직 구현
  if (strcmp(dir, "UP") == 0) {
    // 위쪽 화살표 표시
  } else if (strcmp(dir, "RIGHT") == 0) {
    // 오른쪽 화살표 표시
  }
  // ...
}