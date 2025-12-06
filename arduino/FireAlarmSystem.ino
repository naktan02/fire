/*
 * 프로젝트명: 화재 감지 자동 대응 시스템
 * 작성일: 2025. 12. 05
 * * [시스템 개요]
 * 1. 화재 감지 시 환기 팬 가동 (즉시 작동)
 * 2. 부저는 최초 감지 시 10회 경보 울림 후 정지 (팬은 계속 돔)
 * 3. 화재 상황 종료 시 시스템 리셋
 * * [하드웨어 연결]
 * - 환기 팬 (릴레이): 디지털 8번 핀
 * - 부저: 디지털 9번 핀
 * - 화재 센서: (추후 연결 예정, 현재는 시뮬레이션 코드 작동)
 */

// ==========================================
// [1] 환경 설정 (Configuration)
// ==========================================
// 핀 번호 설정
#define PIN_FAN     8   // 환기 팬(릴레이) 연결 핀
#define PIN_BUZZER  9   // 부저 연결 핀

// 작동 파라미터 설정
#define BUZZER_FREQ 2000    // 부저 주파수 (2000Hz = 삐-)
#define BUZZER_REPEAT 10    // 경보음 반복 횟수
#define FAN_ON_LEVEL HIGH   // 릴레이 켜짐 신호 (모듈에 따라 LOW일 수 있음)
#define FAN_OFF_LEVEL LOW   // 릴레이 꺼짐 신호

// 시스템 상태 변수 (수정 불필요)
bool isAlarmPlayed = false; // 경보음이 울렸는지 확인하는 플래그

// ==========================================
// [2] 초기화 (Setup)
// ==========================================
void setup() {
  // 디버깅을 위한 시리얼 통신 시작
  Serial.begin(9600);
  Serial.println(">>> 시스템 부팅 완료: 감시 모드 진입 <<<");

  // 핀 모드 설정
  pinMode(PIN_FAN, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  // 초기 상태: 모두 끔
  digitalWrite(PIN_FAN, FAN_OFF_LEVEL);
  noTone(PIN_BUZZER);
}

// ==========================================
// [3] 메인 루프 (Loop)
// ==========================================
void loop() {
  // 1. 화재 감지 여부 확인 (모듈 함수 호출)
  bool isFire = getFireTriggerStatus();

  // 2. 상황별 대응 로직
  if (isFire) {
    // 화재 발생 시 대응
    activateEmergencyProtocol();
  } else {
    // 평상시 상태 복구
    resetSystem();
  }

  // 시스템 안정성 대기
  delay(100);
}

// ==========================================
// [4] 기능 모듈 (Functions)
// ==========================================

/*
 * [입력 모듈] 화재 감지 트리거 확인
 * 설명: 센서 값을 읽어 화재 여부(true/false)를 반환합니다.
 * 참고: 현재는 테스트를 위해 5초마다 상태가 바뀌는 시뮬레이션 코드가 들어있습니다.
 */
bool getFireTriggerStatus() {
  // --- [TODO: 추후 실제 센서 코드로 교체할 영역] ---
  static bool simulatedState = false;
  static unsigned long lastCheckTime = 0;
  
  // 5초마다 테스트 상태 변경
  if (millis() - lastCheckTime > 5000) {
    lastCheckTime = millis();
    simulatedState = !simulatedState; // 상태 반전
    
    // 상태 모니터링 출력
    Serial.print("[센서 상태] ");
    Serial.println(simulatedState ? "🔥 화재 감지됨 (TRUE)" : "🟢 정상 (FALSE)");
  }
  
  return simulatedState;
  // --- [교체 영역 끝] ---
}

/*
 * [출력 모듈 1] 비상 대응 가동
 * 설명: 팬을 켜고, 부저를 조건부(10회)로 울립니다.
 */
void activateEmergencyProtocol() {
  // 1. 환기 팬 즉시 가동 (지속)
  digitalWrite(PIN_FAN, FAN_ON_LEVEL);

  // 2. 부저 경보 (아직 안 울렸을 경우에만 10회 재생)
  if (isAlarmPlayed == false) {
    Serial.println(">> 경보 발령! 부저 10회 재생 시작");
    
    for (int i = 0; i < BUZZER_REPEAT; i++) {
      tone(PIN_BUZZER, BUZZER_FREQ); // 소리 켬
      delay(200);                    // 0.2초 유지
      noTone(PIN_BUZZER);            // 소리 끔
      delay(200);                    // 0.2초 대기
    }
    
    Serial.println(">> 부저 정지. 환기 팬은 계속 가동됩니다.");
    isAlarmPlayed = true; // '울림 완료' 처리
  }
}

/*
 * [출력 모듈 2] 시스템 리셋
 * 설명: 모든 장치를 끄고, 다음 경보를 위해 상태를 초기화합니다.
 */
void resetSystem() {
  // 경보가 울린 적이 있다면(즉, 방금까지 화재상황이었다면) 초기화 수행
  if (isAlarmPlayed == true) {
    Serial.println(">> 상황 해제. 시스템을 초기화합니다.");
    
    // 장치 정지
    digitalWrite(PIN_FAN, FAN_OFF_LEVEL);
    noTone(PIN_BUZZER);
    
    // 상태 변수 리셋 (다음 화재 시 다시 울리기 위함)
    isAlarmPlayed = false;
  }
}
