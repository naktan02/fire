import numpy as np
import heapq
import cv2

class GridMap:
    def __init__(self, width, height, grid_size=20):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.cols = width // grid_size
        self.rows = height // grid_size
        
        # 0: 이동 가능, 1: 장애물(벽/불)
        self.grid = np.zeros((self.rows, self.cols), dtype=np.uint8)
        self.exits = []

    def reset(self):
        """매 프레임 맵 상태 초기화"""
        self.grid.fill(0)
        self.exits.clear()

    def _to_grid(self, x, y):
        gx = int(x // self.grid_size)
        gy = int(y // self.grid_size)
        gx = max(0, min(self.cols - 1, gx))
        gy = max(0, min(self.rows - 1, gy))
        return gx, gy

    def _to_pixel(self, gx, gy):
        cx = gx * self.grid_size + self.grid_size // 2
        cy = gy * self.grid_size + self.grid_size // 2
        return cx, cy

    def update_obstacles_from_mask(self, mask):
        """
        Detector에서 만든 벽/불 마스크(0 or 255)를 받아 그리드에 장애물로 등록
        미래지향적: 픽셀 단위 마스크를 그리드 단위로 효율적으로 변환
        """
        # 마스크를 그리드 크기로 축소 (Nearest Neighbor or Max Pooling 개념)
        # 단순히 resize하면 중간에 있는 얇은 벽이 사라질 수 있으므로 주의.
        # 여기서는 안전하게 픽셀 체크 방식으로 구현 (성능 최적화 가능)
        
        # 리사이즈로 대략적인 그리드 맵 생성 (cv2.INTER_AREA or MAX)
        small_mask = cv2.resize(mask, (self.cols, self.rows), interpolation=cv2.INTER_NEAREST)
        
        # 마스크가 있는 곳(>0)은 장애물(1)로 설정
        self.grid[small_mask > 0] = 1

    def set_obstacle_rect(self, x, y, w, h):
        """사각형 영역 장애물 설정 (불 등)"""
        gx1, gy1 = self._to_grid(x, y)
        gx2, gy2 = self._to_grid(x + w, y + h)
        self.grid[gy1:gy2+1, gx1:gx2+1] = 1

    def add_exit(self, x, y, w, h):
        cx, cy = x + w/2, y + h/2
        self.exits.append(self._to_grid(cx, cy))

    def get_shortest_path(self, start_x, start_y):
        if not self.exits: return []
        
        start_node = self._to_grid(start_x, start_y)
        # 시작점이 벽/불 속이면 탈출 불가
        if self.grid[start_node[1], start_node[0]] == 1:
            return []

        shortest_path = []
        min_len = float('inf')

        for exit_pos in self.exits:
            path = self._astar(start_node, exit_pos)
            if path and len(path) < min_len:
                min_len = len(path)
                shortest_path = path
        
        return shortest_path

    def _astar(self, start, end):
        # (기존 A* 로직 유지)
        # 만약 끝점이 장애물이면 근처 가능한 곳으로 타협하는 로직 추가 가능
        if self.grid[end[1], end[0]] == 1: return [] 

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: abs(start[0]-end[0]) + abs(start[1]-end[1])}

        while open_set:
            current = heapq.heappop(open_set)[1]
            if current == end:
                return self._reconstruct(came_from, current)

            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]: # 4방향
                nx, ny = current[0]+dx, current[1]+dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if self.grid[ny, nx] == 0: # 장애물 아님
                        tentative_g = g_score[current] + 1
                        if nx == end[0] and ny == end[1]: pass # 도착지
                        
                        if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                            came_from[(nx, ny)] = current
                            g_score[(nx, ny)] = tentative_g
                            f_score[(nx, ny)] = tentative_g + abs(nx-end[0]) + abs(ny-end[1])
                            heapq.heappush(open_set, (f_score[(nx, ny)], (nx, ny)))
        return []

    def _reconstruct(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return [self._to_pixel(gx, gy) for gx, gy in path]
        
    def draw_grid(self, img):
        # 디버깅: 그리드 그리기 (장애물은 빨간색 채우기)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r, c] == 1:
                    cx, cy = self._to_pixel(c, r)
                    # 장애물(벽) 표시
                    cv2.rectangle(img, 
                                  (c*self.grid_size, r*self.grid_size), 
                                  ((c+1)*self.grid_size, (r+1)*self.grid_size), 
                                  (0, 0, 100), -1)