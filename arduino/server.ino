#include "WiFiEsp.h"

// ESP-01 모듈과 통신할 시리얼 설정 (RX: 2, TX: 3)
#ifndef HAVE_HWSERIAL1
#include "SoftwareSerial.h"
SoftwareSerial Serial1(2, 3); // RX, TX
#endif

// [수정 필요] 본인의 와이파이 정보로 변경하세요
char ssid[] = "Net";   
char pass[] = "ddingdding";       

int status = WL_IDLE_STATUS;
int reqCount = 0; // 요청 횟수 카운트

WiFiEspServer server(80);

void setup() {
  Serial.begin(9600);   // 시리얼 모니터용
  Serial1.begin(9600);  // ESP-01 모듈용 (통신 속도 주의: 9600 추천)
  
  WiFi.init(&Serial1);

  // 와이파이 연결 시도
  if (WiFi.status() == WL_NO_SHIELD) {
    Serial.println("WiFi shield not present");
    while (true);
  }

  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to WPA SSID: ");
    Serial.println(ssid);
    status = WiFi.begin(ssid, pass);
  }

  Serial.println("You're connected to the network");
  printWifiStatus(); // 연결된 정보 출력 (여기서 IP 확인!)
  
  server.begin();
}

void loop() {
  WiFiEspClient client = server.available(); // 클라이언트 접속 확인

  if (client) {
    Serial.println("New client connected");
    boolean currentLineIsBlank = true;
    
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        // HTTP 요청의 끝을 확인 (빈 줄이 나오면 헤더 끝)
        if (c == '\n' && currentLineIsBlank) {
          
          // --- 노트북으로 보낼 HTML 응답 시작 ---
          client.print(
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n"
            "Refresh: 20\r\n"  // 20초마다 자동 새로고침
            "\r\n");

          client.print("<!DOCTYPE HTML>\r\n");
          client.print("<html>\r\n");
          client.print("<h1>Hello World!</h1>\r\n");

          client.print("Requests received: ");
          client.print(++reqCount);
          client.print("<br>\r\n");

          client.print("Analog input A0: ");
          client.print(analogRead(0));
          client.print("<br>\r\n");

          client.print("</html>\r\n");
          // --- 응답 끝 ---
          break;
        }
        
        if (c == '\n') {
          currentLineIsBlank = true;
        } else if (c != '\r') {
          currentLineIsBlank = false;
        }
      }
    }
    
    delay(10);
    client.stop();
    Serial.println("Client disconnected");
  }
}

// IP 주소 등을 출력하는 함수
void printWifiStatus() {
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip); // ★ 이 IP 주소가 중요합니다!

  Serial.println();
  Serial.println("To see this page in action, open a browser to http://");
  Serial.println(ip);
}