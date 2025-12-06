#include "LedControl.h"
#include <WiFiEsp.h>
#include <SoftwareSerial.h>

// ==========================================
// 1. 와이파이 및 서버 설정
// ==========================================
char ssid[] = "마음다리 상담센터_2.4G";
char pass[] = "mind1004!!";
char server[] = "192.168.219.44";
int port = 5000;

// 각 매트릭스 모듈이 담당할 서버의 도트 ID 매핑
// 모듈 0번 -> 서버 ID 0, 모듈 1번 -> 서버 ID 1 ...
int MODULE_TO_DOT_ID[4] = {0, 1, 2, 3};
int MODULE_ROTATION[4] = {1, 1, 0, 0};
SoftwareSerial SerialESP(2, 3); // RX=2, TX=3
WiFiEspClient client;

// ==========================================
// 2. 하드웨어 핀 설정 (환풍기 8번, 부저 9번)
// ==========================================
// 도트 매트릭스: DIN=12, CLK=11, CS=10
LedControl lc = LedControl(12, 11, 10, 4);

const int PIN_FAN = 8;     // 환풍기 
const int PIN_BUZZER = 9;  // 부저 (+)

unsigned long lastCheckTime = 0;
const long checkInterval = 1000; // 1초 간격 확인

// ==========================================
// 3. 화살표 패턴 데이터
// ==========================================
const byte arrows[5][8] = {
  { B10000001, B01000010, B00100100, B00011000, B00011000, B00100100, B01000010, B10000001 }, // X
  { B00011000, B00001100, B00000110, B11111111, B11111111, B00000110, B00001100, B00011000 }, // Right
  { B00011000, B00111100, B01111110, B11111111, B00011000, B00011000, B00011000, B00011000 }, // Up
  { B00011000, B00110000, B01100000, B11111111, B11111111, B01100000, B00110000, B00011000 }, // Left
  { B00011000, B00011000, B00011000, B00011000, B11111111, B01111110, B00111100, B00011000 }  // Down
};

void setup() {
  Serial.begin(9600);
  SerialESP.begin(9600);

  // [핀 모드 설정]
  pinMode(PIN_FAN, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  
  // 초기 상태: 끔
  digitalWrite(PIN_FAN, LOW);
  noTone(PIN_BUZZER);

  // --------------------------------------------------------
  // [전력 안전 시동] 와이파이 먼저 연결 -> 매트릭스 나중에 켬
  // --------------------------------------------------------
  
  // 1. 와이파이 연결
  WiFi.init(&SerialESP);
  if (WiFi.status() == WL_NO_SHIELD) {
    Serial.println("WiFi shield not present");
    while (true);
  }

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    WiFi.begin(ssid, pass);
    delay(1000);
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("IP: "); Serial.println(WiFi.localIP());

  // 2. 도트 매트릭스 켜기
  Serial.println("Initializing Dot Matrix...");
  for (int i = 0; i < lc.getDeviceCount(); i++) {
    lc.shutdown(i, false); 
    lc.setIntensity(i, 1); // 전력 절약을 위해 밝기 1
    lc.clearDisplay(i);
  }
  
  // 초기화면: X 표시
  for(int i=0; i<4; i++) displayPattern(i, 0);
}

void loop() {
  // 주기적으로 서버 데이터 확인
  if (millis() - lastCheckTime > checkInterval) {
    lastCheckTime = millis();
    getAllDataFromServer();
  }
}

void getAllDataFromServer() {
  if (!client.connect(server, port)) {
    Serial.println("Connection failed");
    return;
  }

  // 서버에 상태 요청
  client.println("GET /status HTTP/1.1");
  client.print("Host: "); client.println(server);
  client.println("Connection: close");
  client.println();

  // 응답 받기
  String response = "";
  bool headerEnded = false;
  unsigned long timeout = millis();
  
  while (client.connected() || client.available()) {
    if (millis() - timeout > 3000) break;
    if (client.available()) {
      char c = client.read();
      if (c == '{') headerEnded = true; 
      if (headerEnded) response += c;
    }
  }
  client.stop();

  // 데이터가 있으면 처리
  if (response.length() > 0) {
    
    // -----------------------------------------------------
    // [기능 1] 화재 감지 시 -> 환풍기(8번) & 부저(9번) 작동
    // -----------------------------------------------------
    bool isFire = false;
    // JSON에서 "fire_detected":true 찾기
    if (response.indexOf("\"fire_detected\":true") != -1 || 
        response.indexOf("\"fire_detected\": true") != -1 ) {
      isFire = true;
    }

    if (isFire) {
      Serial.println("!!! FIRE DETECTED !!!");
      
      // 환풍기 켜기
      digitalWrite(PIN_FAN, HIGH); 
      
      // 복잡한 멜로디는 와이파이 통신을 방해하므로 단순음 권장
      for(int k=0; k<5; k++) {
        tone(PIN_BUZZER, 2000); // 소리 켬
        delay(100);             // 0.1초만 유지 
        noTone(PIN_BUZZER);     // 소리 끔
        delay(100);             // 0.1초 대기
        }
        
        // 3. 패턴 사이 쉬는 시간 (0.5초)
        delay(500);

    } else {
      // 화재 아님 -> 끄기
      digitalWrite(PIN_FAN, LOW);
      noTone(PIN_BUZZER);
    }

    // -----------------------------------------------------
    // [기능 2] 도트 매트릭스 개별 방향 표시
    // -----------------------------------------------------
    for (int i = 0; i < 4; i++) {
      int targetDotID = MODULE_TO_DOT_ID[i];
      int dir = parseDirectionForID(response, targetDotID);
      
      // 여기서 방향을 그리기만 하면 됨 (회전 로직은 displayPattern 안에 있음)
      displayPattern(i, dir);
    }
  }
}

// JSON 파싱 함수 (ID별 방향 추출)
int parseDirectionForID(String json, int id) {
  String key = "\"" + String(id) + "\":\"";
  int keyIndex = json.indexOf(key);
  if (keyIndex == -1) return 0;

  int valStart = keyIndex + key.length();
  int valEnd = json.indexOf("\"", valStart);
  if (valEnd == -1) return 0;

  String dirStr = json.substring(valStart, valEnd);
  
  if (dirStr == "RIGHT") return 1;
  if (dirStr == "UP") return 2;
  if (dirStr == "UP-RIGHT") return 2; 
  if (dirStr == "LEFT") return 3;
  if (dirStr == "DOWN") return 4;
  
  return 0; // STOP
}

void displayPattern(int deviceIndex, int arrowIdx) {
  // STOP(0)이거나 범위를 벗어나면 그냥 원본 출력 (회전 필요 없음)
  if (arrowIdx <= 0 || arrowIdx > 4) {
    for (int row = 0; row < 8; row++) {
      lc.setRow(deviceIndex, row, arrows[0][row]);
    }
    return;
  }

  // 회전 계산 로직
  // arrowIdx는 1~4 (Right, Up, Left, Down)
  // 1을 빼서 0~3으로 만들고, 회전값(0~3)을 더한 뒤, 다시 4로 나눈 나머지를 구함
  int rotation = MODULE_ROTATION[deviceIndex];
  
  // (현재방향 - 1 + 회전각) % 4 + 1
  int newIdx = ((arrowIdx - 1 + rotation) % 4) + 1;

  for (int row = 0; row < 8; row++) {
    lc.setRow(deviceIndex, row, arrows[newIdx][row]);
  }
}