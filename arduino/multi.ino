#include "LedControl.h"

// DIN=12, CLK=11, CS=10, 모듈 2개
LedControl lc = LedControl(12, 11, 10, 3);

// 오른쪽 화살표
byte arrow_right[8] = {
  B00011000,
  B00001100,
  B00000110,
  B11111111,
  B11111111,
  B00000110,
  B00001100,
  B00011000
};

// 위쪽 화살표
byte arrow_up[8] = {
  B00011000,
  B00111100,
  B01111110,
  B11111111,
  B00011000,
  B00011000,
  B00011000,
  B00011000
};

void setup() {
  for (int index = 0; index < lc.getDeviceCount(); index++) {
    lc.shutdown(index, false);  // 절전 모드 해제
    lc.setIntensity(index, 8);  // 밝기 (0~15)
    lc.clearDisplay(index);     // 초기 화면 지우기
  }
}

void loop() {
  drawBothArrows();
  // 계속 보여주기만 할 거면 delay만 주고 끝
}

// 두 모듈에 서로 다른 화살표를 동시에 그림
void drawBothArrows() {
  for (int row = 0; row < 8; row++) {
    // 인덱스 0번 모듈
    lc.setRow(0, row, arrow_right[row]);
    // 인덱스 1번 모듈
    lc.setRow(1, row, arrow_up[row]);
    lc.setRow(2, row, arrow_up[row]);
    lc.setRow(3, row, arrow_up[row]);
  }
}
