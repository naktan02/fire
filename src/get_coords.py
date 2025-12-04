import cv2
import numpy as np
from camera import Camera
from detector import Detector

# 맵 크기 (main.py와 동일)
MAP_W, MAP_H = 860, 520


def mouse_callback(event, x, y, flags, param):
    img = param['img']

    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"DOT: ({x}, {y}),")
        cv2.circle(img, (x, y), 5, (0, 255, 255), -1)
        cv2.putText(img, "DOT", (x+5, y-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,255), 1)

    elif event == cv2.EVENT_RBUTTONDOWN:
        print(f"EXIT: ({x}, {y}),")
        cv2.circle(img, (x, y), 7, (0, 0, 0), -1)
        cv2.putText(img, "EXIT", (x+5, y-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1)

    param['img'] = img


def main():
    # [수정됨] 라즈베리파이 스트림 주소
    STREAM_URL = "http://10.8.0.2:8080/?action=stream"
    
    cam = None
    try:
        print(f"Connecting to {STREAM_URL}...")
        cam = Camera(STREAM_URL)
    except Exception as e:
        print(f"Error connecting to camera: {e}")
        return

    detector = Detector()
    last_valid_corners = None
    
    print("=== 좌표 추출 도구 ===")
    print("1. 'Click Coordinates' 창에서 도트/목적지 위치를 클릭")
    print("2. 콘솔에 출력된 DOT/EXIT 좌표를 main.py에 복사")
    print("3. 's' = 화면 일시정지 / 해제")
    print("4. 'q' = 종료")

    is_paused = False

    blank = np.zeros((MAP_W, MAP_H, 3), dtype=np.uint8)
    param = {'img': blank}

    cv2.namedWindow('Click Coordinates')
    cv2.setMouseCallback('Click Coordinates', mouse_callback, param)

    while True:
        if not is_paused:
            ret, frame = cam.get_frame()
            if not ret:
                print("[ERROR] 카메라 프레임 읽기 실패")
                break
            
            # 원본 카메라 화면 축소
            frame = cv2.resize(frame, (640, 480))

            # 코너 검출
            corners, _ = detector.detect_corners(frame)
            if corners is not None:
                area = cv2.contourArea(corners)
                if area > (frame.shape[0] * frame.shape[1] * 0.05):
                    last_valid_corners = corners

            # Warp
            warped = None
            if last_valid_corners is not None:
                warped = detector.warp_perspective(
                    frame, last_valid_corners, MAP_W, MAP_H
                )

            if warped is None:
                display_img = np.zeros((MAP_W, MAP_H, 3), dtype=np.uint8)
                cv2.putText(display_img, "No Map Detected",
                            (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (255, 255, 255), 2)
            else:
                display_img = warped.copy()

            param['img'] = display_img

            # 원본 카메라 + 코너 표시용
            display_frame = frame.copy()
            if last_valid_corners is not None:
                cv2.polylines(display_frame,
                              [last_valid_corners.astype(int)],
                              True, (0, 255, 255), 2)
            cv2.imshow("Original Camera (coords mode)", display_frame)

        # 좌표 찍는 창
        cv2.imshow('Click Coordinates', param['img'])

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('s'):
            is_paused = not is_paused
            print(f"화면 일시정지: {'ON' if is_paused else 'OFF'}")

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
