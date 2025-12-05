#include "LedControl.h"

/*
 핀 연결 설정:
 DIN(DataIn)  : 12번 핀
 CLK(Clock)   : 11번 핀
 CS(Load)     : 10번 핀
 1            : 연결된 MAX7219 모듈의 개수 (1개라고 가정)
*/
LedControl lc = LedControl(12, 11, 10, 1);

// 화살표 모양 비트맵 (0은 꺼짐, 1은 켜짐)
// 오른쪽을 가리키는 화살표 모양입니다.
byte arrow[8] = {
  B00011000,
  B00001100,
  B00000110,
  B11111111,
  B11111111,
  B00000110,
  B00001100,
  B00011000
};

void setup() {
  // 전원 절약 모드 해제 (초기화 시 필수)
  lc.shutdown(0, false);
  
  // 밝기 설정 (0~15 사이의 값, 8은 중간 밝기)
  lc.setIntensity(0, 8);
  
  // 화면 초기화 (모든 LED 끄기)
  lc.clearDisplay(0);
}

void loop() {
  // 1. 화살표 표시
  drawArrow();
  delay(1000); // 1초 대기

  // 2. 화면 지우기 (점멸 효과 확인용)
  lc.clearDisplay(0);
  delay(500);  // 0.5초 대기
}

// 화살표를 그리는 함수
void drawArrow() {
  for (int i = 0; i < 8; i++) {
    // setRow(디바이스주소, 행번호, 데이터)
    lc.setRow(0, i, arrow[i]);
  }
}
