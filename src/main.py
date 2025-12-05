import cv2
import numpy as np

# 분리된 모듈들 import
from camera import Camera
from detector import Detector
from map import GridMap
from navigator import Navigator   # [New] 방향 계산
from server import EvacuationServer # [New] 웹 서버

# === 설정 ===
MAP_WIDTH = 640
MAP_HEIGHT = 480
GRID_SIZE = 20

# 1개의 도트만 테스트한다고 가정 (혹은 여러 개)
FIXED_DOT_POSITIONS = [
    (100, 200) # ID 0
]
FIXED_EXIT_POSITIONS = [
    (600, 50)
]

def main():
    # 1. 모듈 초기화
    try:
        cam = Camera(1) # 혹은 스트림 URL
    except Exception as e:
        print(f"Camera Error: {e}")
        return

    detector = Detector()
    grid_map = GridMap(MAP_WIDTH, MAP_HEIGHT, GRID_SIZE)
    navigator = Navigator()      # 방향 계산기 생성
    server = EvacuationServer()  # 서버 생성
    
    # 2. 서버 시작 (백그라운드)
    server.start()

    wall_locked = False
    locked_wall_mask = None

    print("=== System Started ===")
    
    while True:
        ret, frame = cam.get_frame()
        if not ret: break
        
        # 화면 준비
        frame = cv2.resize(frame, (MAP_WIDTH, MAP_HEIGHT))
        analysis_map = frame.copy()

        # [A] 맵 & 벽 업데이트
        grid_map.reset()
        current_wall_mask = None
        
        if wall_locked and locked_wall_mask is not None:
            current_wall_mask = locked_wall_mask
            cv2.putText(analysis_map, "LOCKED", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        else:
            current_wall_mask = detector.detect_walls_in_map(analysis_map)
            cv2.putText(analysis_map, "Scanning...", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            
        if current_wall_mask is not None:
            grid_map.update_obstacles_from_mask(current_wall_mask)

        # [B] 불 감지
        fire_boxes, _ = detector.detect_fire(analysis_map)
        is_fire = (len(fire_boxes) > 0)
        
        for (fx, fy, fw, fh) in fire_boxes:
            grid_map.set_obstacle_rect(fx-20, fy-20, fw+40, fh+40)
            cv2.rectangle(analysis_map, (fx, fy), (fx+fw, fy+fh), (0,0,255), 2)

        # [C] 탈출구 등록
        for ex, ey in FIXED_EXIT_POSITIONS:
            grid_map.add_exit(ex, ey, 20, 20)
            cv2.circle(analysis_map, (ex, ey), 8, (255,255,255), -1)

        # [D] 도트 경로 및 방향 계산 (Navigator 위임)
        current_directions = {}
        
        for i, (dx, dy) in enumerate(FIXED_DOT_POSITIONS):
            path = grid_map.get_shortest_path(dx, dy)
            direction = "STOP"

            if len(path) > 1:
                # [핵심] Navigator가 대각선 포함해서 방향 알려줌
                direction = navigator.get_direction((dx, dy), path[1])
                
                # 시각화
                cv2.polylines(analysis_map, [np.array(path)], False, (255,0,0), 2)
                cv2.putText(analysis_map, direction, (dx, dy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
            
            current_directions[i] = direction
            cv2.circle(analysis_map, (dx, dy), 5, (0,255,255), -1)

        # [E] 서버에 데이터 업데이트
        server.update_data(is_fire, current_directions)

        # 화면 출력
        cv2.imshow("System", analysis_map)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == ord('c'):
            wall_locked = not wall_locked
            locked_wall_mask = current_wall_mask.copy() if wall_locked and current_wall_mask is not None else None

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()