import cv2
import numpy as np
from camera import Camera
from detector import Detector
from map import GridMap

# === 설정 영역 (CONFIGURATION) ===
MAP_WIDTH = 860
MAP_HEIGHT = 520
GRID_SIZE = 20

# 2단계에서 얻은 좌표를 여기에 붙여넣으세요
# 예: FIXED_DOT_POSITIONS = [(123, 456), (50, 50)]
FIXED_DOT_POSITIONS = [
]
FIXED_EXIT_POSITIONS = [
]
def main():
    # [수정됨] 라즈베리파이 MJPG-Streamer 주소 입력
    # 주의: 뒤에 /?action=stream 까지 정확히 적어야 함
    STREAM_URL = "http://10.8.0.2:8080/?action=stream"

    try:
        print(f"Connecting to {STREAM_URL}...")
        cam = Camera(STREAM_URL) 
    except Exception as e:
        print(f"Error: {e}")
        return

    detector = Detector()
    # 맵 객체는 Warp가 성공했을 때 초기화됩니다.
    grid_map = GridMap(MAP_WIDTH, MAP_HEIGHT, GRID_SIZE)
    last_valid_corners = None
    
    print("=== Fire Evacuation System Started ===")
    print(f"Target Nodes: {len(FIXED_DOT_POSITIONS)}")

    while True:
        ret, frame = cam.get_frame()
        if not ret: break
        
        # 원활한 처리를 위해 해상도 고정
        frame = cv2.resize(frame, (640, 480))
        display_frame = frame.copy()

        # 1. 맵 외곽선(종이 테두리) 인식
        corners, _ = detector.detect_corners(frame)
        if corners is not None:
            area = cv2.contourArea(corners)
            if area > (frame.shape[0]*frame.shape[1] * 0.1): # 화면의 10% 이상일 때만
                last_valid_corners = corners

        # 2. 맵 투시 변환 (Top-down View)
        warped_map = None
        if last_valid_corners is not None:
            warped_map = detector.warp_perspective(frame, last_valid_corners, MAP_WIDTH, MAP_HEIGHT)
        
        if warped_map is not None:
            # === [핵심 로직] 맵 분석 및 경로 계산 ===
            
            # (A) 맵 초기화
            grid_map.reset()
            
            # (B) 내부 흰색 벽 인식 -> 장애물 등록
            wall_mask = detector.detect_walls_in_map(warped_map)
            grid_map.update_obstacles_from_mask(wall_mask)
            
            # (C) 불(양초) 인식 -> 장애물 등록
            fire_boxes, fire_mask = detector.detect_fire(warped_map)
            for (fx, fy, fw, fh) in fire_boxes:
                # 불 주변을 넉넉하게 위험지역으로 설정 (안전 마진)
                grid_map.set_obstacle_rect(fx-10, fy-10, fw+20, fh+20)
                # 시각화
                cv2.rectangle(warped_map, (fx, fy), (fx+fw, fy+fh), (0, 0, 255), 2)
                cv2.putText(warped_map, "FIRE", (fx, fy-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

            # (D) 탈출구 처리
            # grid_map.reset()에서 이미 self.exits는 비워진 상태라고 가정
            for (ex, ey) in FIXED_EXIT_POSITIONS:
                w, h = 40, 40
                grid_map.add_exit(ex - w/2, ey - h/2, w, h)

                cv2.circle(warped_map, (ex, ey), 10, (0, 0, 0), -1)
                cv2.putText(
                    warped_map, "EXIT",
                    (ex - 20, ey - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 1
                )

            # (E) 각 도트 매트릭스 위치별 최단 경로 계산
            # 디버깅용 그리드 그리기 (장애물 확인)
            # grid_map.draw_grid(warped_map) 

            for i, (dm_x, dm_y) in enumerate(FIXED_DOT_POSITIONS):
                # 위치 표시
                cv2.circle(warped_map, (dm_x, dm_y), 5, (255, 255, 0), -1)
                
                # 경로 계산
                path = grid_map.get_shortest_path(dm_x, dm_y)
                
                if len(path) > 1:
                    # 경로 그리기 (파란색)
                    cv2.polylines(warped_map, [np.array(path)], False, (255, 0, 0), 2)
                    
                    # 방향 화살표 (현재 위치에서 경로의 10% 지점 혹은 3번째 점을 향하도록)
                    lookahead_idx = min(3, len(path)-1)
                    target_pt = path[lookahead_idx]
                    
                    cv2.arrowedLine(warped_map, (dm_x, dm_y), target_pt, (0, 255, 255), 3, tipLength=0.3)
                else:
                    # 갈 수 없음 (고립됨)
                    cv2.putText(warped_map, "X", (dm_x, dm_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

            # 결과 화면 출력
            cv2.imshow("Smart Evacuation Map", warped_map)

        # 원본 화면도 같이 표시 (카메라 조정용)
        if last_valid_corners is not None:
            cv2.polylines(display_frame, [last_valid_corners.astype(int)], True, (0, 255, 255), 2)
        cv2.imshow("Original Camera", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()