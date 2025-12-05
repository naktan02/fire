import cv2

class Camera:
    def __init__(self, source=1):
        """
        카메라를 초기화합니다.
        :param source: 카메라 인덱스(0) 또는 스트림 URL(문자열).
        """
        # source가 문자열(URL)인 경우: 웹 스트리밍 주소로 간주
        if isinstance(source, str):
            print(f"[INFO] 네트워크 스트림 접속 시도: {source}")
            self.cap = cv2.VideoCapture(source)
        
        # source가 숫자(Int)인 경우: 로컬 USB 카메라로 간주
        else:
            # 1) Windows에서 MSMF 대신 DSHOW 백엔드 먼저 시도 (로컬 카메라용)
            self.cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)

            # 2) 만약 이게 안 되면 기본 백엔드로 한 번 더 시도
            if not self.cap.isOpened():
                print("[WARN] CAP_DSHOW로 열기 실패, 기본 백엔드로 재시도합니다.")
                self.cap = cv2.VideoCapture(source)

        # 공통: 카메라/스트림 열기 실패 확인
        if not self.cap.isOpened():
            raise ValueError("Could not open video source ({})".format(source))

    def get_frame(self):
        ret, frame = self.cap.read()
        return ret, frame

    def release(self):
        if self.cap is not None:
            self.cap.release()