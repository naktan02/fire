#include "PeopleCounter.h"
#include <WiFiEsp.h>
#include <SoftwareSerial.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

char ssid[] = "마음다리 상담센터_2.4G";
char pass[] = "mind1004!!";
char server[] = "192.168.219.44";
int port = 5000;
int DOT_ID = 0; // 이 아두이노 위치 ID (지금은 안 써도 됨)

// === [핀 설정] ===
PeopleCounter counter(4, 5, 6, 7, 70); // (TrigA, EchoA, TrigB, EchoB, 거리)

const int LED_UP = 8;
const int LED_DOWN = 9;
const int LED_LEFT = 10;
const int LED_RIGHT = 11;

// I2C LCD (주소: 0x27 또는 0x3F)
LiquidCrystal_I2C lcd(0x27, 16, 2);

SoftwareSerial SerialESP(2, 3); // RX, TX (ESP8266과 연결된 핀)
WiFiEspClient client;

// 서버에서 받은 최종 인원 수
int serverPeopleCount = 0;
unsigned long lastDirectionCheckTime = 0;
const long checkInterval = 1000; // 1초마다 방향 확인 (지금은 생략 가능)

// ---- 함수 선언 ----
void updateLCD();
int sendPeopleData(const char *type);
void resetLEDs();
void getDirectionData(); // 지금은 안 써도 되지만 유지

void setup()
{
  Serial.begin(9600);
  SerialESP.begin(9600);

  // LED 초기화
  pinMode(LED_UP, OUTPUT);
  pinMode(LED_DOWN, OUTPUT);
  pinMode(LED_LEFT, OUTPUT);
  pinMode(LED_RIGHT, OUTPUT);

  // LCD 초기화
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("WiFi Conn...");

  // 와이파이 연결
  WiFi.init(&SerialESP);
  if (WiFi.status() == WL_NO_SHIELD)
  {
    Serial.println("WiFi shield not present");
    lcd.setCursor(0, 1);
    lcd.print("No WiFi Shield");
    while (true)
      ;
  }
  while (WiFi.status() != WL_CONNECTED)
  {
    WiFi.begin(ssid, pass);
    Serial.print(".");
    delay(1000);
  }

  Serial.println();
  Serial.print("Arduino IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("Server IP : ");
  Serial.println(server);
  Serial.println("\nConnected!");

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Smart Evac Sys");
  lcd.setCursor(0, 1);
  lcd.print("People: 0");

  counter.begin();
}

void loop()
{
  int event = counter.update();

  if (event == 1)
  {
    Serial.println("[EVENT] IN detected (sensor)");
    int newCount = sendPeopleData("IN");
    if (newCount >= 0)
    {
      serverPeopleCount = newCount; // ✅ 여기서 전역에 넣어주고
      updateLCD();                  // ✅ 그걸 LCD에 반영
    }
  }
  else if (event == 2)
  {
    Serial.println("[EVENT] OUT detected (sensor)");
    int newCount = sendPeopleData("OUT");
    if (newCount >= 0)
    {
      serverPeopleCount = newCount;
      updateLCD();
    }
  }
}

// 2. (선택) 주기적으로 방향 정보 가져오기
// 나중에 방향 LED까지 붙일 때 다시 활성화하면 됨
/*
if (millis() - lastDirectionCheckTime > checkInterval) {
  getDirectionData();
  lastDirectionCheckTime = millis();
}
*/
// }

// ---- LCD에 서버 인원 수 표시 ----
void updateLCD()
{
  lcd.setCursor(0, 0);
  lcd.print("Smart Evac Sys  "); // 뒤에 공백으로 예전 글자 지우기

  lcd.setCursor(0, 1);
  lcd.print("People: ");
  lcd.print("    "); // 숫자 자리 지우기
  lcd.setCursor(8, 1);
  lcd.print(serverPeopleCount); // ✅ 반드시 이 변수!

  Serial.print("[LCD] People: ");
  Serial.println(serverPeopleCount); // 시리얼에도 같은 값 찍기
}

// ---- 서버로 IN/OUT 보내고 current_count 받기 ----
// 성공하면 current_count 반환, 실패하면 -1
// ---- 서버로 IN/OUT 보내고 current_count 받기 ----
int sendPeopleData(const char *type)
{
  Serial.print("[sendPeopleData] connect to ");
  Serial.print(server);
  Serial.print(":");
  Serial.println(port);

  if (!client.connect(server, port))
  {
    Serial.println("[sendPeopleData] Connect Failed");
    return -1;
  }

  Serial.println("[sendPeopleData] CONNECT OK");

  // JSON payload 전송
  String payload = String("{\"type\":\"") + type + "\"}";
  client.println("POST /api/people_count HTTP/1.1");
  client.print("Host: ");
  client.println(server);
  client.println("Content-Type: application/json");
  client.print("Content-Length: ");
  client.println(payload.length());
  client.println();
  client.print(payload);

  // 응답 읽기
  String line;
  String jsonBody = "";
  bool headerDone = false;
  unsigned long start = millis();

  while ((millis() - start) < 3000)
  {
    while (client.available())
    {
      line = client.readStringUntil('\n');
      line.trim();

      if (line.length() == 0)
      {
        if (!headerDone)
        {
          headerDone = true;
          Serial.println("[sendPeopleData] ---- HEADER END ----");
        }
        continue;
      }

      if (!headerDone)
      {
        Serial.print("[HDR] ");
        Serial.println(line);
      }
      else
      {
        Serial.print("[BODY] ");
        Serial.println(line);
        jsonBody = line;
        break;
      }
    }
    if (jsonBody.length() > 0 || !client.connected())
      break;
  }
  client.stop();

  if (jsonBody.length() == 0)
  {
    Serial.println("[sendPeopleData] No JSON body");
    return -1;
  }

  // --- [수정된 파싱 로직] ---
  int idx = jsonBody.indexOf("current_count");
  if (idx < 0)
  {
    Serial.println("[sendPeopleData] 'current_count' not found");
    return -1;
  }

  idx = jsonBody.indexOf(":", idx);
  if (idx < 0)
  {
    Serial.println("[sendPeopleData] ':' not found");
    return -1;
  }
  idx++;

  while (idx < jsonBody.length() && !isDigit(jsonBody[idx]))
    idx++;

  String numStr = "";
  while (idx < jsonBody.length() && isDigit(jsonBody[idx]))
  {
    numStr += jsonBody[idx];
    idx++;
  }

  Serial.print("[Debug] Extracted Number: '");
  Serial.print(numStr);
  Serial.println("'");

  if (numStr.length() == 0)
    return 0;

  return numStr.toInt();
} // <--- 이 닫는 괄호가 꼭 있어야 합니다!

// ---- (필요하면 나중에 다시 쓸 방향 GET) ----
void getDirectionData()
{
  // 지금은 생략 가능. 나중에 도트 방향/LED 연동할 때 사용.
}

void resetLEDs()
{
  digitalWrite(LED_UP, LOW);
  digitalWrite(LED_DOWN, LOW);
  digitalWrite(LED_LEFT, LOW);
  digitalWrite(LED_RIGHT, LOW);
}
