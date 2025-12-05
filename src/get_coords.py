import cv2
import numpy as np
from camera import Camera

# main.py와 동일한 크기 사용
MAP_W, MAP_H = 640, 480

def mouse_callback(event, x, y, flags, param):
    img = param['img']

    if event == cv2.EVENT_LBUTTONDOWN:
        # 왼쪽 클릭: 도트(출발점) 좌표
        print(f"({x}, {y}),") # 복사하기 편하게 포맷 맞춤
        cv2.circle(img, (x, y), 5, (0, 255, 255), -1)
        cv2.putText(img, "DOT", (x+5, y-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,255), 1)

    elif event == cv2.EVENT_RBUTTONDOWN:
        # 오른쪽 클릭: 탈출구(목적지) 좌표
        print(f"EXIT: ({x}, {y})")
        cv2.circle(img, (x, y), 7, (0, 255, 0), -1)
        cv2.putText(img, "EXIT", (x+5, y-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,0), 1)

    param['img'] = img

def main():
    STREAM_URL = "http://10.8.0.3:8080/?action=stream"
    # STREAM_URL = 1
    
    try:
        print(f"Connecting to {STREAM_URL}...")
        cam = Camera(STREAM_URL)
    except Exception as e:
        print(f"Error connecting to camera: {e}")
        return

    print("=== 좌표 추출 도구 (Fixed Camera) ===")
    print("1. 화면에서 도트(왼클릭) / 탈출구(우클릭) 위치를 찍으세요.")
    print("2. 콘솔에 출력된 좌표 괄호 덩어리 `(x, y),` 를 복사하세요.")
    print("3. main.py의 FIXED_DOT_POSITIONS 리스트에 붙여넣으세요.")
    print("4. 's' 키: 화면 멈춤 (정확히 찍기 위해 사용)")
    print("5. 'r' 키: 화면 리셋 (잘못 찍었을 때)")
    print("6. 'q' 키: 종료")

    is_paused = False
    
    # 클릭한 흔적을 그릴 투명 레이어
    overlay = np.zeros((MAP_H, MAP_W, 3), dtype=np.uint8)
    param = {'img': overlay} # 마우스 콜백이 여기에 그림

    cv2.namedWindow('Get Coordinates')
    cv2.setMouseCallback('Get Coordinates', mouse_callback, param)

    while True:
        if not is_paused:
            ret, frame = cam.get_frame()
            if not ret:
                print("[ERROR] 프레임 읽기 실패")
                break
            
            # 메인 코드와 동일한 크기로 리사이즈
            frame = cv2.resize(frame, (MAP_W, MAP_H))
            
            # 현재 프레임 + 오버레이(점 찍은 것) 합치기
            # 오버레이가 검은색(0)이 아닌 부분만 프레임에 덮어씀
            display_img = frame.copy()
            mask = np.any(overlay > 0, axis=2)
            display_img[mask] = overlay[mask]
            
            cv2.imshow('Get Coordinates', display_img)

        # 화면이 멈춰있을 때도 창은 업데이트
        else:
            cv2.imshow('Get Coordinates', display_img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            is_paused = not is_paused
            print(f"화면 일시정지: {'ON' if is_paused else 'OFF'}")
        elif key == ord('r'):
            # 리셋 기능
            overlay.fill(0)
            param['img'] = overlay
            print("화면 초기화됨")

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()