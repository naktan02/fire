#include "LedControl.h"

// ==========================================
// 1. 하드웨어 설정 및 상수 정의
// ==========================================
const int DIN_PIN = 12;      // 데이터 핀
const int CLK_PIN = 11;      // 클럭 핀
const int CS_PIN  = 10;      // CS 핀
const int NUM_DEVICES = 4;   // 모듈 개수

// 타이밍 설정
const int ANIMATION_SPEED = 100;       // 화살표가 움직이는 속도 (ms)
const long PATTERN_CHANGE_TIME = 5000; // 화살표 방향 변경 주기 (5초)

LedControl lc = LedControl(DIN_PIN, CLK_PIN, CS_PIN, NUM_DEVICES);

// ==========================================
// 2. 전역 변수
// ==========================================
unsigned long lastAnimTime = 0;   // 애니메이션 프레임 타이머
unsigned long lastChangeTime = 0; // 패턴 변경 타이머

int currentDirection = 0; // 현재 화살표 방향 (0~7)
int scrollStep = 0;       // 현재 움직임 단계 (0~7)

// ==========================================
// 3. 패턴 데이터 (정지 상태의 화살표 원본)
// ==========================================
const byte arrows[8][8] = {
  // 0: ➡️ 오른쪽
  { B00011000, B00001100, B00000110, B11111111, B11111111, B00000110, B00001100, B00011000 },
  // 1: ↘️ 오른쪽 아래
  { B00011000, B00001100, B00000110, B00000011, B00000011, B00000110, B00001100, B00011000 },
  // 2: ⬇️ 아래쪽
  { B00011000, B00111100, B01111110, B11111111, B00011000, B00011000, B00011000, B00011000 },
  // 3: ↙️ 왼쪽 아래
  { B00011000, B00110000, B01100000, B11000000, B11000000, B01100000, B00110000, B00011000 },
  // 4: ⬅️ 왼쪽
  { B00011000, B00110000, B01100000, B11111111, B11111111, B01100000, B00110000, B00011000 },
  // 5: ↖️ 왼쪽 위
  { B00011000, B00110000, B01100000, B11000000, B11000000, B01100000, B00110000, B00011000 },
  // 6: ⬆️ 위쪽
  { B00011000, B00111100, B01111110, B11111111, B00011000, B00011000, B00011000, B00011000 },
  // 7: ↗️ 오른쪽 위
  { B00011000, B00001100, B00000110, B00000011, B00000011, B00000110, B00001100, B00011000 }
};

// ==========================================
// 4. 초기화
// ==========================================
void setup() {
  for (int index = 0; index < lc.getDeviceCount(); index++) {
    lc.shutdown(index, false);
    lc.setIntensity(index, 8);
    lc.clearDisplay(index);
  }
  lastAnimTime = millis();
  lastChangeTime = millis();
}

// ==========================================
// 5. 메인 루프
// ==========================================
void loop() {
  unsigned long currentTime = millis();

  // [기능 1] 5초마다 화살표 방향 변경
  if (currentTime - lastChangeTime >= PATTERN_CHANGE_TIME) {
    lastChangeTime = currentTime;
    currentDirection++;
    if (currentDirection >= 8) currentDirection = 0;
    
    scrollStep = 0; // 방향 바뀌면 스크롤 위치 초기화
    lc.clearDisplay(0); // 잔상 방지 (선택 사항)
  }

  // [기능 2] 매 프레임마다 화살표 이동 (애니메이션)
  if (currentTime - lastAnimTime >= ANIMATION_SPEED) {
    lastAnimTime = currentTime;
    
    // 계산된 프레임을 모든 모듈에 송출
    updateAnimatedArrow();
    
    // 다음 프레임을 위해 스텝 증가 (0~7 반복)
    scrollStep = (scrollStep + 1) % 8;
  }
}

// ==========================================
// 6. 헬퍼 함수 (핵심 로직)
// ==========================================

void updateAnimatedArrow() {
  byte frame[8]; // 이번 프레임에 출력할 완성된 이미지 버퍼

  // 현재 방향(currentDirection)과 스텝(scrollStep)에 맞춰 이미지를 시프트(Shift)
  generateShiftedFrame(currentDirection, scrollStep, frame);

  // 모든 모듈에 동일한 프레임 전송
  for (int i = 0; i < NUM_DEVICES; i++) {
    for (int row = 0; row < 8; row++) {
      lc.setRow(i, row, frame[row]);
    }
  }
}

// [알고리즘] 원본 화살표를 방향에 따라 X, Y축으로 Circular Shift(순환 이동) 시키는 함수
void generateShiftedFrame(int dir, int step, byte* outputFrame) {
  // 방향별 X, Y 이동 계수 정의
  // dir: 0(우), 1(우하), 2(하), 3(좌하), 4(좌), 5(좌상), 6(상), 7(우상)
  int dx = 0; 
  int dy = 0;

  switch(dir) {
    case 0: dx = 1;  dy = 0;  break; // 우
    case 1: dx = 1;  dy = 1;  break; // 우하
    case 2: dx = 0;  dy = 1;  break; // 하
    case 3: dx = -1; dy = 1;  break; // 좌하
    case 4: dx = -1; dy = 0;  break; // 좌
    case 5: dx = -1; dy = -1; break; // 좌상
    case 6: dx = 0;  dy = -1; break; // 상
    case 7: dx = 1;  dy = -1; break; // 우상
  }

  // 실제 이동량 계산 (스텝 * 방향)
  // 모듈러 연산(%)을 위해 양수로 변환하는 로직 포함
  int shiftX = (dx * step) % 8;
  int shiftY = (dy * step) % 8;

  // 원본 패턴을 가져와서 변형
  for (int row = 0; row < 8; row++) {
    // 1. Y축 시프트 (Row 인덱스 이동)
    // (row - shiftY)를 하는데 음수가 나올 수 있으니 +8을 하고 %8을 함 (Circular Buffer 개념)
    int srcRow = (row - shiftY + 8) % 8;
    byte pixelData = arrows[dir][srcRow];

    // 2. X축 시프트 (Bitwise Shift)
    // 원형 큐처럼 비트가 밀리면 반대쪽에서 나오도록 처리 (Circular Bit Shift)
    if (shiftX > 0) {
      // 오른쪽으로 이동 (>> shiftX) | (왼쪽으로 넘어간 비트를 가져옴)
      pixelData = (pixelData >> shiftX) | (pixelData << (8 - shiftX));
    } else if (shiftX < 0) {
      // 왼쪽으로 이동 (<< -shiftX) | (오른쪽으로 넘어간 비트를 가져옴)
      int s = -shiftX; // 양수로 변환
      pixelData = (pixelData << s) | (pixelData >> (8 - s));
    }

    outputFrame[row] = pixelData;
  }
}
